# Threat Model

Method: STRIDE plus abuse cases. Security boundary claims apply only when the planned controls and tests pass.

## Assets and trust boundaries

Assets include host/device private keys, pairing capability, relay connection credentials, session content, approval decisions, attachments, capability/policy state, local provider secrets, Hermes-owned terminal/process handles, revocation state, and audit integrity.

Trust boundaries:

1. Android app ↔ Android OS/Keystore/biometrics.
2. Android ↔ relay over public network.
3. Host broker ↔ relay.
4. Broker ↔ local session process over local IPC.
5. Adapter ↔ internal gateway handlers.
6. Relay application ↔ PostgreSQL/blob storage/operator.
7. Optional Android ↔ direct host listener.

The relay is trusted for confidentiality and availability in MVP, but not for authorizing security-sensitive commands. The local OS user and existing Hermes process retain their current authority. Root/admin or a fully compromised endpoint is outside the product’s ability to contain, but compromise must not silently expand to another paired computer.

## Threats and controls

| ID | Threat | Impact | Required controls | Verification |
|---|---|---|---|---|
| T-01 | QR photographed/reused | Unauthorized device pairing | 256-bit capability, two-minute expiry, atomic single use, attempt limits, phrase confirmation | pairing concurrency/expiry tests |
| T-02 | Relay substitutes pairing key | MITM device/host | host-signed offer, both-key transcript signatures, phrase comparison | tampered-key negative tests |
| T-03 | Stolen bearer credential | Session access | five-minute audience/connection credential, challenge renewal, memory-only storage, JTI/revocation | credential replay tests |
| T-04 | Relay forges approval | Tool authority escalation | Android ES256 signature with exact action/display/session/run/revision binding; host verification | forged/mutated approval tests |
| T-05 | Old approval replayed | Wrong tool action | JTI cache, ≤60 s expiry, request state, action digest, tool-call/run ID | time/race/property tests |
| T-06 | Capability confused across sessions/computers | Cross-target action | computer/device/session IDs and capability hash in signed envelope; computer-first UI | cross-binding matrix |
| T-07 | Last client steals transport | Local control loss/event leak | independent listener hub; never assign remote subscriber to session transport | two-client integration test |
| T-08 | Event dropped/reordered | Incorrect mobile state | epoch, seq/prevSeq, ack, replay, snapshot reset | chaos/property tests |
| T-09 | Offline sensitive action executes stale | Unsafe approval/config/action | deny queue for sensitive types; expected revision/policy hash; five-minute low-risk prompt TTL | offline matrix |
| T-10 | Attachment substitution/traversal | Data compromise | content-addressed manifest, SHA-256, size/type limits, generated temp names, adapter-owned resolution | traversal/hash tests |
| T-11 | Terminal handle reused | Wrong-process command | Hermes-owned terminal ID, process birth identity, current capability, biometric step-up, no arbitrary command API | PID-reuse tests |
| T-12 | Relay DB/blob theft | Content disclosure | AES-256-GCM per-computer DEK, wrapped KEK, least privilege, expiry, zero retention | restore/key/expiry tests |
| T-13 | Malicious relay operator reads content | Confidentiality loss | explicitly accepted MVP risk; zero-retention option; direct path; future E2EE ADR | wording/security review |
| T-14 | Logs leak prompts/secrets/paths | Secondary disclosure | allowlisted structured fields; keyed hashes; content-free errors; redaction tests | canary scan |
| T-15 | Android backup/export leaks pairing | Device cloning | Keystore non-exportable key, backup exclusions, no recovery export | manifest/device tests |
| T-16 | Overlay/screenshot captures approval | Social engineering | secure window for sensitive screens, obscured-touch rejection, exact digest text | Android UI security tests |
| T-17 | Malicious deep link | Pairing/domain injection | verified App Link, strict parser, origin allowlist, one-time code; unexported components | manifest/parser tests |
| T-18 | Cleartext/direct downgrade | Network interception | cleartext disabled, Network Security Config, WSS pin, same protocol/auth, no fallback on pin error | MITM tests |
| T-19 | Host secure-store fallback | Private-key theft | backend allowlist and fail closed | backend substitution tests |
| T-20 | Compromised phone controls all hosts | Multi-host blast radius | distinct per-computer pairing records, local revocation, app lock/step-up, computer-first confirmation | cross-host tests |
| T-21 | DoS via streams/files/pairing | Cost/availability | per-device/computer/IP quotas, bounded queues, backpressure, circuit breakers | load/abuse tests |
| T-22 | Dependency/build compromise | APK/relay compromise | exact locks, reviews, provenance, SBOM, dependency review, pinned actions, signing isolation | CI policy tests |

## Approval semantics

“Approve once” authorizes exactly one normalized action digest for one pending tool call in one active run. It is not a shell wildcard, tool-wide grant, session-wide grant, or policy mutation. The host re-renders/normalizes the underlying action and recomputes the digest immediately before passing the decision to existing Hermes approval handling. Any difference is denied.

Remote secret/sudo value entry is excluded from MVP because relaying those values increases content and endpoint risk. The phone may display that local attention is required.

## Android component and lifecycle rules

- Only the verified HTTPS pairing App Link activity is exported.
- All services, receivers, providers, and TurboModule helpers are non-exported unless Android requires otherwise and a threat review approves it.
- `android:allowBackup="false"` plus data-extraction/backup rules exclude every remote-control store.
- cleartext traffic is disabled; user-added CAs are not trusted by release builds.
- sensitive approval/pairing screens use `FLAG_SECURE`; app switcher snapshots are obscured.
- background/lock transitions clear decrypted projections and require unlock according to policy.
- clipboard is not used for credentials; manual codes clear after submission.

## Residual risks

- Trusted relay and operators can read routed content in non-zero-retention mode.
- Endpoint malware at the user’s privilege can interact with local Hermes and may access displayed content.
- Android accessibility services can observe UI content according to OS permissions.
- No FCM means users receive no attention prompt when app is closed.
- Single-replica MVP relay creates an availability window during restart.
- Pairing phrase comparison depends on user behavior.

These risks are visible in product copy and Gate 1; none is masked by an E2EE or “zero knowledge” claim.
