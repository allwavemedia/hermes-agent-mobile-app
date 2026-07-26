# Security Review Findings

Review date: 2026-07-26. Scope: planned protocol, pairing, relay, host adapter/broker, Android architecture, storage, operations, and release. This is a design review; implementation requires a second review with test evidence.

## Findings resolved in this plan

### SR-01 — A multi-client mobile connection would steal the current session transport

Severity before mitigation: Critical.

Evidence: `session.resume`/`session.activate` rebind `session["transport"]`; scoped writes target it.

Resolution: independent bounded `SessionEventHub`; adapter subscriptions are not transports; Task 4/6 invariants block further work.

Status: design resolved, implementation unproven.

### SR-02 — Session IDs and browser-oriented tickets are insufficient pairing identity

Severity before mitigation: Critical.

Resolution: device/host P-256 proof of possession, two-minute one-time capability, transcript phrase, short-lived connection credentials, trust epoch and revocation.

Status: design resolved, Tasks 7–9/15/22–23 required.

### SR-03 — Relay-visible plaintext could permit forged approvals if bearer auth were reused

Severity before mitigation: Critical.

Resolution: device-signed ES256 decision bound to computer/device/session/run/tool/action/display/revision/capability/expiry; host recomputes digest. Relay credential is routing authority only.

Status: design resolved, Tasks 3/10/25 required.

### SR-04 — “E2EE” would be a false claim for the proposed MVP

Severity: High (trust/consumer harm).

Resolution: relay is explicitly content-trusted. TLS, at-rest encryption, and signatures are named separately. Zero-retention/direct choices are offered.

Status: resolved; copy review remains a release gate.

### SR-05 — Existing experimental messaging relay is the wrong security/session boundary

Severity: High.

Resolution: no modification/reuse as mobile wire contract; patterns only. Dedicated stable adapter and protocol have separate namespaces/tests.

Status: resolved by architecture.

### SR-06 — Offline approvals and stale sensitive commands create confused-deputy risk

Severity: Critical.

Resolution: only explicitly opted-in low-risk `prompt.submit` can queue for five minutes under exact revision/policy/capability checks. Every sensitive command is online-only.

Status: design resolved, queue matrix tests required.

### SR-07 — Host key persistence could silently fall back to plaintext

Severity: Critical.

Resolution: `keyring` backend allowlist for Windows Credential Locker/macOS Keychain and fail closed; no file/null/third-party backend.

Status: design resolved, real-platform proof required.

### SR-08 — Direct fallback could become an authentication downgrade/public endpoint

Severity: Critical.

Resolution: disabled by default, private/Tailscale explicit interfaces, WSS SPKI pin, same signed envelopes and host authorization, no UPnP/public bind/bearer-only mode.

Status: design resolved, network/MITM tests required.

## Residual/open findings

### SR-09 — Trusted relay confidentiality

Severity: High, accepted only with explicit Gate 1 decision.

Risk: relay worker/operator compromise can expose content in default retention mode.

Compensating controls: bounded AES-GCM storage, zero retention, direct path, least privilege, no content logs.

Decision: accept for MVP or require a separate E2EE design phase. Do not imply E2EE.

### SR-10 — macOS native keychain and startup are unverified on current Windows host

Severity: High for release readiness, not architecture.

Action: real macOS current/current-1 tests for Keychain access when logged in/locked, launchd restart/update/uninstall, IPC permissions and direct bind.

Owner/gate: host implementation; blocks release.

### SR-11 — Android scanner depends on Google Play services

Severity: Medium.

Action: mandatory manual code/verified App Link fallback and explicit availability tests. If distribution targets non-GMS fleets, reconsider bundled ML Kit under dependency/security review.

### SR-12 — Single-replica relay availability

Severity: Medium.

Risk: update/crash reconnect window.

Action: protocol replay/snapshot; document SLO. Multi-replica design is deferred until connection-directory/fan-out correctness tests exist.

### SR-13 — Backup deletion lag

Severity: Medium.

Risk: content deleted logically can persist in provider backups for backup retention.

Action: minimum backup window, encryption/key lifecycle, privacy copy/runbook; zero-retention content never enters backup.

### SR-14 — Endpoint compromise and accessibility observation

Severity: Medium/residual.

Action: Keystore, biometrics, secure windows, lifecycle lock and user education. Root/admin/accessibility-granted malware cannot be fully contained.

## Security go/no-go criteria

No-go for release if:

- any Critical/High implementation finding is unresolved or lacks explicit owner/date;
- local transport identity changes under remote subscription;
- relay can forge or replay a valid approval;
- native key store or Android network policy falls back insecurely;
- zero-retention content appears in persistent store/log;
- direct path accepts wrong pin, cleartext, public bind, or weaker authorization;
- signed release provenance/signer check fails.

Security review recommends Gate 1 only if SR-09 trusted-relay risk is explicitly accepted and SR-10 is a release-blocking platform validation item.
