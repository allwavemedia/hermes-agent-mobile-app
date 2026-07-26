# Testing Strategy

## Test pyramid and required platforms

| Layer | Scope | Tools |
|---|---|---|
| Schema/contract | valid/invalid fixtures, canonicalization, compatibility | Vitest/Jest, Pytest, Ajv/jsonschema |
| Pure state/property | reducer ordering, replay, idempotency, expiry | Vitest + fast-check, Pytest/Hypothesis if added |
| Host unit | policy, secure store, pairing, journal, adapter normalization | Pytest |
| Relay unit/integration | auth, DB transactions, queue crypto/expiry, WS routing | Node test runner/Vitest + PostgreSQL |
| Gateway integration | two subscribers + Desktop/TUI transport, handler mapping | Pytest with in-memory transports |
| Android unit | Kotlin key/link/lifecycle modules, TS feature state | JUnit/Robolectric, RNTL |
| Android E2E | pairing/session/approval/reconnect/lifecycle | Detox on API 24 and current API emulator |
| Cross-component | Android/protocol/relay/host compatibility | Compose + emulator + fake Hermes, then real Hermes smoke |
| Platform | startup/secure store/direct network | real Windows 11 and macOS current-2/current |
| Security/chaos/load | tampering, replay, MITM, slow clients, restart | custom harness, OWASP ZAP where applicable, toxiproxy/netem equivalent |

## Contract matrix

Every schema has:

- minimal valid fixture;
- maximal valid fixture;
- unknown additive noncritical field;
- missing required field;
- duplicate/unknown critical field;
- oversized string/array;
- invalid ID/time/base64url;
- expired/future/skewed envelope;
- altered signature;
- cross-computer/device/session substitution.

The same corpus must pass/fail identically in TypeScript, Python, Kotlin parser boundary, and relay.

## Critical invariants

1. Adding/removing a remote subscriber never changes `session["transport"]`.
2. A subscriber exception/slow queue cannot delay or fail local event delivery.
3. Reducer yields the same state after duplicate delivery and never accepts a gap.
4. Same idempotency key/digest executes at most once; different digest conflicts.
5. Approval only resolves the exact pending tool call/action/run/revision displayed.
6. Revoked device cannot connect, renew, queue, replay, or use direct path.
7. Zero-retention traffic never writes content to DB/blob/log/backup fixtures.
8. Direct fallback and relay produce identical authorization decisions.
9. Secure-store unsupported backend stops enablement without plaintext artifacts.
10. No Android exported component or cleartext path exceeds the allowlist.

## Race and chaos cases

- Desktop answers while Android biometric dialog is open;
- run ends/restarts before approval arrives;
- host restarts between command acceptance and receipt;
- relay restarts after queue transaction but before ack;
- two devices claim one pairing offer;
- revoke races credential renewal and queued delivery;
- event journal expires during replay;
- attachment expires during final chunk;
- PID is reused before session re-registration;
- app rotates/backgrounds/process-dies during pairing/upload/approval;
- clock skew at ±59 s, ±5 min, and beyond tolerance;
- slow consumer reaches buffer cap;
- PostgreSQL/blob/KEK becomes unavailable independently.

## Security verification

- TLS scanner and cleartext capture on relay/direct paths;
- MITM certificate/user-CA rejection in release Android build;
- JWS algorithm confusion (`none`, wrong curve/key, duplicate header), canonicalization and malleability tests;
- nonce/JTI replay and cache eviction tests;
- QR parser fuzzing and App Link/exported-component inspection;
- path traversal/symlink/archive bomb and attachment hash tests;
- Logcat/server/audit canary scan;
- dependency, secret, SBOM, container and APK static scans;
- Android backup extraction and Keystore non-exportability checks.

Custom crypto primitives are forbidden; tests validate integration with maintained libraries, not home-grown algorithms.

## Performance/load gates

Reference test: 1,000 online computers, two devices/computer, five subscriptions/device, 20 events/sec burst for 60 seconds, with realistic bounded payloads. Single-replica MVP must remain within configured memory, produce no silent gaps, and meet p95 event/ack targets or document lower supported capacity.

Attachment test saturates configured bandwidth without starving approvals/interrupts; control frames have priority queues. Soak test runs 24 hours with reconnect churn and expiry workers, checking memory/DB/object leakage.

## Release gates

CI blocks on schema/contract/unit/integration, Linux relay/host, Windows host, Android unit/lint/build, dependency review, secret scan, SBOM, and docs/traceability. macOS host/startup/keychain and Android physical-device biometric/direct-pin tests are manual-or-self-hosted required evidence before public GitHub Release. A failing security invariant cannot be waived by flaky-test retry.

Exact commands and expected outcomes appear in [test-first implementation plan](22-test-first-implementation-plan.md).
