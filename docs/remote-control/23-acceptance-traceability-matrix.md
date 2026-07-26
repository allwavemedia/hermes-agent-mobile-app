# Acceptance Traceability Matrix

Status values describe this planning stage: **planned** means design and exact test task exist; no production acceptance test has run.

| Requirement | Design evidence | Verification / implementation task | Status |
|---|---|---|---|
| PR-001 computer pairing | [Pairing](06-pairing-identity-key-lifecycle.md) | Tasks 8, 15, 23; two-claim/key-substitution/expiry E2E | Planned |
| PR-002 computer-first navigation | [Android](10-android-architecture.md), [UX](11-ux-flows.md) | Tasks 21, 24; multi-computer UI tests | Planned |
| PR-003 explicit session enable | [Host](09-host-desktop-integration.md) | Tasks 6, 13, 20; default-deny test | Planned |
| PR-004 opt-in auto-enable | [Host](09-host-desktop-integration.md) | Tasks 13, 20; current/future session policy tests | Planned |
| PR-005 online new session | [Product](03-product-requirements.md) | Tasks 5, 13, 25; advertised project/model only | Planned |
| PR-006 synchronized transcript/stream | [Architecture](04-system-architecture.md), [Protocol](05-remote-control-protocol.md) | Tasks 2, 4–6, 17, 24–25 | Planned |
| PR-007 tool activity | [Protocol event types](05-remote-control-protocol.md#ordered-events) | Tasks 5, 25; normalization/UI fixtures | Planned |
| PR-008 clarification/approval | [Approval binding](05-remote-control-protocol.md#approval-and-clarification-binding) | Tasks 10, 25; mutation/race/biometric tests | Planned |
| PR-009 steer/interrupt | [Reconnection](14-reconnection-queueing.md) | Tasks 5, 25; run mismatch/idempotency | Planned |
| PR-010 attachments | [File transfer](13-file-transfer.md) | Tasks 18, 26; hash/traversal/expiry E2E | Planned |
| PR-011 capability-driven controls | [Capability policy](03-product-requirements.md#capability-policy) | Tasks 3, 5, 10, 25 | Planned |
| PR-012 reconnect/replay | [Reconnection](14-reconnection-queueing.md) | Tasks 2, 11, 17, 24, 26; chaos corpus | Planned |
| PR-013 temporary queue | [Relay](08-relay-design.md), [offline matrix](14-reconnection-queueing.md#offline-matrix) | Tasks 16–17; restart/expiry/type matrix | Planned |
| PR-014 zero retention | [Retention modes](08-relay-design.md#retention-modes) | Tasks 16, 18, 26; DB/blob/log no-write spies | Planned |
| PR-015 LAN/Tailscale fallback | [Network paths](04-system-architecture.md#network-paths) | Tasks 14, 24; parity/MITM/pin tests | Planned |
| PR-016 foreground notifications/no FCM | [UX](11-ux-flows.md#foreground-notifications) | Task 26; manifest/dependency/background tests | Planned |
| PR-017 device revocation | [Key lifecycle](06-pairing-identity-key-lifecycle.md#rotation-and-revocation) | Tasks 9, 15, 19, 20 | Planned |
| PR-018 signed GitHub Release APK | [Release](18-release-signing.md) | Task 28; signer/checksum/SBOM/provenance gates | Planned |
| NFR-001 API 24/RN New Architecture | [Android baseline](10-android-architecture.md#baseline) | Task 21; Gradle/manifest/emulator tests | Planned |
| NFR-002 command ack latency | [Product](03-product-requirements.md#non-functional-requirements) | Task 17 and load gate; p95 <2 s | Planned |
| NFR-003 event latency | [Observability](15-audit-observability.md#alerts-and-slos) | Tasks 17, 27; p95 <1 s | Planned |
| NFR-004 no silent loss | [Event consistency](04-system-architecture.md#event-consistency) | Tasks 2, 11, 17; gap property/chaos tests | Planned |
| NFR-005 bounded journal | [Data](12-data-persistence.md) | Tasks 11, 16; 15 min/10 MiB eviction tests | Planned |
| NFR-006 relay restart durability | [Reconnection](14-reconnection-queueing.md#command-recovery) | Tasks 16–17; PostgreSQL restart test | Planned |
| NFR-007 log redaction | [Audit](15-audit-observability.md) | Tasks 13, 16, 27; canary scan | Planned |
| NFR-008 accessibility | [UX](11-ux-flows.md#accessibilityerror-copy-rules) | Tasks 21, 25–26; RNTL/Detox/a11y review | Planned |
| NFR-009 host overhead | [Product](03-product-requirements.md#non-functional-requirements) | Task 27 soak/profile; <100 MiB/<1% idle target | Planned |
| NFR-010 protocol negotiation | [Compatibility](05-remote-control-protocol.md#compatibility) | Tasks 1–3; old/new compatibility corpus | Planned |
| SEC-001 TLS distinction/no E2EE claim | [Threat model](07-threat-model.md) | Tasks 14, 24, 27; copy/TLS/MITM review | Planned |
| SEC-002 device-bound keys | [Identity](06-pairing-identity-key-lifecycle.md) | Tasks 7, 22; backend/Keystore proof | Planned |
| SEC-003 replay defense | [Envelope](05-remote-control-protocol.md#envelope) | Tasks 3, 9–11, 15 | Planned |
| SEC-004 approval binding | [Approval semantics](07-threat-model.md#approval-semantics) | Tasks 10, 25; full mutation matrix | Planned |
| SEC-005 stale-sensitive rejection | [Offline matrix](14-reconnection-queueing.md#offline-matrix) | Tasks 3, 10, 16, 25 | Planned |
| SEC-006 attachment integrity | [File transfer](13-file-transfer.md) | Tasks 18, 26 | Planned |
| SEC-007 Android component/network rules | [Android lifecycle](10-android-architecture.md#lifecyclesecurity) | Tasks 21–24 | Planned |
| SEC-008 secure host storage | [Pairing identity](06-pairing-identity-key-lifecycle.md#identity-model) | Task 7; native backend fail-closed | Planned |
| SEC-009 direct-path parity | [Direct path](05-remote-control-protocol.md#relay-versus-direct-path) | Tasks 14, 24 | Planned |
| SEC-010 supply-chain/release | [Audit](20-dependency-license-supply-chain.md) | Tasks 21, 27–28 | Planned |
| OOS-001 no remote desktop | [Mission boundary](00-executive-brief.md#mission-and-boundary) | API/schema review finds no screen-control type | Planned |
| OOS-002 no independent shell/files/Git/process | [Capability policy](03-product-requirements.md#capability-policy) | Adapter allowlist and negative tests Tasks 5, 10, 25 | Planned |
| OOS-003 no managed cloud execution/offline wake | [Product](03-product-requirements.md) | Session-create/offline matrix tests | Planned |
| OOS-004 no provider secret/permanent MCP admin | [Host local-only](09-host-desktop-integration.md#local-only-operations) | capability/UX negative tests | Planned |
| OOS-005 no Play Store/push/recovery export | [Release](18-release-signing.md), [Android](10-android-architecture.md) | dependency/manifest/workflow tests | Planned |

Gate 2 closes a row only with a link to a passing CI run, platform evidence artifact, or reviewed manual record. “Code exists” is not acceptance evidence.
