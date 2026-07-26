# Relay Design

## Responsibilities and non-responsibilities

The relay authenticates connections, matches paired routes, forwards signed envelopes, persists bounded encrypted queues where allowed, stores public pairing/revocation metadata, handles attachment staging, enforces quota/expiry, and emits content-free audit/metrics. It does not run Hermes, decide Hermes approvals, hold provider secrets, wake computers, or create user accounts.

## Service shape

`apps/remote-control-relay` is a TypeScript modular monolith:

- Node HTTP server: `/health/live`, `/health/ready`, metrics, pairing claim endpoint, attachment upload/download;
- `ws` endpoint: multiplexed host/device channels;
- `jose`: relay credentials and verification of paired JWS;
- `ajv`: canonical protocol schema validation;
- `pg`: PostgreSQL transactions and leases;
- storage interface: local filesystem in Compose, Azure Blob in reference deployment;
- crypto interface: Node `crypto` AES-256-GCM and operator-supplied KEK.

One replica is the supported MVP topology. PostgreSQL is durable, but live connection routing is process-local. Multi-replica deployment is rejected until a tested connection-directory/fan-out mechanism exists; Kubernetes/Redis complexity is not hidden in the first release.

## Data model

| Table | Important columns | Content policy |
|---|---|---|
| `computers` | ID, host public JWK/thumbprint, trust epoch, retention mode, last seen | Metadata |
| `devices` | ID, computer ID, public JWK/thumbprint, name, paired/revoked times | Metadata |
| `pairing_offers` | salted capability hash, host-signed offer, expiry, attempts, consumed time | Two-minute TTL |
| `revocations` | subject ID, trust epoch, reason code, timestamp | Retained security state |
| `queue_envelopes` | route, type, encrypted payload, nonce/tag, expiry, size, device/idempotency IDs | Default only; no zero retention |
| `command_receipts` | device/idempotency key, payload hash, status, expiry | Content-free where possible |
| `attachments` | encrypted manifest, object key, digest, size, expiry, state | Temporary; no zero retention |
| `data_keys` | computer ID, wrapped DEK, KEK version | No plaintext DEK |
| `audit_events` | actor/target IDs, operation, result, risk, hashes, time | No content |

All state transitions that consume pairing offers, revoke identities, or enqueue commands are PostgreSQL transactions. Expiry uses database time to avoid worker-clock races.

## Encryption distinctions

- **TLS 1.2 or 1.3:** link encryption/authentication between client and relay. TLS 1.3 is preferred; TLS 1.2 with modern AEAD/ECDHE suites supports the Android API 24 floor. Older protocol versions are disabled.
- **At-rest encryption:** each content record uses a random 96-bit nonce and AES-256-GCM under a per-computer DEK; AAD binds table, row ID, computer ID, protocol/type, and expiry. DEKs are wrapped by an operator KEK and versioned.
- **Signatures:** JWS ES256 binds paired actor and security-sensitive content; signatures provide authenticity/integrity, not confidentiality.
- **E2EE:** not present in MVP, because relay workers obtain DEKs to route/validate content.

Nonce uniqueness is guaranteed by fresh cryptographic randomness per encryption; a duplicate-nonce detector fails tests and metrics. KEK rotation rewraps DEKs without decrypting every content row. DEK rotation creates a new active key and retains old wrapped keys only until their content expires.

## Retention modes

Default:

- session replay/queue content: 15 minutes, maximum 10 MiB per computer;
- safe offline prompt: five minutes;
- attachment upload grant: 15 minutes;
- incomplete/completed temporary attachment: expired immediately when consumed or swept no later than one hour after expiry;
- content-free audit metadata: 30 days;
- pairing offers: two minutes.

Zero retention:

- live envelopes are held only in bounded memory until write completion;
- no transcript, command, attachment, or replay payload enters PostgreSQL/blob/log;
- reconnect requires host snapshot; offline queue and relay attachments are unavailable;
- device keys, pairing/revocation state, rate-limit hashes, and content-free security audit remain as minimum safety metadata.

Changing to zero retention atomically rejects new persistent work and schedules existing content for immediate deletion. UI reports completion only after database rows/objects are removed.

## Backpressure and abuse controls

- maximum JSON envelope 256 KiB; prompt 64 KiB;
- default attachment 50 MiB each, 200 MiB/computer temporary aggregate;
- per-connection outbound buffer 2 MiB; slow consumers receive `session.reset` then disconnect;
- per-device commands 30/minute burst 10; approval responses 10/minute; pair claims 5/10 minutes/IP and pairing ID;
- maximum five connected devices/computer and ten subscribed sessions/device in MVP;
- cryptographic verification occurs after cheap size/schema/rate checks;
- database and blob timeouts are bounded; readiness fails if durable operations are unsafe.

## Deployment portability

Docker Compose runs relay plus PostgreSQL and a local S3-compatible/file storage adapter only for development/self-hosting. The Azure reference maps relay to Container Apps (one minimum replica for persistent WebSockets), database to PostgreSQL Flexible Server, attachments to Blob Storage, and logs/metrics to Azure Monitor/Log Analytics. Product identity remains pairing keys; Entra is neither required nor used as a mobile login.

Cost is driven by always-on replica CPU/memory, PostgreSQL compute/storage/backups, WebSocket egress, attachment storage/transactions/egress, and log ingestion/retention. Azure publishes Container Apps per-second consumption/request pricing, including scale-to-zero, but this design’s persistent connections require a warm replica; see [Container Apps pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/), [PostgreSQL pricing](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/), and [Blob pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/). No fixed dollar estimate is credible until connection count, regions, attachment volume, and retention are measured.

## Operations

Readiness requires PostgreSQL, KEK availability, schema compatibility, and expiry worker lease. Liveness only proves event-loop health. Graceful shutdown stops accepts, sends retry hints, drains for 20 seconds, persists eligible queued envelopes, and closes sockets. Backup restores are tested into an isolated environment; KEK backup/rotation runbook is mandatory. Content decryption is never part of ordinary support tooling.
