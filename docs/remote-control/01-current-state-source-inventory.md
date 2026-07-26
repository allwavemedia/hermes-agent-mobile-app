# Current State and Source Inventory

## Repository resolution

| Item | Exact value |
|---|---|
| Official upstream | `https://github.com/NousResearch/hermes-agent.git` |
| User fork | `https://github.com/allwavemedia/hermes-agent-mobile-app.git` |
| Clean clone | `A:\Hermes Mobile App\hermes-agent-mobile-app` |
| Planning worktree | `A:\Hermes Mobile App\hermes-android-remote-control-plan` |
| Branch | `plan/hermes-android-remote-control` |
| Selected baseline | `21a2185f86f64be10d28bec1ecc576d89230f761` |
| Fork `main` at discovery | `6ffd7302bf4a2178d784f0d296fb8094a48a5bf4` |
| Extracted archive preserved | `A:\Hermes Mobile App\hermes-agent-mobile-app-main\hermes-agent-mobile-app-main` |

The extracted archive was not a Git checkout and was not modified. The clean worktree was fast-forwarded to current upstream only after confirming the fork commit was its ancestor. The six-commit delta affected project sorting, terminal working-directory behavior, and Desktop E2E tests; it did not introduce a remote-control subsystem.

## Instructions read

`AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `DESIGN.md`, `README.md`, and `apps/desktop/AGENTS.md` were read before authoring. Applicable constraints include:

- keep the orchestration loop narrow; preserve prompt caching;
- behavior belongs in `config.yaml`, secrets in `.env` or native stores;
- Desktop renderer has no Node/Electron access; the backend is authoritative;
- TypeScript state stays feature-owned and interfaces small;
- session IDs are identifiers, not authentication;
- external surfaces require real authentication;
- current approvals are application controls, not an operating-system security boundary;
- cross-platform code must avoid Unix-only process assumptions.

## Source map and contract status

| Area | Verified files | Current behavior | Contract assessment |
|---|---|---|---|
| Desktop transport | `apps/shared/src/json-rpc-gateway.ts`, `websocket-url.ts`; `apps/desktop/src/lib/gateway-events.ts`, `gateway-rpc.ts` | JSON-RPC over WS; pending calls fail on close; browser globals assumed | Reusable algorithms, internal wire contract |
| Gateway RPC/events | `tui_gateway/server.py`, `entry.py`, `ws.py`, `transport.py` | Broad session/tool/config/terminal RPC set and streaming events | Internal; needs stable adapter |
| Session persistence | `hermes_state.py` (`SCHEMA_VERSION = 23`) | SQLite/WAL canonical sessions, messages, lineage, FTS | Durable local source; schema internal |
| Dashboard auth | `hermes_cli/dashboard_auth/ws_tickets.py`, `web_server.py` | 30-second one-time WS tickets; loopback/OAuth/password gates | Useful pattern; browser-oriented |
| Remote messaging | `gateway/relay/*.py`, `docs/relay-connector-contract.md`, `tests/gateway/relay/*` | Experimental outbound connector, HMAC auth, reconnect/backlog/ack/media | Reuse patterns only; not session sync |
| Process isolation | `tui_gateway/host_supervisor.py`, `compute_host.py` | Dashboard/worker supervision and mutator routing | Useful shape; Windows adaptation required |
| Host startup | `hermes_cli/gateway.py`, `gateway_windows.py` | launchd/systemd; Windows Task Scheduler with Startup VBS fallback | Reuse directly |
| Desktop credentials | `apps/desktop/electron/hardening.ts`, `main.ts` | Electron `safeStorage`; isolated OAuth partition | Desktop-only; not headless broker |
| Gateway entry | `gateway/run.py`, `gateway/config.py`; `hermes_cli/subcommands/gateway.py`, `main.py` | Existing optional messaging relay registration and service CLI | Correct broker lifecycle integration point |

## Exact current representations

`tui_gateway/server.py` exposes methods covering session create/list/resume/activate/history/status/save/delete/branch/undo/compress/interrupt/steer; prompts; approvals, clarifications, sudo and secret responses; file/PDF/image attachments; terminal/process/shell; projects; models; tools/toolsets/MCP-adjacent controls; config; handoff/delegation/subagents; and setup/billing/usage.

Events cover message start/delta/interim/complete, thinking and reasoning, tool start/progress/complete/output-risk, approval/clarification/sudo/secret/terminal-read requests, status/background/subagent updates, session metadata, titles, and usage. History is available as a state query, but live events do not carry a durable sequence/cursor contract.

The supported public surface is the documented CLI and user-facing Desktop/dashboard behavior. The Python decorators, event dictionaries, SQLite rows, Electron IPC, and `apps/shared` JSON-RPC types are implementation details until explicitly stabilized.

## Multi-client and reconnection finding

The current live session dictionary contains one `transport`. `session.resume` and `session.activate` bind that field to `current_transport()`. `write_json` sends session-scoped events to that transport; only sessionless events fan out to `_live_transports`. A resume lock prevents duplicate agent reconstruction, but it does not provide simultaneous event subscriptions. This makes “Desktop plus Android share the same live session” a hard capability gap.

Gateway WebSocket disconnect handling detaches a client and reaps after a grace period (20 seconds by default). `JsonRpcGatewayClient` rejects outstanding requests on close. Neither layer defines persisted ordered replay, acknowledged cursors, gap detection, or idempotent command recovery.

## Reuse decisions

Directly reuse:

- SessionDB as the local canonical transcript;
- gateway RPC handlers for actual Hermes-authorized operations;
- gateway startup on Windows/macOS;
- outbound connector retry/ack/capability test patterns;
- browser WS ticket concepts and Electron credential hygiene;
- framework-neutral JSON-RPC parsing/state normalization after removing browser globals.

Adapt:

- gateway event publication into a multi-subscriber listener hub;
- host supervision into a cross-platform broker;
- Desktop settings/status integration;
- shared TypeScript code into a schema-driven protocol package;
- auth from browser tickets/HMAC shared secrets to paired public-key identities.

Keep local-only:

- provider secrets and provider configuration;
- arbitrary shell/filesystem/process access outside Hermes;
- permanent MCP installation or mutation;
- operating-system login, wake, remote desktop, and unrelated processes;
- full secret/sudo values, which remain entered locally in MVP unless a later security review explicitly expands scope.

## Official behavior references

- [Hermes Desktop](https://hermes-agent.nousresearch.com/docs/user-guide/desktop)
- [Hermes web dashboard](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard)
- [Claude Code Remote Control](https://code.claude.com/docs/en/remote-control)
- [React Native releases](https://reactnative.dev/docs/0.86/releases)
- [Android Keystore](https://developer.android.com/privacy-and-security/keystore)

Claude is a behavior reference only: local execution, simultaneous surfaces, explicit enablement, QR/session links, outward connectivity, trusted devices, reconnection, permissions, retention limitations, and notifications. No undocumented proprietary implementation is assumed.
