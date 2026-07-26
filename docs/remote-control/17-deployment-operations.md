# Deployment and Operations

## Supported deployment shapes

### Docker Compose reference

Later implementation adds `deploy/remote-control/compose.yaml`, `.env.example`, relay Dockerfile, PostgreSQL health check, named volumes, and an optional local attachment volume. The relay container runs non-root, read-only root filesystem, drops Linux capabilities, uses a tmpfs for temporary data, has resource limits, and exposes only its HTTP/WSS port. PostgreSQL is private to the Compose network. TLS terminates at an operator-provided reverse proxy or relay certificate configuration; example credentials are never valid defaults.

Required operator inputs:

- public `RELAY_ORIGIN`;
- PostgreSQL DSN via secret;
- 32-byte+ KEK and key version via secret;
- relay ES256 service signing key via secret;
- TLS certificate/key or documented reverse-proxy mode;
- retention/queue/attachment quotas;
- allowed origins and structured log level.

`docker compose config` must succeed before start. Bootstrap migration is explicit and idempotent; relay refuses a newer/unknown schema. Backups and KEK backups are configured before production data.

### Azure reference

Provider-neutral abstractions map to:

- Azure Container Apps, Consumption workload, exactly one warm replica for MVP WebSockets;
- Azure Database for PostgreSQL Flexible Server with TLS/private networking where available;
- Azure Blob Storage private container for temporary attachments;
- Container Apps secrets (or Key Vault integration as an operator choice) for KEK, DSN, and service key;
- Azure Monitor/Log Analytics for allowlisted logs/metrics;
- managed certificate/custom domain or a fronting service that preserves WebSockets.

Product authentication uses pairing keys, not Entra. Azure resource management may use normal Azure operator identity without becoming an end-user dependency. Terraform/Bicep is provider-specific reference material; the relay itself remains runnable outside Azure.

## Network requirements

Host requires outbound DNS and TCP 443 to configured relay. No inbound public firewall rule. Android uses normal HTTPS/WSS. Idle ping interval stays within common proxy timeouts and is configurable (default 25 seconds), but ping contains no sensitive data.

Direct mode is disabled by default. When enabled, host binds only explicitly selected RFC1918/Tailscale interfaces and a random/high configured port, requires WSS and signed challenge, and displays firewall action. It never enables UPnP/NAT-PMP or public port forwarding.

## Runbooks

### Normal deployment

1. Verify image digest, SBOM, signature/provenance.
2. Apply additive database migration.
3. Start new relay revision with readiness false.
4. Verify KEK, DB, blob, schema, and expiry-worker lease.
5. Mark ready and drain old revision for 20 seconds.
6. Inspect auth/replay/reset/error metrics and oldest queue age.
7. Retain prior image and migration rollback decision.

Single-replica Container Apps may briefly reconnect clients during revision change. The protocol absorbs this through replay/snapshot; it is an accepted MVP availability trade-off.

### Suspected key compromise

- Relay service key: stop credential issue, rotate service key with controlled overlap, revoke active relay credentials, force reconnect.
- KEK: block writes, rotate/rewrap DEKs, audit access, delete compromised version only after verification.
- Host identity: local user rotates, trust epoch increments, all devices re-pair.
- Device: revoke immediately; no host key rotation needed unless host also compromised.

### Queue/backlog incident

Reject new offline queue before memory/disk exhaustion, preserve live approvals/events, alert, inspect content-free size/age metrics, expire by policy, and never extend TTL to hide an outage.

### Database/blob outage

Zero-retention live routing may continue only if revocation/auth state remains safely available in verified cache and policy explicitly allows it; default is readiness false and reconnect. Persistent mode never acknowledges queue/upload until durable commit succeeds.

## Backup and restore

Back up PostgreSQL and KEK material through separate access paths. Blob lifecycle is not a backup requirement because attachments are temporary. Quarterly restore test verifies identities/revocation/queue metadata, decrypts a synthetic canary, and proves expired content is not resurrected into routable state. Restored relay starts isolated until expiry and revocation reconciliation completes.

## Capacity and cost

Measure concurrent sockets, events/second, mean payload, reconnect rate, attachment bytes/egress, PostgreSQL IOPS/storage, and log ingestion. Persistent WebSockets make minimum replica time a baseline cost. PostgreSQL is likely the dominant fixed MVP cost; attachments/egress dominate variable high-volume cost. Multi-region, HA database, private endpoints, longer audit retention, and warm standby are explicit cost multipliers, not MVP defaults.

## Environment readiness for later work

Current machine can author/validate docs and use Git/GitHub, Node/npm, `uv`, Docker client/Compose, and Azure CLI. It cannot build Android: JDK, Android Studio/SDK/Gradle/ADB/signing tools are absent. Docker daemon is stopped. Installed Python 3.14.6 is outside Hermes-supported 3.11–3.13. Tailscale is absent. Gate 1 provisioning should use Python 3.11 or 3.13 in `uv`, JDK 17, Android SDK/Build Tools 36.0.0, and an emulator/device matrix; no global changes were made in planning.
