# Hermes Android Remote Control — Development Handoff

Last refreshed: 2026-07-26 04:58 EDT

Refresh owner: the active implementation agent

Status: implementation authorized; Milestone 1 / Task 2 complete, Task 3 next

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
| Stacked base branch | `plan/hermes-android-remote-control` |
| Stacked base commit | `28e1bb59dfee7c54340fbc0798e1dba69516b708` |
| Upstream baseline | `21a2185f86f64be10d28bec1ecc576d89230f761` |
| Planning worktree | `A:\Hermes Mobile App\hermes-android-remote-control-plan` |
| Planning draft PR | `https://github.com/allwavemedia/hermes-agent-mobile-app/pull/1` |
| Implementation draft PR | `https://github.com/allwavemedia/hermes-agent-mobile-app/pull/2` |

The implementation branch is intentionally stacked on the documentation branch until the planning PR is merged. Do not rebase it onto `main` without first checking the PR/base state and preserving the handoff.

## Scope and authority

The user explicitly authorized development after the planning stop gate. Begin with reversible foundation slices. Do not create cloud resources, public endpoints, signing keys, or a public release without separate explicit approval. Do not claim E2EE; the proposed MVP relay is content-trusted.

Current slice: [Milestone 1, Task 3](22-test-first-implementation-plan.md#task-3--canonical-signatures-capabilities-and-risk-policy), canonical signatures, capabilities, and risk policy.

Task 1 execution corrections accepted during critical review:

- Add `jsonschema==4.26.0` as a direct dependency of a dedicated `remote-control` extra because production Python code imports it; do not rely on its incidental presence in the development-only MCP stack or enlarge the default core install.
- Make initial red tests fail by assertion on missing/unsupported behavior, not by test-runner configuration or uncaught import errors.
- Canonical schemas already exist under `docs/remote-control/schemas/v1/`; implementation consumes and validates those bytes rather than recreating them.

These corrections do not change protocol semantics.

## Required reading on restart

Read completely, in order:

1. root `AGENTS.md`;
2. this file;
3. `docs/remote-control/README.md`;
4. `docs/remote-control/22-test-first-implementation-plan.md`;
5. the relevant Android/engineering `SKILL.md` files for the next task.

For Android work, use the installed official skills at `C:\Users\ldoby\.codex\skills\`, especially `android-cli`, `testing-setup`, and `android-intent-security` when their trigger conditions apply. The CLI executable is `C:\ProgramData\AndroidCLI\android.exe` if the current process has a stale `PATH`.

## Work completed

- Gate 0/Gate 1 planning package: 46 documentation artifacts, eight ADRs, six v1 schemas, 28 test-first tasks.
- Planning branch pushed and documentation-only draft PR #1 opened.
- Official Android skills installed for Codex.
- Isolated implementation worktree and branch created from planning commit `28e1bb59d`.
- Implementation branch pushed and stacked draft PR #2 opened against `plan/hermes-android-remote-control`.

- `abf106e07bd734cddee23226bd6c2832c8a93488` — `feat(remote-protocol): define validated v1 contract`
- `b651ed53f9320807419a54b82f8d7fee25ffb5b6` — `feat(remote-protocol): add deterministic replay reducer`

Task 1 delivered 13 shared literal validation fixtures, validators/types in both runtimes, a direct pinned Python `remote-control` extra, and a build-time schema copy/byte-identity gate. Pairing public JWKs reject private key material.

Task 2 delivered immutable ordered replay results, duplicate/gap/conflict/epoch-reset handling, a 4,096-entry identity cap, and fail-closed highest-common-minor negotiation. Seven properties run 1,000 generated cases each.

## Current work and next exact steps

1. Read Task 3 plus `06-pairing-identity-key-lifecycle.md`, the signature/replay sections of `07-threat-model.md`, and current Python JWT/crypto helpers.
2. Define shared deterministic signature vectors and risk-policy cases before adding production code.
3. Add `jose` only if the reviewed TypeScript implementation requires it; reuse the pinned Python cryptography/PyJWT stack.
4. Run the Task 3 tests for the intended RED, then implement JCS bytes/digests, strict ES256 verification, capability hash, unknown-critical handling, and queue/step-up taxonomy.
5. Refresh this handoff at each red/green boundary and commit the independently verified Task 3 slice.

## Latest verification evidence

| Time | Command | Result |
|---|---|---|
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

Tooling note: Hermes intentionally blocks ordinary wheel/sdist builds. A wheel smoke attempt failed at the repository's explicit distribution guard before packaging, so supported editable/source-install verification is authoritative for this slice.

## Open product/security decisions

These do not block Task 1:

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
