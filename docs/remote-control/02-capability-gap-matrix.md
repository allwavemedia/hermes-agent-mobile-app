# Capability-Gap Matrix

Legend: **reuse** means current behavior can remain authoritative; **adapt** means add a stable boundary without rewriting Hermes; **new** means no suitable subsystem exists.

| Capability | Current evidence | Gap | Disposition / MVP rule |
|---|---|---|---|
| Local execution | Agent and tools run in local gateway/session processes | None | Reuse; relay never executes Hermes tools |
| Desktop transport | JSON-RPC WS via `apps/shared` and `tui_gateway` | Internal/browser-coupled | Adapt behind `remote-control/v1` |
| Multiple live surfaces | One `session["transport"]` owns scoped events | Last attach steals events | New listener hub + subscriber cursors |
| Session transcript | SessionDB SQLite history | No remote projection/version | Adapt into snapshot with revision and redaction |
| Response streaming | Rich deltas/events | No sequence/replay contract | Adapt to ordered event envelope |
| Tool activity | Start/progress/complete/risk events | Internal payload variance | Normalize and capability-gate |
| Approvals | Existing prompt and `approval.respond` | No remote identity/action binding | New signed approval decision |
| Clarifications | `clarify.respond` | No stale-response defense | Bind request/session/revision/expiry |
| Steering/interrupt | RPCs exist | Retry can duplicate or target stale run | Idempotency and expected run ID |
| Attachments | file/PDF/image RPCs exist | No remote upload integrity/quota | New chunk/blob manifest, hashes, expiry |
| Terminals | terminal/process/shell RPCs exist | Excess authority if exposed raw | Read/write only for Hermes-owned terminal IDs; step-up |
| Models/tools/projects | List/select RPCs exist | Internal shapes and mutation risk | Read capabilities; allow only advertised safe controls |
| MCP | Existing tool/config surfaces | Permanent mutation out of scope | Inspect/enable existing session-scoped options only |
| New sessions | Session create/spawn paths exist | Must constrain cwd/model and online host | Basic signed request, host policy, no offline start |
| Existing-session activation | `session.activate` exists | It rebinds transport | Broker subscription without rebinding |
| Auto-enable | No computer policy | Missing | New opt-in broker policy, off by default |
| Reconnection | 20-second grace | No durable replay/gap repair | Snapshot + bounded journal + ack cursor |
| Offline queue | Experimental messaging backlog | Not session-safe | New selective queue; deny sensitive types |
| Zero retention | No remote-control relay | Missing | Per-computer live-only routing mode |
| Pairing | Browser tickets/OAuth/HMAC connector | No accountless computer pairing | New two-minute QR and device-bound keys |
| Revocation | Messaging 4401 pattern | No paired-device registry | New computer/device revocation and channel close |
| Host startup | launchd/systemd/Task Scheduler implemented | Broker not integrated | Reuse gateway service, add optional subsystem |
| LAN/Tailscale | Local dashboard can listen remotely | No protocol parity/pinning | New WSS direct listener, same auth/protocol |
| Android | None | Entire client absent | New bare RN 0.86 app + focused Kotlin modules |
| Relay deployment | Messaging relay is client-side connector | No session relay service | New provider-neutral Node/PostgreSQL service |
| Notifications | Desktop/dashboard events | Android background push absent | Foreground in-app only; no FCM MVP |
| Audit | Existing logs | Content leakage/no paired actor model | Structured redacted audit schema |
| Signed APK | Desktop packaging exists | Android pipeline absent | New later GitHub Actions/Release flow |

## Claude behavior comparison

| Claude behavior reference | Hermes target | Deliberate difference |
|---|---|---|
| `claude remote-control`, interactive enable, existing-session enable | `hermes remote-control`, gateway policy, Desktop action | Exact command names are proposed, not copied |
| QR and session link | Computer QR pairs device; session list follows | Pair to computer, not individual session |
| Local and remote synchronized | Listener hub projects one Hermes session | Requires new adapter because current transport is exclusive |
| Outbound HTTPS | Host and Android dial WSS relay | Direct fallback is optional and pinned |
| Short-lived scoped credentials | Five-minute challenge credentials | No central user account |
| Server-side transcript/queue retention | Temporary encrypted relay queue or zero retention | Content-trusted MVP is stated explicitly |
| Trusted devices and revocation | Per-computer device registry | Device identity is Android Keystore key |
| Permissions remain local | Existing Hermes approval system remains authoritative | Signed remote decisions add actor/action binding |
| Push notifications | Foreground in-app notifications | FCM intentionally deferred |

## Hard blockers before implementation may advance

1. Prove local Desktop/TUI event delivery is unchanged with two remote subscribers.
2. Prove relay replay produces no duplicates or silent gaps after disconnect.
3. Prove a relay cannot forge an approval despite seeing plaintext.
4. Prove device revocation terminates current and future credentials.
5. Prove secure-store failure cannot fall back to plaintext.
6. Prove direct fallback applies the same authorization and replay rules as relay.
7. Validate host startup and key storage on real Windows and macOS machines.
