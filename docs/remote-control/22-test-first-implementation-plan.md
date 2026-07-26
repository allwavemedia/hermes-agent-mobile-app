# Test-First Implementation Plan

This plan begins only after Gate 1 approval. It contains 28 independently reviewable tasks in nine milestones. Each task follows red → minimal implementation → green → review → atomic commit. Do not combine tasks to hide a failing invariant.

Command assumptions: repository root; Python 3.11/3.13 via `uv`; Node 22; PostgreSQL test service available where stated; Linux/macOS use `./gradlew`, Windows uses `gradlew.bat`. A red step must fail for the named missing behavior—not syntax, missing tool, or unrelated baseline failure. Record the failing and passing output in the PR.

## Milestone 1 — Protocol narrow waist

### Task 1 — Canonical v1 schema and cross-runtime validation

Files: `apps/remote-control-protocol/{package.json,tsconfig.json}`, `src/{index,types,validate,version}.ts`, `src/validate.test.ts`, `scripts/copy-schemas.mjs`, `fixtures/v1/*.json`, `docs/remote-control/schemas/v1/{envelope,snapshot,event,capability,command,pairing}.schema.json`, `tests/remote_control/test_protocol_schema.py`, `remote_control/{__init__,models,protocol}.py`, `package-lock.json`.

1. Add valid/invalid fixture tests in TS and Python; run `npm test --workspace apps/remote-control-protocol -- --run src/validate.test.ts` and `uv run --extra remote-control pytest -q tests/remote_control/test_protocol_schema.py`. Expected red: package/module/validator absent and fixtures cannot validate.
2. Add schemas, minimal types/validators, and schema-byte-identity check.
3. Rerun both commands. Expected green: identical accept/reject result for every fixture, zero failures.
4. Run `npm run check --workspace apps/remote-control-protocol && uv run ruff check remote_control tests/remote_control`.
5. Commit `feat(remote-protocol): define validated v1 contract`.

### Task 2 — Ordered reducer, replay, and compatibility

Files: `apps/remote-control-protocol/src/{reducer,compatibility}.ts`, `src/{reducer,compatibility}.test.ts`.

1. Write fast-check properties for duplicate idempotence, gap rejection, epoch reset, and highest-common-minor negotiation. Run `npm test --workspace apps/remote-control-protocol -- --run src/reducer.test.ts src/compatibility.test.ts`. Expected red: missing reducer/negotiator.
2. Implement pure reducer and compatibility rules.
3. Rerun with `--runInBand` if supported by selected runner. Expected green: at least 1,000 generated cases/property, no counterexample.
4. Commit `feat(remote-protocol): add deterministic replay reducer`.

### Task 3 — Canonical signatures, capabilities, and risk policy

Files: `apps/remote-control-protocol/src/{canonicalize,risk}.ts`, `src/{canonicalize,risk}.test.ts`, `remote_control/{protocol,authorization}.py`, `tests/remote_control/test_protocol_signatures.py`.

1. Add shared signature vectors plus unknown-critical, cross-target, expired, wrong-algorithm, stale-capability, and offline-policy tests. Run TS and Python tests; expected red: signature vectors/policy unsupported.
2. Implement portable JCS bytes plus an asynchronous crypto-provider boundary, capability hash, and queue/step-up taxonomy. Verify the Node test adapter with `jose`, use existing Python crypto/JWT libraries on the host, and implement the same provider later through the focused Kotlin native module; do not import `node:crypto` into the shared package or assume React Native WebCrypto.
3. Expected green: both runtimes verify the same vectors and reject every mutation.
4. Commit `feat(remote-protocol): bind signed capabilities and risk`.

## Milestone 2 — Safe multi-client gateway adapter

### Task 4 — Nonblocking session listener hub

Files: `tui_gateway/transport.py`, `tui_gateway/server.py`, `tests/tui_gateway/test_remote_event_hub.py`.

1. Test local transport identity, two subscribers, subscriber exception, queue overflow, and exact local event order. Run `uv run pytest -q tests/tui_gateway/test_remote_event_hub.py`; expected red: no listener API.
2. Implement bounded listener hub and publish copies after existing transport write.
3. Expected green: local transport receives all fixtures unchanged; slow listener gets gap/reset signal; agent path never awaits it.
4. Run `uv run pytest -q tests/tui_gateway/test_reasoning_session_scope.py tests/tui_gateway/test_remote_event_hub.py`.
5. Commit `feat(tui-gateway): add isolated session event listeners`.

### Task 5 — Stable snapshot/event adapter

Files: `remote_control/adapter.py`, `remote_control/models.py`, `tui_gateway/server.py`, `tests/tui_gateway/test_remote_adapter.py`, `tests/tui_gateway/test_remote_event_normalization.py`.

1. Add snapshot and internal-event normalization fixtures, allowlisted command mapping, and generic-RPC denial tests. Expected red from `uv run pytest -q tests/tui_gateway/test_remote_adapter.py tests/tui_gateway/test_remote_event_normalization.py`.
2. Implement `GatewaySessionAdapter` methods and explicit mappings.
3. Expected green: snapshots redact forbidden fields; all known fixture events normalize; unknown critical events fail closed; raw method names cannot be invoked.
4. Commit `feat(remote-host): add stable gateway session adapter`.

### Task 6 — Simultaneous Desktop/TUI and remote clients

Files: `tests/tui_gateway/test_remote_multi_client.py`, `tui_gateway/entry.py`, `remote_control/adapter.py`.

1. Simulate one local transport, two remote subscribers, local and remote prompts, local approval winning a race, disconnect/reconnect. Expected red from `uv run pytest -q tests/tui_gateway/test_remote_multi_client.py`.
2. Wire adapter lifecycle without assigning `session["transport"]`.
3. Expected green: local transport object identity never changes; both subscribers converge; stale remote approval rejects.
4. Run full focused suite: `uv run pytest -q tests/tui_gateway/test_remote_*.py`.
5. Commit `feat(remote-host): preserve local ownership with concurrent clients`.

## Milestone 3 — Pairing, identity, and authorization

### Task 7 — Native host secure storage

Files: `pyproject.toml`, `uv.lock`, `remote_control/{secure_store,identity,errors}.py`, `tests/remote_control/test_secure_store.py`.

1. Add fake native, plaintext, null, third-party, unavailable, rotation, and no-secret-log cases. Expected red from `uv run pytest -q tests/remote_control/test_secure_store.py`.
2. Add `keyring>=25.7,<26`, native backend allowlist, P-256 key lifecycle, fail-closed errors.
3. Expected green: only Windows Credential Locker/macOS Keychain fakes succeed; private key never appears in DB/log.
4. Commit `feat(remote-host): store identity in native keychains`.

### Task 8 — One-time pairing transcript

Files: `remote_control/pairing.py`, `tests/remote_control/test_pairing.py`, shared pairing fixtures in `apps/remote-control-protocol/fixtures/v1/`.

1. Test two-minute expiry, 256-bit capability, atomic two-claim race, key substitution, nonce replay, phrase mismatch, direct/relay transcript equality. Expected red.
2. Implement deterministic state machine and proof verification.
3. Expected green including race test with exactly one accepted claim.
4. Commit `feat(remote-host): prove one-time computer pairing`.

### Task 9 — Connection challenge and revocation

Files: `remote_control/{credentials,identity}.py`, `tests/remote_control/test_credentials.py`.

1. Test five-minute audience/connection-bound credential, fresh nonce, JTI replay, trust-epoch race, single/all-device revocation. Expected red.
2. Implement verifier/credential model and write-before-ack revocation.
3. Expected green: revoked connection closes and no renewal/old envelope succeeds.
4. Commit `feat(remote-host): enforce short-lived paired credentials`.

### Task 10 — Approval/action binding

Files: `remote_control/authorization.py`, `tests/remote_control/test_authorization.py`.

1. Parameterize computer/device/session/run/tool/action/display/revision/capability/expiry mutations and permanent-allow denial. Expected red.
2. Implement exact digest recomputation and existing-handler decision mapping.
3. Expected green: only unchanged, pending, unexpired `approve_once`/`deny` passes.
4. Commit `feat(remote-host): bind remote decisions to exact actions`.

## Milestone 4 — Host broker vertical slices

### Task 11 — Host DB, replay journal, idempotency

Files: `remote_control/{storage,replay,idempotency}.py`, `remote_control/migrations/001_initial.sql`, `tests/remote_control/{test_storage,test_replay,test_idempotency}.py`.

1. Add migration, WAL/fallback, 15-minute/10-MiB eviction, duplicate/gap/reset, crash-transaction and payload-conflict tests. Expected red.
2. Implement separate SQLite store and deterministic receipts.
3. Expected green; `uv run pytest -q tests/remote_control/test_storage.py tests/remote_control/test_replay.py tests/remote_control/test_idempotency.py`.
4. Commit `feat(remote-host): persist bounded replay and receipts`.

### Task 12 — Authenticated cross-platform local IPC

Files: `remote_control/{ipc,registry}.py`, `tui_gateway/entry.py`, `tests/remote_control/{test_ipc,test_registry}.py`.

1. Test unauthorized OS user/credential, malformed/oversized frame, PID/start-time mismatch/reuse, broker restart and backpressure. Platform-mark Windows AF_PIPE and macOS AF_UNIX cases. Expected red.
2. Implement framed authenticated IPC and `psutil` registration.
3. Expected green locally for platform-neutral cases and on Windows/macOS CI for platform cases; no `os.kill(pid, 0)`.
4. Commit `feat(remote-host): register sessions over authenticated local IPC`.

### Task 13 — Broker lifecycle and relay transport

Files: `remote_control/{config,relay_transport,audit,broker}.py`, `gateway/{config,run}.py`, `tests/remote_control/{test_relay_transport,test_broker_integration,test_log_redaction}.py`, `tests/gateway/{test_remote_control_config,test_remote_control_lifecycle}.py`.

1. Test default-disabled startup, outbound-only WSS, jitter/reconnect, registration, explicit/auto enable, redaction, clean shutdown, and broker failure isolation. Expected red.
2. Implement optional broker composition and relay transport.
3. Expected green; existing messaging relay tests remain green: `uv run pytest -q tests/gateway/relay tests/gateway/test_remote_control_*.py tests/remote_control/test_broker_integration.py`.
4. Commit `feat(remote-host): run optional outbound control broker`.

### Task 14 — Direct transport parity

Files: `remote_control/direct_transport.py`, `tests/remote_control/test_direct_parity.py`.

1. Run the same authorization/replay corpus through fake relay and direct paths; add cleartext, public-bind, wrong-pin, user-CA, and downgrade tests. Expected red.
2. Implement explicit private-interface WSS listener and signed challenge.
3. Expected green: decisions/receipts byte-equivalent; unsafe bind/pin fails closed.
4. Commit `feat(remote-host): add pinned direct fallback parity`.

## Milestone 5 — Provider-neutral relay

### Task 15 — Relay auth, pairing, and revocation

Files: `apps/remote-control-relay/{package.json,tsconfig.json}`, `src/{main,config,http,auth,pairing,revocation,errors}.ts`, `migrations/001_initial.sql`, matching `src/*.test.ts`, `package-lock.json`.

1. Add PostgreSQL-backed offer race, challenge, credential, trust-epoch, rate-limit and close tests. `npm test --workspace apps/remote-control-relay`; expected red.
2. Implement routes/transactions with DB time.
3. Expected green and zero open handles.
4. Commit `feat(remote-relay): authenticate paired routes`.

### Task 16 — Queue encryption, expiry, and zero retention

Files: relay `src/{crypto,queue,storage,postgres,audit}.ts`, matching tests and integration fixtures.

1. Test AES-GCM vectors/AAD mutation, nonce uniqueness, wrapped-key rotation, allowed-type matrix, quota/TTL, restart, zero-retention no-write and log canaries. Expected red.
2. Implement crypto/repository/queue.
3. Expected green: database/blob spies observe zero content writes in zero-retention corpus.
4. Commit `feat(remote-relay): encrypt and expire selective queues`.

### Task 17 — WebSocket routing, replay, and backpressure

Files: relay `src/{websocket,routes,metrics}.ts`, `test/integration/{routing,reconnect,backpressure}.test.ts`.

1. Test host/device matching, multiple devices/sessions, cumulative ack/replay, slow consumer reset, graceful restart and revoked close. Expected red.
2. Implement single-process connection directory and bounded prioritized buffers.
3. Expected green with no silent sequence gaps.
4. Commit `feat(remote-relay): route replayable multiplexed sessions`.

### Task 18 — Relay attachments and Compose operational slice

Files: relay `src/attachments.ts`, attachment tests, `Dockerfile`, `.dockerignore`, `deploy/remote-control/{compose.yaml,.env.example,README.md}`.

1. Add grant/range/hash/quota/expiry/orphan/zero-retention tests and `docker compose config` assertion. Expected red.
2. Implement storage adapter, non-root image and Compose reference.
3. Expected green: `npm test --workspace apps/remote-control-relay`; `docker compose -f deploy/remote-control/compose.yaml config --quiet`; integration smoke uploads canary, consumes, expires, and confirms deletion.
4. Commit `feat(remote-relay): stage verified temporary attachments`.

## Milestone 6 — Desktop and CLI control plane

### Task 19 — CLI/service control

Files: `hermes_cli/{main,gateway,gateway_windows}.py`, `hermes_cli/subcommands/gateway.py`, `tests/cli/{test_remote_control_cli,test_remote_control_service_status}.py`.

1. Add exact parse/output tests for status, pair, devices, revoke, session enable/disable, retention/auto-enable/direct settings; assert no key material. Expected red.
2. Implement structured broker client commands while reusing service lifecycle.
3. Expected green on Windows and macOS CI; existing gateway lifecycle tests pass.
4. Commit `feat(cli): manage paired remote control`.

### Task 20 — Desktop pairing/settings/session activation

Files: the Desktop files enumerated in [file plan](21-file-by-file-change-plan.md#desktop-integration).

1. Add Electron IPC allowlist and React tests for QR countdown, device revoke, retention, auto-enable, direct warning, enable/disable and no renderer secret. `npm test --workspace apps/desktop -- --run remote-control session-actions-menu`; expected red.
2. Implement main/preload DTO API, feature store, settings and session indicators.
3. Expected green plus `npm run check --workspace apps/desktop`.
4. Commit `feat(desktop): control remote pairing and session access`.

## Milestone 7 — Android secure foundation

### Task 21 — RN scaffold and manifest policy

Files: RN template/tooling and manifest/resource files enumerated in the file plan, `src/App.tsx`, `src/navigation/RootNavigator.tsx`, manifest policy tests.

1. Generate tests first in an isolated temp scaffold patch: API 24, New Architecture, only pairing activity exported, no cleartext/backup/notification/camera permission, release user-CA denial. Expected red against unmodified template.
2. Apply reviewed RN 0.86 template and minimal secure config; add no product screen beyond lock/computer empty state.
3. Expected green: `npm run test --workspace apps/android`; `cd apps/android/android && ./gradlew lintRelease testDebugUnitTest`; manifest inspection passes.
4. Commit `build(android): establish secure new-architecture app`.

### Task 22 — Keystore, biometric, and lifecycle modules

Files: `src/native/{NativeHermesIdentity,NativeHermesLifecycleSecurity}.ts`, Kotlin `identity/*`, `lifecycle/*`, Kotlin unit/instrumentation tests, `src/features/lock/*`.

1. Add tests for non-exportable key, JWK/thumbprint, biometric-bound exact digest, cancel/failure, lock/background, `FLAG_SECURE`, key deletion. Expected red.
2. Implement two focused TurboModules and lock UI.
3. Expected green on emulator; physical device evidence required for hardware/biometric characteristics.
4. Commit `feat(android): bind identity to keystore and biometrics`.

### Task 23 — Secure pairing module and flow

Files: `src/native/NativeHermesPairing.ts`, Kotlin `pairing/*`, `src/features/pairing/*`, TS/Kotlin/Detox tests.

1. Add QR/link fuzz corpus, origin/version/length/duplicate-field rejection, no-GMS manual fallback, expiry/phrase UI tests. Expected red.
2. Implement Google Code Scanner bridge, strict parser, verified App Link and flow.
3. Expected green: unit tests and `npx detox test --configuration android.emu.debug e2e/pairing.e2e.ts`.
4. Commit `feat(android): pair computers with verified proofs`.

## Milestone 8 — Android synchronized workflows

### Task 24 — Relay/direct transport and session convergence

Files: `src/native/NativeHermesSecureTransport.ts`, Kotlin `transport/*`, `src/{protocol,state}/*`, `src/features/{computers,sessions}/*`, tests.

1. Add wrong-pin/MITM/direct-parity tests and reducer reconnect/process-death/multi-computer tests. Expected red.
2. Implement transport coordinator, cursor persistence and computer/session catalog.
3. Expected green: relay and pinned direct fake produce same state; cleartext/pin errors terminal.
4. Commit `feat(android): synchronize paired session projections`.

### Task 25 — Conversation, tool activity, requests, and control

Files: `src/features/session/*`, `src/features/settings/*`, UI/controller tests and `e2e/session.e2e.ts`, `e2e/approval.e2e.ts`.

1. Add snapshot/stream, local-surface event, stale approval, clarification-won-elsewhere, interrupt/run mismatch, biometric display-digest and accessibility tests. Expected red.
2. Implement capability-driven screens and signed controllers.
3. Expected green with Detox end-to-end against fake host and real Hermes smoke.
4. Commit `feat(android): remotely control capability-bound sessions`.

### Task 26 — Attachment and lifecycle completion

Files: `src/features/attachments/*`, lifecycle/settings additions, `e2e/{attachments,lifecycle,reconnect}.e2e.ts`.

1. Add content URI/hash/cancel/expiry/zero-retention/process-death, app-switcher, background lock, in-app foreground notification tests. Expected red.
2. Implement bounded transfer and lifecycle UX; no FCM/background service.
3. Expected green across API 24/current emulators and physical-device smoke.
4. Commit `feat(android): secure attachments and lifecycle`.

## Milestone 9 — Operations, release, and final proof

### Task 27 — Azure reference, CI, observability, and migration rehearsal

Files: `deploy/remote-control/azure/{main.bicep,parameters.example.json,README.md}` plus modules, workflows `android-remote.yml`, `remote-relay.yml`, audit/metrics tests, migration runbooks.

1. Add `az bicep build`, `docker compose config`, workflow policy, redaction canary, backup/restore and migration/rollback test scripts; expected red because reference/workflows are absent.
2. Implement provider reference and blocking CI without creating Azure resources.
3. Expected green: Bicep compiles, Compose validates, CI dry checks find no unpinned action/release-secret exposure, restore rehearsal passes locally.
4. Commit `ops(remote-control): validate portable relay operations`.

### Task 28 — Signed release pipeline and acceptance closure

Files: `.github/workflows/android-remote-release.yml`, signer-digest file created only after approved key generation, release scripts/tests, updated `docs/remote-control/{18-release-signing,23-acceptance-traceability-matrix,24-security-review-findings,25-gate-0-gate-1-report}.md`.

1. Add workflow policy tests that reject PR secret access, unprotected tags, debug signer, missing checksum/SBOM/provenance, lower versionCode, and failed platform/security evidence. Expected red.
2. After separate explicit approval, generate/provision signing material outside repository, implement protected release workflow, run full acceptance matrix.
3. Expected green: `apksigner verify --verbose --print-certs` matches reviewed digest; API 24/current install/upgrade works; all traceability rows link passing evidence; no unresolved critical/high finding.
4. Commit `release(android): prove signed remote-control apk`.

## Final Gate 2 verification

Run from clean clone/worktrees:

```text
uv sync --frozen
uv run pytest -q tests/tui_gateway/test_remote_*.py tests/remote_control tests/gateway/test_remote_control_*.py tests/cli/test_remote_control_*.py
npm ci
npm run check --workspace apps/remote-control-protocol
npm test --workspace apps/remote-control-protocol
npm run check --workspace apps/remote-control-relay
npm test --workspace apps/remote-control-relay
npm run check --workspace apps/desktop
npm test --workspace apps/desktop
npm run check --workspace apps/android
npm run test --workspace apps/android
docker compose -f deploy/remote-control/compose.yaml config --quiet
cd apps/android/android && ./gradlew lintRelease testDebugUnitTest connectedDebugAndroidTest assembleRelease
```

Expected: every command exits 0; release assembly is unsigned unless the protected release environment is active; `git status --short` shows only deliberate generated evidence or is clean. Then perform Windows/macOS/physical Android/direct-network/restore/load/security manual gates and attach evidence. Stop rather than release on any hard invariant failure.
