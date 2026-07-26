# Gate 0 / Gate 1 Report

Report date: 2026-07-26.

## Gate 0 — Discovery and feasibility

Status: **Complete**.

### Repository

| Item | Result |
|---|---|
| Selected fork | `allwavemedia/hermes-agent-mobile-app` |
| Upstream | `NousResearch/hermes-agent` |
| Clean clone | `A:\Hermes Mobile App\hermes-agent-mobile-app` |
| Isolated worktree | `A:\Hermes Mobile App\hermes-android-remote-control-plan` |
| Planning branch | `plan/hermes-android-remote-control` |
| Baseline | `21a2185f86f64be10d28bec1ecc576d89230f761` |
| Fork main at discovery | `6ffd7302bf4a2178d784f0d296fb8094a48a5bf4` |
| Extracted archive | Preserved, not modified |

### Environment

Windows 11 Pro Insider Preview build 26300 x64, ample disk/memory, Git/GitHub/Node/npm/`uv` ready. Python 3.14.6 is outside Hermes’s supported 3.11–3.13. JDK/Android Studio/SDK/Gradle/ADB/signing tools and Tailscale are missing. Docker/Compose client exists but daemon is stopped. Azure CLI is authenticated; no resource was created. macOS cannot be assessed on this host. Firewall and Defender are enabled; no explicit proxy was found.

### Current capability and reuse

- Desktop uses `apps/shared` JSON-RPC WS to `tui_gateway`; SessionDB is canonical.
- Existing gateway RPC/events cover required session, response, tool, approval, clarification, interruption, attachment, terminal, model/tool/project behaviors.
- Current live session events have a single transport owner; simultaneous safe clients are not supported.
- Current disconnect grace is not durable replay.
- Existing experimental `gateway/relay` is a messaging connector, not a session-sync relay.
- Existing dashboard WS tickets, outbound connector retry/ack patterns, gateway service startup, Electron credential hygiene, and compute supervision patterns are useful evidence/reuse paths.
- A dedicated stable adapter, listener hub, paired identity, replay journal, relay service, Android client, and direct-path policy are required.

### Feasibility

Feasible without extending Hermes authority, provided the first listener/adapter slice proves that local surfaces remain authoritative and every command flows through existing handlers/policy. No production code was changed during Gate 0.

## Gate 1 — Proposed architecture/security approval

Status: **Ready for decision; not self-approved**.

Recommended:

- bare React Native 0.86 Android/API 24 New Architecture;
- framework-neutral `apps/remote-control-protocol`;
- optional Python host broker in existing gateway lifecycle;
- new Node/PostgreSQL provider-neutral relay, one replica MVP;
- trusted-relay content model, TLS 1.3, AES-256-GCM at rest, ES256 sensitive-command integrity;
- two-minute proof-of-possession computer pairing;
- explicit per-session enable by default, opt-in auto-enable;
- temporary 15-minute/10-MiB relay queue or computer-level zero retention;
- five-minute explicit low-risk offline prompt only; all sensitive commands online-only;
- optional pinned WSS LAN/Tailscale direct path with no policy downgrade;
- foreground in-app notifications only;
- signed GitHub Release APK after separate key/release approval.

Rejected: raw public `tui_gateway`, rebranding the experimental messaging relay, polling SessionDB, WebView/PWA, native-only app, FCM MVP, generic RPC/native bridges, and unproven E2EE claims.

### Milestones and effort shape

Nine milestones, 28 atomic test-first tasks:

1. protocol;
2. multi-client gateway;
3. identity/authorization;
4. host broker;
5. relay;
6. Desktop/CLI;
7. Android secure foundation;
8. Android synchronized workflows;
9. operations/release/final proof.

Largest cost drivers are Android + two host platforms, synchronized multi-client correctness, security/race testing, always-warm relay plus PostgreSQL, WebSocket egress, attachments, and macOS/physical-device CI. Cloud pricing is usage-dependent; no resources were created.

### Dependency/license result

Proposed runtime dependencies are MIT/Apache-2.0/PostgreSQL-compatible except Google Code Scanner under Google Android SDK terms. No copyleft/SSPL dependency is proposed. `keyring` 25.7.0 is MIT but must be native-backend allowlisted. React Native template versions are resolved at implementation rather than guessed. SBOM/license/provenance gates are required.

### Unresolved decisions/risks

1. Explicitly accept or reject trusted-relay confidentiality risk for MVP.
2. Confirm five-minute selectively queued prompt behavior versus disabling all offline commands.
3. Confirm manual-code fallback is sufficient for non-GMS Android in MVP.
4. Validate macOS Keychain/launchd/IPC and Windows Credential Locker/service behavior on real hosts.
5. Accept one-replica relay availability trade-off.
6. Select operator domain/region/database/backup/log-retention only during deployment approval.
7. Generate/provision APK signing key only after a separate release gate.

## Change-control status

This branch contains documentation only under `docs/remote-control/`. Production source, dependencies, scaffolding, cloud resources, endpoints, signing keys, and builds were not changed or created. Commit and draft PR identifiers are filled after repository validation and push:

- Documentation commits: pending
- Draft PR: pending

Gate 1 approval authorizes implementation planning to be executed in later PRs; it does not authorize deployment, signing-key creation, or public release by itself.
