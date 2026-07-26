# Host and Desktop Integration

## Integration rule

Remote control is an adapter over current Hermes behavior, not a second execution system. Existing RPC handlers continue to own sessions, models, tools, approvals, terminals, attachments, and persistence. The adapter has an allowlist mapping from protocol command to a specific internal handler; no generic “invoke any RPC” endpoint exists.

## Event publication change

`tui_gateway/transport.py` gains a listener protocol and bounded fan-out hub. `tui_gateway/server.py` publishes a normalized copy after existing session-event routing. It must preserve:

- the exact local `session["transport"]`;
- current Desktop/TUI event order and latency;
- prompt caching and orchestration loop;
- failure isolation (listener exceptions/logging cannot fail the agent);
- unscoped versus scoped event semantics.

Remote subscriptions are registered by the host adapter, not represented as the session transport. This is the first implementation slice and a hard blocker.

## Broker lifecycle

`gateway/run.py` creates `RemoteControlBroker` only when `remote_control.enabled` is true. The existing gateway process and service installation remain the lifecycle owner:

- Windows uses existing Scheduled Task/Startup fallback in `hermes_cli/gateway_windows.py`;
- macOS uses existing launchd support in `hermes_cli/gateway.py`;
- systemd remains available upstream but is outside the requested paired-host MVP;
- stop/status include broker health and connected-device/session counts without content.

Config belongs in `config.yaml`:

```yaml
remote_control:
  enabled: false
  relay_url: https://relay.example.invalid
  auto_enable_sessions: false
  retention_mode: temporary
  direct:
    enabled: false
    interfaces: []
  attachment_max_mb: 50
```

Keys and relay operator secrets never enter YAML. Environment variable overrides are documented for deployment, but host identity stays in native secure storage.

## Local IPC and registration

Each `hermes serve`/session process registers session ID, PID, process start time, gateway protocol fingerprint, remote-enable state, and safe display metadata with the broker. Broker challenges the child over an OS-user-protected channel. Re-registration after broker restart creates a new epoch and snapshot.

Adapter commands are passed over request/response IPC with deadlines and idempotency. Event stream uses length-prefixed frames and a bounded queue. The broker never imports a session’s mutable in-memory server object across process boundaries.

## Existing and new sessions

- Existing sessions are remote-disabled by default. Desktop/CLI enable action registers the adapter and emits a signed capability snapshot.
- Auto-enable is a local computer policy and affects only sessions created after the policy change unless the user explicitly enables current sessions.
- Basic remote new-session request selects one advertised project and model. Broker starts the same Hermes session command path as local UI, with a structured argument list and sanitized inherited environment. Host must be online.
- Disabling remote control detaches listeners, invalidates capabilities, emits `session.remoteDisabled`, and leaves local execution running.

## Desktop UI

Add a Remote Control settings section:

- broker enabled/health and relay connectivity;
- pair-device QR/manual code with countdown;
- paired device list, last seen, rename and revoke;
- temporary versus zero retention;
- auto-enable toggle with warning;
- direct fallback toggle/interface/pin status;
- per-session enable/disable action and remote-presence indicator.

Renderer receives only typed data through preload IPC. Electron main invokes local broker commands. Device keys/credentials never enter renderer state or logs. Closing Desktop does not stop the gateway service or remotely enabled sessions.

## Local-only operations

Provider secret input, sudo password, unrestricted shell, arbitrary filesystem picker/path, credential management, permanent MCP installation/config, gateway service installation, computer wake, and remote-control key reset remain local. Remote UI can show “Action required on computer” without relaying the sensitive value.

## Version/update behavior

Broker advertises Hermes commit/version, protocol range, and adapter capability version. Unsupported major version refuses remote activation without affecting local sessions. Desktop and host broker update through existing Hermes mechanisms; Android/relay compatibility is negotiated. A rollback disables new protocol features while continuing v1 if schema compatibility remains.
