# Product Requirements

## Personas and primary jobs

- **Individual operator:** pair a personal Android phone with one or more computers, monitor ongoing work, answer a clarification, approve or deny a bounded action, steer/interrupt, and resume locally.
- **Security-conscious operator:** disable content retention, inspect devices, revoke a phone, require biometrics for sensitive actions, and use a private direct path.
- **Self-hosting operator:** run the provider-neutral relay with Docker Compose or the Azure reference without adopting Entra as product identity.

## Functional requirements

| ID | Requirement | Acceptance summary |
|---|---|---|
| PR-001 | Pair an entire online computer using a one-time QR or manual/deep-link equivalent | Two-minute single-use offer; both keys prove possession; user confirms matching phrase |
| PR-002 | Show paired computers before sessions | Online, last seen, retention mode, trust status, version, and revocation state are visible |
| PR-003 | Explicitly enable an existing session for remote access | Default deny; local UI/CLI action advertises it without moving event ownership |
| PR-004 | Offer opt-in auto-enable for future sessions | Computer-level policy is off by default, locally changeable, auditable |
| PR-005 | Request a basic new session on an online host | Host validates project/cwd/model against advertised choices; no offline wake/start |
| PR-006 | Synchronize transcript and streaming events | Snapshot revision plus ordered replay; Desktop/TUI and Android converge |
| PR-007 | Show tool activity and requests | Normalized start/progress/complete/risk and bounded outputs |
| PR-008 | Answer clarifications and approvals | Exact request binding, expiry, stale rejection, biometric step-up by risk |
| PR-009 | Steer or interrupt the active run | Expected run ID and idempotency key prevent stale/duplicate action |
| PR-010 | Transfer Hermes-mediated attachments | Size/type policy, SHA-256 integrity, expiry, cancellation, local mediation |
| PR-011 | Expose only capability-driven controls | Missing/unknown/expired capability is denied; no hidden generic RPC console |
| PR-012 | Reconnect after network/app lifecycle changes | Resume from acknowledged cursor or fetch a fresh snapshot on gap |
| PR-013 | Support temporary encrypted queueing | Bounded time/size; selective low-risk offline prompt only |
| PR-014 | Support computer-level zero retention | No content persistence at relay; minimum identity/revocation/security metadata only |
| PR-015 | Offer authenticated LAN/Tailscale fallback | Explicitly enabled, private bind, pinned WSS, identical envelopes/policy |
| PR-016 | Provide in-app foreground notifications | No FCM permission, token, or background push dependency in MVP |
| PR-017 | Revoke one device or all devices | Active channels close; credentials rejected; audit event recorded |
| PR-018 | Distribute a signed APK after a later gate | Reproducible GitHub Actions build, protected signing secret, Release checksum/provenance |

## Non-functional requirements

| ID | Target |
|---|---|
| NFR-001 | Android API 24 minimum; current supported RN New Architecture |
| NFR-002 | p50 command acknowledgement under 500 ms and p95 under 2 s, excluding model/tool work, on a healthy relay path |
| NFR-003 | Streaming event display p95 under 1 s from host publication on a healthy path |
| NFR-004 | No silent loss: every cursor gap causes replay or an explicit snapshot reset |
| NFR-005 | Default journal: 15 minutes and 10 MiB per computer, whichever first |
| NFR-006 | Relay survives process restart without losing persisted non-zero-retention queue metadata/content |
| NFR-007 | Secrets and content are redacted from logs; audit records stable IDs/hashes only |
| NFR-008 | Accessibility: screen-reader labels, 48 dp touch targets, scalable text, non-color status cues |
| NFR-009 | Host idle overhead target under 100 MiB RSS and 1% CPU, measured separately from Hermes sessions |
| NFR-010 | Protocol compatibility: host and app negotiate major/minor and reject unsupported security semantics |

## Capability policy

The host signs a capability snapshot containing protocol versions, computer ID, session ID, snapshot revision, available methods, risk class, constraints, and expiry. The app renders only those controls. The broker independently verifies every command against the current snapshot and existing Hermes policy. UI visibility is not authorization.

Remote control never exposes:

- arbitrary filesystem paths, shell commands, Git operations, credentials, provider secrets, or unrelated processes;
- permanent MCP installation/configuration;
- starting or waking an offline machine;
- secret or sudo value entry in MVP;
- cloud-managed Hermes execution.

## Retention and queue policy

Default mode permits a temporary encrypted event/command queue for 15 minutes and 10 MiB per computer. Attachments have separate limits and are deleted by an hourly expiry sweep. Zero-retention mode permits live routing only; it retains device public keys, revocation state, hashed abuse controls, and content-free security audit metadata as operational minimums.

Only `prompt.submit` may be queued while a host is offline, and only when the host previously advertised `offlinePrompt.v1`, the user explicitly selects “send if reconnected,” expected session/capability/policy hashes are present, and TTL is at most five minutes. Approvals, clarifications, interrupts, terminal input, files, new sessions, model/tool/MCP/config mutations, and other sensitive actions are rejected while stale/offline.

## MVP success and stop conditions

Success requires two concurrent surfaces, Windows and macOS host coverage, accountless pairing, relay and direct-path parity, deterministic replay, signed sensitive decisions, revocation, zero retention, and a signed internal APK.

Stop release if any test demonstrates transport theft, approval confusion, plaintext key fallback, cleartext network traffic, replayed state-changing commands, capability bypass, content-bearing logs, or rollback that strands active sessions.
