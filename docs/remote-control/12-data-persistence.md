# Data and Persistence

## Sources of truth

| State | Authority | Persistence |
|---|---|---|
| Hermes transcript/session lineage | Existing `SessionDB` in `hermes_state.py` | Existing SQLite/WAL |
| Live run/tool/request state | Existing gateway/session process | Memory + existing session save behavior |
| Remote projection sequence/replay | Host broker | Separate `remote-control.db`, bounded |
| Pairing/device/revocation | Host broker and relay, reconciled by signed trust epoch | Native key store + host DB + relay PostgreSQL |
| Relay queue/attachments | Relay | PostgreSQL + blob/file adapter, encrypted and expiring |
| Android keys | Android Keystore | Non-exportable |
| Android public metadata/cursor | DataStore | Backup excluded |
| Android content projection | App memory | Cleared on security lifecycle |

Remote control does not change SessionDB schema for MVP. A separate database limits migration and rollback risk. It stores no duplicate full transcript; snapshots are generated from SessionDB and live adapter state.

## Host `remote-control.db`

SQLite uses WAL, foreign keys, busy timeout, explicit schema version, and atomic migrations. Tables:

- `schema_meta(version, migrated_at)`;
- `computer_identity_metadata(id, public_thumbprint, trust_epoch, created_at)`;
- `devices(id, public_jwk, thumbprint, display_name, paired_at, revoked_at, trust_epoch)`;
- `session_policies(session_id, enabled, auto_enabled, retention_mode, updated_at)`;
- `session_epochs(session_id, epoch, next_seq, snapshot_revision, capability_hash)`;
- `event_journal(session_id, epoch, seq, event_id, payload, expires_at, size_bytes)`;
- `command_receipts(device_id, idempotency_key, payload_hash, result, expires_at)`;
- `audit_events(...)` with content-free columns.

Journal payload is local-only and inherits host disk protection. The 15-minute/10-MiB bound is enforced transactionally per session/computer. Expiry and compaction never block the gateway write path.

## Relay persistence

See [relay data model](08-relay-design.md#data-model). Content columns are application-encrypted with per-computer DEKs; public identity and routing indices remain plaintext because the service must query them. Database disk encryption is an additional infrastructure control, not a substitute for application encryption.

Deletion semantics:

1. Mark expired/revoked within the same transaction that makes it unavailable.
2. Delete content row/object.
3. Record content-free deletion outcome.
4. Retry orphan cleanup with bounded backoff.
5. Alert on oldest expired object/row age.

Backups can extend physical recoverability. Operational policy sets backup retention to the minimum acceptable period and documents that logical deletion cannot erase prior immutable backups immediately. Zero-retention content never enters backups.

## Android model

DataStore records:

- computer ID/name, host public JWK/thumbprint, relay origin, direct pin;
- device ID/key alias (not private key), pairing/revocation state;
- retention/direct display state;
- per-session last acknowledged `(epoch, seq)` and safe display metadata;
- app lock preferences.

It does not record prompts, responses, tool output, approval payloads, credentials, pairing capabilities, nonces, or attachment bytes. Process death therefore forces a signed snapshot/replay before actions re-enable.

## Consistency and clocks

Security expiry is checked by relay and host using their clocks. A peer clock error over five minutes produces a diagnostic and denies state-changing commands; it does not silently widen expiry. Ordering uses sequence numbers/database transactions, never timestamps alone.

Trust epoch resolves revocation races: every credential/envelope contains the current epoch, and increasing it invalidates old state. Session revision resolves policy/capability races. Event epoch resolves broker/session restart.

## Privacy classification

- **Secret:** private keys, KEKs/DEKs, connection credentials — native/secret stores only.
- **Sensitive content:** prompts, responses, tool output, attachment bytes — transient/bounded encrypted handling.
- **Sensitive metadata:** project/session/device names, public keys, timing — minimized and access controlled.
- **Security metadata:** hashes, revocations, rate-limit keys, results — retained according to policy without content.

Telemetry and support exports are allowlist-based. A field not classified is not emitted.
