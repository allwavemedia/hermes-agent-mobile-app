# Exact File-by-File Change Plan

This is the proposed production change inventory. Any implementation PR that needs another production file must update this document and receive architecture/security review first. Generated lockfiles and RN template files are still reviewed.

## Root dependency and CI files

| File | Planned change |
|---|---|
| `package.json` | Add only cross-workspace validation/release scripts if required; existing `apps/*` glob already covers new packages |
| `package-lock.json` | Lock all Android/protocol/relay workspaces and exact transitive dependencies |
| `pyproject.toml` | Add opt-in remote-control dependencies (`rfc8785==0.1.4`, later `keyring>=25.7,<26`); add test markers only if needed |
| `uv.lock` | Lock host dependency graph |
| `.github/workflows/ci.yml` | Wire existing reusable jobs to new remote-control checks if current orchestrator requires it |
| `.github/workflows/android-remote.yml` | Android unit/lint/debug build/emulator contract gates; no release secrets on PR |
| `.github/workflows/remote-relay.yml` | Protocol/relay/PostgreSQL/Compose tests, SBOM and image scan |
| `.github/workflows/android-remote-release.yml` | Protected-tag signed APK, verification, SBOM/provenance, GitHub Release |
| `.github/dependabot.yml` | Add npm/Gradle paths only if not already covered |
| `CODEOWNERS` or `.github/CODEOWNERS` (whichever exists at implementation baseline) | Require security/Android/relay owners for sensitive paths; do not create both |

## Framework-neutral protocol workspace

| File | Planned content |
|---|---|
| `apps/remote-control-protocol/package.json` | Private workspace, exports, check/test/build scripts; runtime declarations for `ajv` and RFC 8785 Appendix G `canonicalize`; `jose` is test-only here and becomes a relay runtime dependency when the Node crypto adapter lands |
| `apps/remote-control-protocol/tsconfig.json` | Strict TS, no DOM dependency |
| `apps/remote-control-protocol/src/index.ts` | Deliberate public exports |
| `apps/remote-control-protocol/src/version.ts` | v1 major/minor negotiation |
| `apps/remote-control-protocol/src/types.ts` | Envelope/snapshot/event/capability/command/receipt types |
| `apps/remote-control-protocol/src/validate.ts` | Ajv validators and stable schema errors |
| `apps/remote-control-protocol/src/canonicalize.ts` | RFC 8785-compatible canonical bytes plus a narrow async hash/strict-ES256 runtime adapter contract; no Node or assumed WebCrypto import |
| `apps/remote-control-protocol/src/risk.ts` | Risk classes and queue/step-up policy constants |
| `apps/remote-control-protocol/src/reducer.ts` | Epoch/sequence/idempotent projection reducer |
| `apps/remote-control-protocol/src/compatibility.ts` | Minor negotiation/unknown-critical rules |
| `apps/remote-control-protocol/src/*.test.ts` | Fixture, property, reducer, compatibility, canonicalization tests |
| `apps/remote-control-protocol/fixtures/v1/*.json` | Shared valid/invalid contract corpus copied/generated from canonical docs schemas |
| `apps/remote-control-protocol/scripts/copy-schemas.mjs` | Build-only Node script that copies the canonical schemas into `dist/schemas/v1/` and fails unless every emitted file is byte-identical |

Canonical schemas remain under `docs/remote-control/schemas/v1/`; the package build copies them and verifies byte identity rather than maintaining a second source.

## Gateway listener and stable adapter

| File | Planned change |
|---|---|
| `tui_gateway/transport.py` | Add `SessionEventListener` protocol and nonblocking bounded `SessionEventHub`; preserve transports |
| `tui_gateway/server.py` | Publish normalized copies after existing write routing; expose adapter-safe handler invocation without transport rebinding |
| `tui_gateway/entry.py` | Create/register adapter endpoint when broker credential/IPC descriptor is present |
| `tui_gateway/ws.py` | No wire expansion; only thread adapter lifecycle if tests prove required |
| `tests/tui_gateway/test_remote_event_hub.py` | Local transport plus two remote listeners, isolation/backpressure/order |
| `tests/tui_gateway/test_remote_adapter.py` | Allowlisted commands/snapshot/capabilities and no generic RPC |
| `tests/tui_gateway/test_remote_multi_client.py` | Desktop/TUI ownership invariant and concurrent command race |
| `tests/tui_gateway/test_remote_event_normalization.py` | Internal-to-v1 event fixture mapping |

## New Python host package

| File | Planned content |
|---|---|
| `remote_control/__init__.py` | Stable package exports/version |
| `remote_control/models.py` | Typed protocol/domain models; no raw gateway dictionaries outside adapter |
| `remote_control/protocol.py` | JSON schema load/validation and JCS/JWS integration |
| `remote_control/identity.py` | host/device public identity, thumbprints, trust epoch |
| `remote_control/secure_store.py` | `keyring` native-backend allowlist and fail-closed key access |
| `remote_control/pairing.py` | offer/claim/transcript/proof/expiry state machine |
| `remote_control/credentials.py` | challenge and short-lived credential verification |
| `remote_control/authorization.py` | capability/revision/risk/approval/action-digest enforcement |
| `remote_control/replay.py` | epoch/sequence journal, ack/replay/reset |
| `remote_control/idempotency.py` | command receipt persistence/conflict handling |
| `remote_control/storage.py` | SQLite schema/migrations/transactions/expiry |
| `remote_control/adapter.py` | `GatewaySessionAdapter` and exact RPC/event mappings |
| `remote_control/ipc.py` | AF_PIPE/AF_UNIX authenticated framed IPC |
| `remote_control/registry.py` | PID/start-time/session registration and reaping via `psutil` |
| `remote_control/relay_transport.py` | outbound WSS auth/reconnect/multiplex transport |
| `remote_control/direct_transport.py` | opt-in pinned WSS listener with identical envelopes |
| `remote_control/attachments.py` | manifests, temporary files, hashes, cleanup |
| `remote_control/audit.py` | allowlisted structured security audit/redaction |
| `remote_control/broker.py` | subsystem orchestration, route/session/device lifecycle |
| `remote_control/config.py` | validated non-secret config projection |
| `remote_control/errors.py` | stable safe reason codes |
| `remote_control/migrations/001_initial.sql` | separate host metadata/journal schema |
| `tests/remote_control/conftest.py` | fake clock/keys/relay/session fixtures |
| `tests/remote_control/test_*.py` | one focused module test file per module above |
| `tests/remote_control/test_broker_integration.py` | broker/session/relay vertical integration |
| `tests/remote_control/test_direct_parity.py` | relay/direct authorization parity corpus |
| `tests/remote_control/test_log_redaction.py` | canary content scan |

## Existing gateway/service/CLI integration

| File | Planned change |
|---|---|
| `gateway/config.py` | Parse/default `remote_control` config, default disabled |
| `gateway/run.py` | Start/stop/status optional broker beside existing subsystems; do not modify messaging relay contract |
| `hermes_cli/subcommands/gateway.py` | Add remote-control status/pair/revoke/enable/configured subcommands |
| `hermes_cli/main.py` | Dispatch new structured subcommands |
| `hermes_cli/gateway.py` | Include broker status in macOS/system service status only if required by existing abstraction |
| `hermes_cli/gateway_windows.py` | Include broker status only; retain existing Scheduled Task/Startup behavior |
| `tests/gateway/test_remote_control_config.py` | Defaults/validation/no-secret config |
| `tests/gateway/test_remote_control_lifecycle.py` | broker optional startup/shutdown/failure isolation |
| `tests/cli/test_remote_control_cli.py` | exact command parsing/output/error behavior |
| `tests/cli/test_remote_control_service_status.py` | Windows/macOS service status projection |

## Desktop integration

| File | Planned change |
|---|---|
| `apps/desktop/electron/main.ts` | Register typed broker IPC handlers; main process remains authority |
| `apps/desktop/electron/preload.ts` | Expose narrow remote-control API |
| `apps/desktop/electron/hardening.ts` | Validate IPC origin/argument limits; no renderer secrets |
| `apps/desktop/src/global.d.ts` | Declare narrow preload API |
| `apps/desktop/src/app/settings/index.tsx` | Register Remote Control section |
| `apps/desktop/src/app/settings/gateway-settings.tsx` | Link broker/service state without conflating messaging gateway relay |
| `apps/desktop/src/app/settings/remote-control-settings.tsx` | Pairing, devices, retention, auto-enable, direct fallback |
| `apps/desktop/src/app/settings/remote-control-settings.test.tsx` | UI/state/error/security-copy tests |
| `apps/desktop/src/app/chat/sidebar/session-actions-menu.tsx` | Per-session remote enable/disable action |
| `apps/desktop/src/app/chat/sidebar/session-actions-menu.test.tsx` | Action availability/result tests |
| `apps/desktop/src/app/chat/sidebar/session-row.tsx` | Remote presence indicator |
| `apps/desktop/src/app/remote-control/types.ts` | Renderer-safe DTOs |
| `apps/desktop/src/app/remote-control/store.ts` | Feature-owned nanostore |
| `apps/desktop/src/app/remote-control/api.ts` | Preload calls and safe errors |
| `apps/desktop/src/app/remote-control/*.test.ts` | Store/API/pair countdown/revocation tests |
| `apps/desktop/electron/remote-control-ipc.test.ts` | IPC allowlist/validation/no-secret tests |

If current Desktop i18n becomes the controlling baseline before implementation, add strings to its existing locale source identified at that commit; do not create a parallel localization system.

## Relay workspace

| File | Planned content |
|---|---|
| `apps/remote-control-relay/package.json`, `tsconfig.json` | Private Node TS workspace and strict scripts |
| `apps/remote-control-relay/src/main.ts` | Composition root and graceful shutdown |
| `src/config.ts` | validated env, no unsafe defaults |
| `src/http.ts` | health/readiness/pairing/attachment routes |
| `src/websocket.ts` | connection framing/backpressure |
| `src/auth.ts` | nonce challenge, JWS verification, five-minute credentials |
| `src/routes.ts` | in-memory paired connection directory |
| `src/pairing.ts` | transactional offers/claims/consumption |
| `src/revocation.ts` | trust epochs and connection termination |
| `src/queue.ts` | allowed-type queue, leases, TTL/quota |
| `src/crypto.ts` | AES-256-GCM envelope encryption and DEK wrapping |
| `src/attachments.ts` | grants, storage interface, hash/expiry |
| `src/storage.ts`, `src/postgres.ts` | repository contracts/transactions |
| `src/audit.ts`, `src/metrics.ts` | allowlisted telemetry |
| `src/errors.ts` | safe protocol/HTTP close codes |
| `migrations/001_initial.sql` | initial tables/indexes/constraints |
| `src/**/*.test.ts` | unit/property/negative tests matching modules |
| `test/integration/*.test.ts` | PostgreSQL restart/race/queue/WS tests |
| `test/fixtures/*` | shared protocol and canary fixtures |
| `Dockerfile`, `.dockerignore` | pinned, non-root production image |

## Android workspace

RN template files are generated once at the approved RN 0.86 patch, then reviewed. Exact app-owned files:

| File | Planned content |
|---|---|
| `apps/android/package.json`, `tsconfig.json`, `babel.config.js`, `metro.config.js`, `jest.config.js` | RN workspace/tooling |
| `apps/android/index.js`, `src/App.tsx` | bootstrap and root lock/navigation |
| `src/navigation/RootNavigator.tsx` | computer-first stacks |
| `src/features/lock/*` | lock/step-up flow |
| `src/features/computers/*` | computer list/detail/security |
| `src/features/pairing/*` | scan/manual/link/phrase flow |
| `src/features/sessions/*` | catalog, activation, create flow |
| `src/features/session/*` | transcript/activity/composer/requests |
| `src/features/attachments/*` | picker/hash/progress/download |
| `src/features/settings/*` | lifecycle, retention display, diagnostics |
| `src/state/*` | keyed nanostores and pure projections |
| `src/protocol/*` | transport coordinator and protocol package adapters |
| `src/native/NativeHermesIdentity.ts` | TurboModule spec |
| `src/native/NativeHermesSecureTransport.ts` | TurboModule spec |
| `src/native/NativeHermesPairing.ts` | TurboModule spec |
| `src/native/NativeHermesLifecycleSecurity.ts` | TurboModule spec |
| `src/**/*.test.ts(x)` | reducers, controllers, UI and security copy |
| `e2e/*.e2e.ts` | pairing/session/approval/reconnect/lifecycle |
| `android/app/src/main/AndroidManifest.xml` | API/components/backup/cleartext/app link policy |
| `android/app/src/main/res/xml/network_security_config.xml` | system CA/no-cleartext policy |
| `android/app/src/main/res/xml/backup_rules.xml`, `data_extraction_rules.xml` | exclude all app state |
| `android/app/src/main/java/.../identity/*` | Keystore/Biometric TurboModule |
| `android/app/src/main/java/.../transport/*` | pinned direct WSS TurboModule |
| `android/app/src/main/java/.../pairing/*` | scanner/parser/App Link TurboModule |
| `android/app/src/main/java/.../lifecycle/*` | secure-window/lock signals |
| `android/app/src/test/java/.../*Test.kt` | Kotlin parser/key/policy unit tests |
| `android/app/src/androidTest/java/.../*Test.kt` | Keystore/biometric/manifest/device tests |
| `android/gradle/verification-metadata.xml` | Gradle supply-chain verification |
| `detox.config.js` | emulator E2E configuration |

Template-owned `android/build.gradle`, `android/settings.gradle`, `android/gradle.properties`, `android/gradle/wrapper/gradle-wrapper.properties`, and `android/app/build.gradle` are accepted from RN scaffold and changed only for app ID, min API, dependencies, release signing inputs, verification, and New Architecture—not wholesale rewritten.

## Deployment and documentation

| File | Planned content |
|---|---|
| `deploy/remote-control/compose.yaml` | relay/PostgreSQL local/self-host reference |
| `deploy/remote-control/.env.example` | names and safe placeholders, no values |
| `deploy/remote-control/README.md` | TLS/secrets/backup/start/upgrade |
| `deploy/remote-control/azure/main.bicep` and modules | one-replica Container Apps/PostgreSQL/Blob/monitor reference |
| `deploy/remote-control/azure/parameters.example.json` | non-secret parameters |
| `deploy/remote-control/azure/README.md` | cost/security/network/teardown |
| `docs/remote-control/*` | Update normative plan/protocol/security/traceability as implementation evidence accrues |

No existing `gateway/relay/*` or `tests/gateway/relay/*` production contract is modified for remote control. If a reusable primitive is later extracted, it must be a behavior-preserving standalone commit with both old and new callers tested.
