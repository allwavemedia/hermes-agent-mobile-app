# Reconnection and Queueing

## State machines

Connection:

```text
locked → disconnected → connecting → authenticating → synchronizing → live
                                ↘ backoff ↗             ↘ reset/snapshot ↗
live → suspended (background) → disconnected
revoked/unsupported → terminal until user action/update
```

Subscription:

```text
none → requesting → snapshot → replaying → current
current → gap → replaying
replaying → reset-required → snapshot
any → remote-disabled/revoked → closed
```

The app disables state-changing controls until `current`. Read-only stale content is visibly marked.

## Cursors, acks, and replay

Host assigns `epoch` and `seq`; relay does not rewrite them. Android sends cumulative `session.ack(epoch, seq)` after reducer application. Relay/host may discard earlier replay entries only after every relevant condition and retention policy permit; slow devices do not extend the hard 15-minute/10-MiB bound.

Reconnect request includes last epoch/seq and pending command idempotency keys. Outcomes:

- exact replay available: events `seq+1…head`, then current;
- epoch changed or entry expired: signed `session.reset`, fresh snapshot;
- session disabled/deleted: terminal state;
- host offline: no guessed local state.

Duplicate events are ignored by event ID/sequence; conflicting same sequence is a protocol security error and forces disconnect.

## Backoff

Full-jitter exponential delay: base 500 ms, cap 30 s, reset after 60 s stable connection. Server `retryAfter` may increase but not reduce rate-limit delay. Android network change triggers one immediate attempt. Authentication/revocation/schema errors do not loop.

Host relay connection uses equivalent jitter with a 60 s cap and sends presence only after authentication. Shutdown is distinguishable from unexpected disconnect.

## Command recovery

App shows a command as:

- `unsent` — local only;
- `queued` — relay durably accepted under policy;
- `accepted` — host verified and forwarded;
- `completed`/`rejected` — terminal;
- `unknown` — connection lost before durable receipt.

For `unknown`, app queries the idempotency receipt before retrying. It never changes the idempotency key. Host receipts are retained for 24 hours for executed state-changing commands or longer than maximum client retry window; sensitive payload is not retained, only digest/result.

## Offline matrix

| Command | Host offline | TTL | Additional binding |
|---|---|---:|---|
| `prompt.submit` | Only explicit opt-in and `offlinePrompt.v1` | 5 min | session revision, capability/policy hash, user confirmation |
| Read subscription | Wait | n/a | Fresh snapshot before current |
| Approval/deny | Reject | 0 | Never queue |
| Clarification | Reject | 0 | Never queue |
| Interrupt/steer | Reject | 0 | Never queue |
| Terminal read/write | Reject | 0 | Never queue |
| Attachment | Reject | 0 | Never queue |
| New session | Reject | 0 | Online host required |
| Model/tool/MCP/config/project change | Reject | 0 | Never queue |
| Device revocation | Relay records immediately; host applies on reconnect | durable security state | trust epoch |

Queued prompt executes only if, at delivery, the session still exists/is enabled, active state permits a prompt, revision/capability/policy hashes match, device remains paired, and expiry has not passed. Otherwise it is rejected and content deleted.

## Zero retention

Relay cannot replay or queue. Reconnect always requests host replay/snapshot. Host local journal can still provide 15-minute continuity because content remains on the paired computer; zero retention describes relay content retention, not deletion of Hermes’s canonical local session history.

## Concurrent surfaces

Commands from Desktop/TUI and Android serialize through existing Hermes session semantics. A state-changing remote command includes expected revision/run. When another surface wins, remote receives a conflict/stale result and refreshes. Transcript events identify source surface where safe, but neither surface receives greater authority.
