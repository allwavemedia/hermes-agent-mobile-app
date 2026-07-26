# Migration and Rollback

## Additive introduction

Remote control ships disabled. Existing Desktop, TUI, gateway, messaging connectors, SessionDB, and CLI behavior remain unchanged until local opt-in. Rollout order:

1. protocol package and inert listener hub;
2. host adapter/broker disabled by default;
3. relay internal environment;
4. Desktop controls behind feature flag;
5. Android internal APK;
6. Windows/macOS pilot;
7. optional public GitHub prerelease/release.

No existing session is auto-enabled during upgrade. Enabling auto-enable requires an explicit local choice.

## Database migrations

Host uses a new `remote-control.db`; SessionDB v23 is not altered for MVP. Migration runs under an exclusive broker startup lock, creates a backup of the small metadata DB before schema change, and is idempotent. Unknown newer schema disables remote control but does not block Hermes gateway/session startup.

Relay uses numbered PostgreSQL migrations:

- expand schema first (nullable/additive);
- deploy code supporting old and new;
- backfill content-free metadata in bounded batches;
- switch reads;
- contract only after at least one release and rollback window.

Migrations never extend expired content. Data copied/backfilled retains original expiry and encryption AAD/version.

## Protocol migration

Within v1, additive minor features are capability-gated. Host/relay/app continue the previous minor until all peers share the new one. A v2 deployment runs alongside v1 routes or uses a translating host boundary only if security semantics are equivalent and tested; relay never silently strips v2 security fields to create v1.

## Kill switches

Independent controls:

- relay global accept-new-connections;
- relay offline queue;
- relay attachments;
- host broker enabled;
- host auto-enable;
- host direct fallback;
- per-computer remote access;
- per-session remote access;
- device revocation/trust epoch.

Security switches fail closed and are auditable. Disabling remote control leaves local Hermes work running.

## Rollback cases

| Failure | Rollback | Local impact |
|---|---|---|
| Listener hub regression | Disable broker/listeners or revert adapter commit | Local sessions continue; verify transport |
| Broker crash loop | `remote_control.enabled=false`, restart existing gateway service | Remote unavailable only |
| Relay application regression | Route/deploy previous compatible image; clients replay/snapshot | Short reconnect |
| Relay DB migration issue | Stop writes, restore/roll forward per migration; never restore expired routable content | Remote unavailable |
| Android regression | Re-release prior safe source with higher versionCode | Pairings retained only if storage/protocol compatible |
| Key/signature flaw | Disable affected command types, revoke credentials/keys as scope requires | Local approvals remain |
| Content leakage | Disable persistence/attachments, preserve evidence, rotate relevant keys, delete per incident plan | Zero-retention/live may remain only after review |

## Uninstall and data deletion

Android uninstall removes app DataStore and Keystore aliases under normal Android semantics; host/relay device record remains revocable and marked stale until local deletion. “Remove computer” first requests device revocation when online; offline local removal warns that host-side revocation must be completed separately.

Host “reset remote control” stops broker, increments trust epoch, revokes devices/offers, removes host remote metadata/database after confirmation, deletes native identity key, and leaves SessionDB/workspaces untouched. Relay deletion removes content and route metadata subject to security/audit/legal policy.

## Rollback rehearsal

Before release:

1. start active local + remote session;
2. upgrade host/relay/app one at a time;
3. prove continuity/replay and local operation;
4. roll relay and host back one compatible version;
5. disable broker mid-run and prove local run completes;
6. reinstall higher-version rollback APK;
7. verify no stale approval/queue executes;
8. verify data/keys expected to survive or be revoked exactly as documented.
