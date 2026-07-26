# Versioned Remote-Control Protocol

Normative version: `hermes.remote-control/1.0`. Canonical schemas are under [`schemas/v1/`](schemas/v1/). JSON uses UTF-8, no duplicate object keys, RFC 3339 UTC timestamps, UUIDv7 identifiers where ordering helps, and base64url without padding for binary values. Signatures use RFC 7515 JWS compact serialization with ES256. Signed JSON is serialized with RFC 8785 JSON Canonicalization Scheme before hashing/signing.

## Compatibility

Peers advertise `protocol: {major, minMinor, maxMinor}`. Major mismatch fails closed with `protocol.unsupported`. Minor negotiation chooses the highest common minor. Unknown event types are retained as opaque telemetry only when their envelope declares `critical: false`; unknown commands, security fields, or `critical: true` events are rejected. Schema IDs are immutable. Breaking semantics require v2.

## Envelope

Every routed message has:

```json
{
  "protocol": "hermes.remote-control/1.0",
  "envelopeId": "019c…",
  "kind": "command",
  "type": "approval.respond",
  "computerId": "cmp_…",
  "deviceId": "dev_…",
  "sessionId": "session_…",
  "epoch": "019c…",
  "issuedAt": "2026-07-26T18:00:00Z",
  "expiresAt": "2026-07-26T18:01:00Z",
  "jti": "019c…",
  "idempotencyKey": "019c…",
  "expectedSessionRevision": 42,
  "capabilityHash": "sha256-…",
  "payload": {},
  "signature": "eyJ…"
}
```

`signature` covers every field except itself. `computerId`, `deviceId`, and `sessionId` are identifiers, never credentials. Relay-assigned connection context must match signed identifiers. Host keeps a replay cache through `expiresAt + 60 seconds` and persists terminal command receipts long enough to make retries deterministic.

## Message families

| Kind | Types | Direction | Durable by default |
|---|---|---|---|
| Control | `hello`, `challenge`, `authenticate`, `credential`, `ping`, `pong`, `error` | peer/relay | No |
| Pairing | `pair.offer`, `pair.claim`, `pair.confirm`, `pair.accept`, `pair.reject` | phone↔host via relay/direct | Offer until 2-minute expiry |
| Presence | `computer.presence`, `session.catalog`, `session.capabilities` | host→phone | Metadata only |
| Subscription | `session.subscribe`, `session.unsubscribe`, `session.ack`, `session.replay` | bidirectional | Cursor metadata |
| State | `session.snapshot`, `session.event`, `session.reset` | host→phone | Bounded journal |
| Command | `session.enable`, `session.disable`, `session.create`, `prompt.submit`, `session.steer`, `session.interrupt`, `clarify.respond`, `approval.respond`, `attachment.*`, `terminal.*`, supported selection commands | phone→host | Policy-specific |
| Receipt | `command.accepted`, `command.completed`, `command.rejected` | host→phone | Idempotency window |
| Device | `device.list`, `device.rename`, `device.revoke`, `computer.revokeAll` | bidirectional | Security metadata |

## Snapshot

`session.snapshot` contains:

- `epoch`, `snapshotSeq`, `sessionRevision`, `generatedAt`;
- session metadata: ID, title, project display name, safe cwd label, model display ID, status, active run ID;
- bounded transcript entries using normalized roles/parts;
- active tool activities and pending requests;
- terminal descriptors for Hermes-owned terminals only;
- attachment manifests without local absolute paths;
- signed capability snapshot and its hash.

Sensitive provider details, environment, secrets, sudo values, unrelated processes, and filesystem paths outside a host-approved display policy are absent.

## Ordered events

`session.event` contains `seq`, `prevSeq`, `eventId`, `occurredAt`, `eventType`, `causedByCommandId`, and normalized payload. Event types:

- `message.started|delta|interim|completed`;
- `reasoning.started|delta|completed` when host policy allows display;
- `tool.started|progress|completed|failed|risk`;
- `request.approval|clarification|terminalRead`;
- `request.resolved|expired`;
- `session.status|title|usage|context`;
- `terminal.opened|output|closed`;
- `attachment.accepted|progress|available|failed|expired`;
- `subagent.started|updated|completed`;
- `capabilities.changed`;
- `session.remoteDisabled`.

`seq` orders the remote projection, not the underlying model token timestamps. A normalized event may correspond to several internal gateway events.

## Capability snapshot

The host signs:

```json
{
  "capabilityVersion": 1,
  "computerId": "cmp_…",
  "sessionId": "session_…",
  "sessionRevision": 42,
  "issuedAt": "…",
  "expiresAt": "…",
  "methods": {
    "prompt.submit": {"risk": "low", "offline": true, "maxBytes": 65536},
    "approval.respond": {"risk": "high", "offline": false, "biometric": true}
  },
  "constraints": {
    "attachmentMaxBytes": 52428800,
    "terminalWrite": false
  }
}
```

Capability TTL is five minutes or the session’s remaining remote-enable lifetime, whichever is shorter. Any policy/approval/tool/model/project change increments `sessionRevision` and emits `capabilities.changed`. Host authorizes against current state, never merely the presented snapshot.

## Approval and clarification binding

An `approval.respond` payload MUST include:

- `requestId`, `approvalId`, `toolCallId`, `activeRunId`;
- `decision` (`approve_once`, `deny`);
- `actionDigest` (SHA-256 of normalized tool/action preview);
- `requestEventSeq`, `expectedSessionRevision`, `capabilityHash`;
- `displayDigest` (hash of the exact risk text shown on Android);
- biometric-backed device signature for high risk;
- expiry no later than the request deadline or 60 seconds.

Permanent allow or policy mutation is not exposed in MVP. Clarification response binds `requestId`, `activeRunId`, `requestEventSeq`, and expires no later than five minutes or host deadline. A stale, replaced, mismatched, or already resolved request returns `command.rejected` with a stable reason.

## Idempotency and errors

State-changing commands require `idempotencyKey`. The host stores `(deviceId, idempotencyKey, payloadDigest, result)`; an identical retry returns the original result, while the same key with another digest is `idempotency.conflict`.

Stable error codes include:

- `auth.invalid`, `auth.revoked`, `auth.replay`;
- `protocol.unsupported`, `schema.invalid`;
- `capability.missing`, `capability.stale`, `policy.denied`;
- `session.notFound`, `session.notEnabled`, `session.revisionMismatch`, `session.runMismatch`;
- `request.expired`, `request.resolved`, `action.digestMismatch`;
- `queue.disallowed`, `queue.expired`, `retention.zero`;
- `attachment.size`, `attachment.hash`, `attachment.expired`;
- `rate.limit`, `host.offline`, `internal.unavailable`.

Errors shown to users contain a safe message and retryability flag. Detailed exceptions remain local and redacted.

## Relay versus direct path

Transport framing is WebSocket text for JSON and binary frames only for negotiated attachment chunks. Both paths use identical signed envelopes. Relay credentials authorize a connection to route envelopes but do not replace device signatures. Direct WSS uses mutual challenge signatures and pinned host certificate/public key; no bearer-only direct mode exists.

## Schema evolution procedure

1. Add/change canonical schema and negative fixtures.
2. Make compatibility tests fail against previous minor.
3. Update TypeScript and Python generated/handwritten types.
4. Prove older clients ignore only noncritical additive fields.
5. Update protocol changelog and acceptance matrix.
6. Security review any new command, secret-bearing field, or retention behavior.
