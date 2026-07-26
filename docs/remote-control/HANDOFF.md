# Hermes Android Remote Control — Development Handoff

Last refreshed: 2026-07-26 13:24 EDT

Refresh owner: the active implementation agent

Status: Milestone 2 / Task 5 complete, independently reviewed, and published; Task 6 has not started

This is the canonical restart document for the implementation phase. It is intentionally operational and must describe the repository as it exists, not as the plan expects it to exist.

## Mandatory refresh policy

Update this file:

1. before ending any development session;
2. after every red/green/refactor cycle that changes the next command;
3. after every commit, push, branch/worktree change, or PR change;
4. when a decision is accepted, rejected, or newly blocks work;
5. when environment/tooling readiness changes;
6. at least once per completed implementation task.

Never copy secrets, credentials, private keys, pairing capabilities, cloud subscription identifiers, or signing material into this file. Replace stale status instead of appending an unbounded diary. Keep the latest verification evidence and a short completed-commit list.

## Repository state

| Item | Current value |
|---|---|
| Fork | `https://github.com/allwavemedia/hermes-agent-mobile-app.git` |
| Upstream | `https://github.com/NousResearch/hermes-agent.git` |
| Implementation worktree | `A:\Hermes Mobile App\hermes-remote-control-implementation` |
| Implementation branch | `feat/remote-control-protocol-v1` |
| Implementation HEAD | Run `git rev-parse HEAD`; this self-updating file intentionally does not hardcode its own commit |
| Published Task 5 implementation | `464351924a2ad71f95cf28ffa43872fd8e734fcf` |
| Stacked base branch | `plan/hermes-android-remote-control` |
| Stacked base commit | `28e1bb59dfee7c54340fbc0798e1dba69516b708` |
| Upstream baseline | `21a2185f86f64be10d28bec1ecc576d89230f761` |
| Planning worktree | `A:\Hermes Mobile App\hermes-android-remote-control-plan` |
| Planning draft PR | `https://github.com/allwavemedia/hermes-agent-mobile-app/pull/1` |
| Implementation draft PR | `https://github.com/allwavemedia/hermes-agent-mobile-app/pull/2` — OPEN / DRAFT / CLEAN; head `464351924`, base `plan/hermes-android-remote-control`; `feat(remote-control): establish secure protocol and gateway adapter` |

The implementation branch is intentionally stacked on the documentation branch until the planning PR is merged. Do not rebase it onto `main` without first checking the PR/base state and preserving the handoff.

## Scope and authority

The user explicitly authorized development after the planning stop gate. Begin with reversible foundation slices. Do not create cloud resources, public endpoints, signing keys, or a public release without separate explicit approval. Do not claim E2EE; the proposed MVP relay is content-trusted.

Next slice: [Milestone 2, Task 6](22-test-first-implementation-plan.md#task-6--simultaneous-desktoptui-and-remote-clients), simultaneous Desktop/TUI and remote clients. No Task 6 implementation or RED test has started.

Durable implementation constraints accepted during critical review:

- Add `jsonschema==4.26.0` as a direct dependency of a dedicated `remote-control` extra because production Python code imports it; do not rely on its incidental presence in the development-only MCP stack or enlarge the default core install.
- Make initial red tests fail by assertion on missing/unsupported behavior, not by test-runner configuration or uncaught import errors.
- Canonical schemas already exist under `docs/remote-control/schemas/v1/`; implementation consumes and validates those bytes rather than recreating them.

These corrections do not change protocol semantics.

Task 5 security boundary accepted during parallel preflight:

- Build fresh allowlisted remote projections; schema validation is defense in depth, not a redaction boundary.
- Never expose raw JSON-RPC, raw gateway/session dictionaries, raw exceptions, secrets, absolute paths, provider details, tool arguments/results/diffs, terminal content, or attachment bytes/paths.
- Never replace or rebind `session["transport"]`; consume only Task 4 listener copies after the local write.
- Unknown noncritical internal events are dropped without a v1 event or sequence increment. Unknown critical or sensitive-unmappable events fail closed without a sequence increment.
- Task 5 may route only `prompt.submit`, `session.steer`, and `session.interrupt`, using a constant allowlist and freshly constructed parameters. It must expose no caller-selected method or generic dispatch surface.
- `approval.respond`, `clarify.respond`, unconstrained `session.create`, and terminal controls remain denied/unadvertised until their dedicated binding, spawn-policy, and terminal-policy tasks. Do not alias `interrupt.request`.

## Required reading on restart

Read completely, in order:

1. root `AGENTS.md`;
2. this file;
3. `docs/remote-control/README.md`;
4. `docs/remote-control/22-test-first-implementation-plan.md`;
5. the Task 5 parallel-analysis artifacts listed below, when the existing worktree is available;
6. the relevant Android/engineering `SKILL.md` files for the next task.

For Android work, use the installed official skills at `C:\Users\ldoby\.codex\skills\`, especially `android-cli`, `testing-setup`, and `android-intent-security` when their trigger conditions apply. The CLI executable is `C:\ProgramData\AndroidCLI\android.exe` if the current process has a stale `PATH`.

## Work completed

- Gate 0/Gate 1 planning package: 46 documentation artifacts, eight ADRs, six v1 schemas, 28 test-first tasks.
- Planning branch pushed and documentation-only draft PR #1 opened.
- Official Android skills installed for Codex.
- Isolated implementation worktree and branch created from planning commit `28e1bb59d`.
- Implementation branch pushed and stacked draft PR #2 opened against `plan/hermes-android-remote-control`.

- `abf106e07bd734cddee23226bd6c2832c8a93488` — `feat(remote-protocol): define validated v1 contract`
- `b651ed53f9320807419a54b82f8d7fee25ffb5b6` — `feat(remote-protocol): add deterministic replay reducer`
- `daca7c231` — `feat(remote-protocol): bind signed capabilities and risk`
- `b82922970` — `feat(tui-gateway): add isolated session event listeners`
- `2fbd04c8d` — `docs(remote-control): record gateway task 4 publish`
- `464351924a2ad71f95cf28ffa43872fd8e734fcf` — `feat(remote-host): add stable gateway session adapter`

Task 1 delivered 13 shared literal validation fixtures, validators/types in both runtimes, a direct pinned Python `remote-control` extra, and a build-time schema copy/byte-identity gate. Pairing public JWKs reject private key material.

Task 2 delivered immutable ordered replay results, duplicate/gap/conflict/epoch-reset handling, a 4,096-entry identity cap, and fail-closed highest-common-minor negotiation. Seven properties run 1,000 generated cases each.

Task 3 dependency decision: use `canonicalize@3.0.0` (npm, RFC 8785 Appendix G implementation) and Trail of Bits `rfc8785==0.1.4` (Python, no transitive dependencies) instead of writing security-sensitive JCS serialization. The shared TypeScript package must not import Node crypto or assume React Native WebCrypto: it defines an asynchronous crypto-provider boundary. `jose@6.2.4` is dev-only here for shared-vector tests and will be runtime-owned by the relay adapter; Android implements the provider with the focused Kotlin native module. Python uses existing pinned `cryptography`/PyJWT libraries.

Task 3 delivered shared RFC 8785/ES256 vectors, canonical hashes, strict protected algorithm/type and public-key checks, exact computer/device/session target binding, expiry/future-clock rejection, capability-stale rejection, low-risk-only offline prompt queueing, foreground/unlock/biometric step-up policy, and fail-closed unknown-message handling in both runtimes. Runtime crypto adapter failures cannot authorize.

Task 4 delivered a bounded asynchronous listener queue per `(sessionId, subscriberId)`, independent deep-copied deliveries, exception isolation, one reset-required signal on overflow, and server publication only after the unchanged local transport write. A listener never replaces `session["transport"]` or runs inline on the agent path.

Task 5 preflight used three parallel read-only subagents, followed by one implementation owner. The source, security, and test-design reports are nonbinding research artifacts; the reconciled brief is authoritative:

- `.superpowers/sdd/22-test-first-implementation-plan/task-5-gateway-analysis.md`
- `.superpowers/sdd/22-test-first-implementation-plan/task-5-security-analysis.md`
- `.superpowers/sdd/22-test-first-implementation-plan/task-5-test-analysis.md`
- `.superpowers/sdd/22-test-first-implementation-plan/task-5-brief.md`
- `.superpowers/sdd/22-test-first-implementation-plan/progress.md`

Task 5 delivered a typed stable adapter context, schema-valid allowlisted snapshots/capabilities/events, fixed command routing for only `prompt.submit`, `session.steer`, and `session.interrupt`, content-free fail-closed outcomes, bounded force-redacted text with absolute-path removal, and a server seam that neutralizes ambient transport before invoking one fixed handler. Raw RPC, unadvertised commands, offline queueing, terminal output, provider/error detail, tool arguments/results/diffs, subagent files/output tails, and attachment content remain unavailable. The adapter consumes one shared Task 4 listener copy stream, normalizes each event once before isolated fan-out, preserves strict source criticality, and never assigns `session["transport"]`.

The implementation owner created both required test files before production adapter code. The first exact focused command reached intentional RED with 51 behavioral assertion failures because `GatewaySessionAdapter` was not yet exported; collection and environment setup succeeded. Follow-up source-shape and redaction tests were also observed failing before the corresponding changes.

Independent review fix round 1 reproduced four blocking findings before production changes: `/tmp` path leakage, duplicate per-subscriber normalization/identity, snapshot/subscription cursor races, and lost critical metadata on the real subscription path. The final design uses one persistent bounded upstream listener, one sequence-locked snapshot boundary, and atomic cursor validation plus sink registration. A Task 4 reset invalidates the closed upstream handle so a fresh post-snapshot listener can be established.

All four Important findings were fixed in round 1, and the scoped independent re-review passed. One Minor cursor-boundary duplicate-delivery/test weakness is explicitly deferred to Task 6, where the complete simultaneous-client lifecycle and replay boundary belong. Task 5 commit `464351924a2ad71f95cf28ffa43872fd8e734fcf` is published on `origin/feat/remote-control-protocol-v1`; draft PR #2 is open, draft, and clean at that head.

## Current work and next exact steps

Task 5 is complete, reviewed, and published. Task 6 is the next work item; no Task 6 implementation, test, or preflight artifact has started.

1. Read the Task 6 section of `docs/remote-control/22-test-first-implementation-plan.md` and the current Task 5 adapter/listener contracts.
2. Reconcile the deferred Minor cursor-boundary duplicate-delivery/test weakness into the Task 6 test-first brief.
3. Start Task 6 with its required intentional RED behavior tests before production changes.
4. Preserve the published Task 5 commit and current draft PR state until the next explicitly authorized publish checkpoint.

## Latest verification evidence

| Time | Command | Result |
|---|---|---|
| 2026-07-26 13:24 EDT | Task 5 publication and PR verification | `origin/feat/remote-control-protocol-v1` at reviewed implementation `464351924`; draft PR #2 OPEN / DRAFT / CLEAN with base `plan/hermes-android-remote-control` |
| 2026-07-26 13:24 EDT | Scoped independent re-review | PASS: all four Important findings fixed in round 1; one Minor cursor-boundary duplicate-delivery/test weakness deferred to Task 6 |
| 2026-07-26 13:14 EDT | `uv run pytest -q tests/tui_gateway/test_remote_adapter.py tests/tui_gateway/test_remote_event_normalization.py` | Fix round 1 final GREEN: 60 passed |
| 2026-07-26 13:14 EDT | Exact focused fix-round command before production changes | Intended RED: 6 failed / 54 passed for the four independent-review findings; reset lifecycle follow-up intentionally RED at 1 failed / 59 passed |
| 2026-07-26 13:14 EDT | `uv run pytest -q tests/tui_gateway/test_protocol.py tests/tui_gateway/test_remote_event_hub.py tests/gateway/test_tui_approval_redaction.py tests/remote_control/test_protocol_schema.py` | Exact broader regression GREEN: 119 passed |
| 2026-07-26 13:14 EDT | Repository Ruff and scoped Task 5 ty commands | GREEN: all checks passed |
| 2026-07-26 13:14 EDT | `git diff --check` | GREEN; only expected Windows LF-to-CRLF checkout notices |
| 2026-07-26 12:51 EDT | `uv run pytest -q tests/tui_gateway/test_remote_adapter.py tests/tui_gateway/test_remote_event_normalization.py` | Final Task 5 GREEN: 55 passed |
| 2026-07-26 12:50 EDT | `uv run pytest -q tests/tui_gateway/test_protocol.py tests/tui_gateway/test_remote_event_hub.py tests/gateway/test_tui_approval_redaction.py tests/remote_control/test_protocol_schema.py` | Exact broader regression GREEN: 119 passed |
| 2026-07-26 12:50 EDT | `uv run --frozen --extra dev --extra remote-control ruff check .` | GREEN: repository Ruff check passed |
| 2026-07-26 12:50 EDT | `uv run --frozen --extra dev --extra remote-control ty check remote_control/adapter.py remote_control/models.py remote_control/__init__.py tests/tui_gateway/test_remote_adapter.py tests/tui_gateway/test_remote_event_normalization.py` | GREEN: Task 5 adapter/model/export/tests ty check passed |
| 2026-07-26 12:50 EDT | `git diff --check` | GREEN; only expected Windows LF-to-CRLF checkout notices |
| 2026-07-26 12:45 EDT | Exact focused Task 5 command after current gateway producer-shape fixtures | Intended RED: 5 behavioral failures for missing tool-generating, project, subagent, and offline-queue behavior; subsequent GREEN 52 passed |
| 2026-07-26 12:48 EDT | Exact focused Task 5 command after content-free error and absolute-path fixtures | Intended RED then GREEN: three error/path failures, then one UNC-path failure; final focused suite 55 passed |
| 2026-07-26 12:37 EDT | `uv run pytest -q tests/tui_gateway/test_remote_adapter.py tests/tui_gateway/test_remote_event_normalization.py` | Intended Task 5 RED: 51 behavioral assertion failures because `GatewaySessionAdapter` is not exported; both requested files collected and the environment initialized successfully |
| 2026-07-26 04:27 EDT | `npm test --workspace apps/remote-control-protocol -- --run src/validate.test.ts` | Intended RED: 1 file, 12 failed assertions because the TypeScript validator does not exist |
| 2026-07-26 04:27 EDT | `uv run --frozen --extra dev pytest -q tests/remote_control/test_protocol_schema.py` | Intended RED: 12 failed assertions because the Python validator does not exist |
| 2026-07-26 04:32 EDT | `npm test --workspace apps/remote-control-protocol -- --run src/validate.test.ts` | GREEN: 1 file, 12 passed |
| 2026-07-26 04:32 EDT | `uv run --frozen --extra dev pytest -q tests/remote_control/test_protocol_schema.py` | Provisional GREEN: 12 passed; repository wrapper still required |
| 2026-07-26 04:36 EDT | `npm run check --workspace apps/remote-control-protocol` | GREEN: typecheck, lint, 12 tests, six-schema byte-identical build copy |
| 2026-07-26 04:37 EDT | `scripts/run_tests.sh ... test_protocol_schema.py tests/test_project_metadata.py -q` via Git Bash and Windows venv | GREEN exit 0: 21 passed; progress callback emitted a non-fatal cp1252 Unicode traceback |
| 2026-07-26 04:40 EDT | TypeScript and Python focused tests with private JWK fixture | Intended RED: 1 of 13 failed because private `d` was accepted |
| 2026-07-26 04:41 EDT | Same focused tests after canonical pairing schema hardening | GREEN: 13 passed in each runtime |
| 2026-07-26 04:41 EDT | `uvx pip-audit --local --skip-editable --progress-spinner off` | No known Python vulnerabilities |
| 2026-07-26 04:41 EDT | `npm audit --workspace apps/remote-control-protocol --omit=dev` | New Ajv-path `fast-uri` findings remediated by root override `3.1.4`; remaining PostCSS finding traces to existing non-protocol workspaces |
| 2026-07-26 04:43 EDT | `npm run check --workspace apps/remote-control-protocol` | GREEN: typecheck, lint, 13 tests, six-schema byte-identical build copy |
| 2026-07-26 04:43 EDT | `npm test --workspace tests-js -- --run` | GREEN: 3 files, 9 tests |
| 2026-07-26 04:43 EDT | `uv run --frozen --extra dev --extra remote-control ...` | GREEN: Ruff, ty, and 13 focused tests |
| 2026-07-26 04:43 EDT | Hermetic wrapper for protocol plus project metadata tests | GREEN exit 0: 22 passed; same non-fatal Windows cp1252 progress traceback |
| 2026-07-26 04:43 EDT | `git diff --check` | GREEN; only expected Windows LF-to-CRLF checkout warnings |
| 2026-07-26 04:44 EDT | Task 1 atomic commit | `abf106e07bd734cddee23226bd6c2832c8a93488` |
| 2026-07-26 04:49 EDT | `npm test --workspace apps/remote-control-protocol -- --run src/reducer.test.ts src/compatibility.test.ts` | Intended RED: 2 files, 8 failed assertions because reducer/negotiator modules do not exist |
| 2026-07-26 04:50 EDT | Same focused Task 2 command after minimal implementation | GREEN: 2 files, 8 tests; each property ran 1,000 generated cases |
| 2026-07-26 04:52 EDT | Reducer bounded-history test | Intended RED: identity-window constant absent |
| 2026-07-26 04:53 EDT | Same reducer test after a 4,096-identity cap | GREEN: 1 file, 5 tests; state growth remains bounded between snapshots |
| 2026-07-26 04:54 EDT | `npm run check --workspace apps/remote-control-protocol` | GREEN: typecheck, zero lint findings, 3 files/22 tests, six-schema build gate |
| 2026-07-26 04:54 EDT | `npm test --workspace tests-js -- --run` | GREEN: 3 files, 9 tests |
| 2026-07-26 04:54 EDT | `fast-check@4.9.0` dependency review | MIT, development-only, locked with `pure-rand@8.4.2`; no new runtime dependency |
| 2026-07-26 04:54 EDT | `git diff --check` | GREEN; only expected Windows LF-to-CRLF checkout warnings |
| 2026-07-26 04:56 EDT | Final protocol check after predecessor-link coverage review | GREEN: 3 files, 22 tests; gap property covers both missing sequence and wrong `prevSeq` |
| 2026-07-26 04:56 EDT | Task 2 atomic commit | `b651ed53f9320807419a54b82f8d7fee25ffb5b6` |
| 2026-07-26 04:58 EDT | Publish checkpoint | Branch tracks `origin/feat/remote-control-protocol-v1`; stacked draft PR #2 is open |
| 2026-07-26 05:07 EDT | `npm test --workspace apps/remote-control-protocol -- --run src/canonicalize.test.ts src/risk.test.ts` | Intended RED: 2 files, 7 failed assertions because canonicalization/signature and risk modules do not exist |
| 2026-07-26 05:07 EDT | `uv run --frozen --extra dev --extra remote-control pytest tests/remote_control/test_protocol_signatures.py -q` | Intended RED: 4 failed assertions because Python canonicalization/signature and authorization APIs do not exist |
| 2026-07-26 05:09 EDT | Focused Task 3 TypeScript and Python commands after minimal implementation | GREEN: 2 files / 7 TypeScript tests; 4 Python tests |
| 2026-07-26 05:10 EDT | Focused fail-closed refactor tests | Intended RED: invalid TypeScript clock, malformed TypeScript risk, and unverified cross-runtime biometric proof were accepted/unsupported |
| 2026-07-26 05:11 EDT | Focused Task 3 commands after security refactor | GREEN: 2 files / 7 TypeScript tests; 4 Python tests |
| 2026-07-26 05:12 EDT | First broad protocol check | Typecheck initially found three integration issues; after correction, package check GREEN: 5 files / 29 tests and schema gate |
| 2026-07-26 05:14 EDT | Python Ruff/ty/focused pytest | GREEN after one type-only RFC 8785 value narrowing correction: Ruff and ty clean; 26 tests passed |
| 2026-07-26 05:18 EDT | Android portability review | Rejected pre-commit `node:crypto` import: RN 0.86 does not document WebCrypto and `jose` requires WebCrypto outside Node. Added narrow async runtime crypto provider instead. |
| 2026-07-26 05:19 EDT | Focused TypeScript tests/typecheck after provider refactor | GREEN: 2 files / 7 tests; TypeScript clean |
| 2026-07-26 05:22 EDT | Runtime-provider fail-closed tests | Intended RED: malformed digest output authorized and malformed verified payload returned the weaker payload-mismatch result |
| 2026-07-26 05:22 EDT | Focused provider tests/typecheck/lint after hardening | GREEN: 2 files / 7 tests; TypeScript and lint clean |
| 2026-07-26 05:23 EDT | Canonical repository runner via Git Bash/Windows venv | GREEN exit 0: 3 files / 26 tests; same non-fatal cp1252 progress callback traceback |
| 2026-07-26 05:24 EDT | Exact target-context tests | Intended RED then GREEN: both runtimes now reject a signed device/session target when caller omits either binding |
| 2026-07-26 05:25 EDT | Final Task 3 commit gate | GREEN: protocol 5 files / 29 tests plus type/lint/schema gate; root JavaScript 9 tests; Python Ruff/ty clean and 26 focused tests; `git diff --check` clean except expected line-ending notices |
| 2026-07-26 05:26 EDT | Task 3 atomic commit | `daca7c231` — `feat(remote-protocol): bind signed capabilities and risk` |
| 2026-07-26 05:28 EDT | Push / draft PR checkpoint | `e886b69bb` is on `origin/feat/remote-control-protocol-v1`; fork draft PR #2 remains open and stacked on the planning branch |
| 2026-07-26 05:33 EDT | Task 4 canonical focused test | Intended RED: 1 file / 4 failed assertions because the listener hub and server registration API do not exist |
| 2026-07-26 05:36 EDT | Task 4 canonical focused test after minimal implementation | GREEN: 1 file / 4 tests; local transport identity/order, asynchronous two-subscriber copies, exception isolation, overflow reset |
| 2026-07-26 05:37 EDT | Task 4 Ruff/ty | GREEN for listener hub, server integration, and focused tests |
| 2026-07-26 05:39 EDT | Canonical Task 4 regression run | New hub and protocol files passed; existing reasoning-scope file could not collect because Windows `env -i` strips home-resolution variables. Wrapper exit 1; no product assertion failed. |
| 2026-07-26 05:40 EDT | Direct focused regression diagnostic | GREEN: 3 files / 109 tests, including reasoning session scope |
| 2026-07-26 05:42 EDT | Concurrent local/remote ordering test | Intended RED: local transport order was `[1, 2]` while the listener observed `[2, 1]` under racing writers |
| 2026-07-26 05:43 EDT | Per-session write/publish ordering lock | GREEN: focused hub 5 tests; Ruff and ty clean |
| 2026-07-26 05:44 EDT | Final Task 4 canonical focused gate | GREEN exit 0: 1 file / 5 tests; `git diff --check` clean except expected line-ending notices |
| 2026-07-26 05:45 EDT | Task 4 atomic commit | `b82922970` — `feat(tui-gateway): add isolated session event listeners` |
| 2026-07-26 05:47 EDT | Task 4 publish checkpoint | Branch and fork draft PR #2 are at `2b1f07162`; PR remains open, draft, and GitHub reports a clean merge state |
| 2026-07-26 05:48 EDT | Final Task 4 documentation publish | `2fbd04c8d` pushed; local branch and `origin/feat/remote-control-protocol-v1` match |

Tooling note: Hermes intentionally blocks ordinary wheel/sdist builds. A wheel smoke attempt failed at the repository's explicit distribution guard before packaging, so supported editable/source-install verification is authoritative for this slice.

## Open product/security decisions

These do not block the safe Task 5 subset:

- explicit acceptance of trusted-relay confidentiality risk;
- selective five-minute offline prompt queue versus no offline commands;
- non-GMS scanner expectations;
- one-replica relay availability trade-off;
- real Windows/macOS secure-store and service-context validation;
- later cloud region/SKU/operator policy and APK signing custody.

Do not implement a decision-dependent relay/queue/signing behavior until its decision is resolved or the implementation preserves both options behind a narrow interface.

## Restart commands

```powershell
Set-Location 'A:\Hermes Mobile App\hermes-remote-control-implementation'
git status --short --branch
git log --oneline --decorate -8
git fetch origin upstream
Get-Content -Raw AGENTS.md
Get-Content -Raw docs\remote-control\HANDOFF.md
Get-Content -Raw docs\remote-control\22-test-first-implementation-plan.md
```

Before changing code, confirm the branch is not `main` or `plan/hermes-android-remote-control`, the worktree is clean or every dirty path is explained above, and the next test is named here.

## Handoff quality checklist

- Repository/branch/worktree/HEAD are exact.
- “Current work” matches `git status` and the latest commit.
- Next command is executable without guessing.
- Latest red/green verification is recorded with outcome.
- Open decisions are separated from blockers.
- No secret or sensitive content is present.
- Stale completed detail has been condensed.
