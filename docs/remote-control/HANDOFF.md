# Hermes Android Remote Control — Development Handoff

Last refreshed: 2026-07-26 04:19 EDT

Refresh owner: the active implementation agent

Status: implementation authorized; Milestone 1 / Task 1 setup in progress

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

The implementation branch is intentionally stacked on the documentation branch until the planning PR is merged. Do not rebase it onto `main` without first checking the PR/base state and preserving the handoff.

## Scope and authority

The user explicitly authorized development after the planning stop gate. Begin with reversible foundation slices. Do not create cloud resources, public endpoints, signing keys, or a public release without separate explicit approval. Do not claim E2EE; the proposed MVP relay is content-trusted.

Current slice: [Milestone 1, Task 1](22-test-first-implementation-plan.md#task-1--canonical-v1-schema-and-cross-runtime-validation), canonical v1 schema and cross-runtime validation.

Task 1 execution corrections identified during critical review:

- Add `jsonschema==4.26.0` as a direct Python dependency because production Python code will import it; it currently appears only transitively in `uv.lock`.
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

No implementation production files or dependencies have been changed yet.

## Current work and next exact steps

1. Verify/install repository-local Node dependencies with `npm ci`; do not use global package mutation.
2. Establish a focused baseline using existing TypeScript workspace checks relevant to a new framework-neutral package.
3. Add Task 1 workspace/test configuration and literal valid/invalid fixtures.
4. Run the TypeScript and Python tests and record the intended red assertion failures here.
5. Add the minimal validators/types and explicit Python dependency.
6. Run focused tests/checks, cross-runtime parity, lockfile review, and `git diff --check`.
7. Update this file with green evidence and exact commit, then make the atomic Task 1 commit.

## Latest verification evidence

| Time | Command | Result |
|---|---|---|
| 2026-07-26 04:19 EDT | `git status --short --branch` | Clean branch `feat/remote-control-protocol-v1` |
| 2026-07-26 04:19 EDT | `git rev-parse HEAD` before handoff creation | `28e1bb59dfee7c54340fbc0798e1dba69516b708` |

No Task 1 red or green test has run yet.

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
