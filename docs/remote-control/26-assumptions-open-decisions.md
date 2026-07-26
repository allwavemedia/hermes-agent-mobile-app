# Assumptions and Open Decisions

## Verified facts, not assumptions

- Selected source baseline is upstream commit `21a2185f86f64be10d28bec1ecc576d89230f761`.
- Desktop uses `tui_gateway` JSON-RPC/WebSocket and shared TypeScript client.
- Session-scoped live events currently target one session transport.
- Existing messaging relay is experimental and not a Desktop session-sync service.
- Windows/macOS gateway startup logic already exists.
- Planning host lacks Android/macOS implementation prerequisites.
- All prompt package files were accessible and checksum-verified.

## Assumptions used

| ID | Assumption | Why reasonable | Validation/impact |
|---|---|---|---|
| A-01 | One user controls both phone and paired computer during pairing | Pairing-only identity/no account requirement | Product test; multi-user administration deferred |
| A-02 | Maximum five devices/computer and ten session subscriptions/device is adequate MVP | Bounds abuse/cost while supporting normal use | Load/pilot data; config can narrow, protocol can later expand |
| A-03 | 50 MiB/file and 200 MiB temporary aggregate meets basic attachment need | Covers documents/images, controls relay cost | Pilot metrics; capability advertises lower limits |
| A-04 | 15-minute/10-MiB replay window balances mobile reconnect and privacy | Typical transient loss, bounded storage | Chaos/pilot reset rate |
| A-05 | API 24 is acceptable Android floor | RN 0.86 support floor and Biometric/Scanner compatibility | Confirm target device population |
| A-06 | A warm single relay replica is acceptable MVP | Simplifies correct live routing | Accept SLO/reconnect window or fund distributed design |
| A-07 | Foreground-only attention is acceptable MVP | Explicit no-FCM boundary | User testing; do not imply closed-app notifications |

## Gate 1 decisions requested

### D-01 Trusted relay versus E2EE

Recommendation: accept trusted-relay MVP with precise wording, zero-retention mode and direct option. Requiring E2EE adds multi-device group key distribution, queue/blob encryption, rotation/revocation, metadata/privacy and recovery design; it should be a separate ADR/threat-model phase.

### D-02 Offline prompt queue

Recommendation: permit only explicit `prompt.submit` for five minutes when the host advertised `offlinePrompt.v1`, with revision/capability/policy binding. Safer alternative: zero offline commands. No other command is queueable.

### D-03 QR dependency

Recommendation: Google Code Scanner plus manual code and verified App Link. It avoids camera permission and app-size cost. Non-GMS bundled scanning is deferred unless target fleet requires it.

### D-04 Relay availability

Recommendation: one warm replica and 99.5% routing SLO for MVP. Multi-replica routing requires a separately tested connection directory/fan-out design.

### D-05 Host secure-store adapter

Recommendation: `keyring>=25.7,<26` with exact backend allowlist/fail closed. Re-evaluate after Windows/macOS spike; choose direct platform APIs only if keyring cannot satisfy headless service behavior without insecure fallback.

### D-06 Reasoning visibility

Recommendation: mirror only reasoning/thinking events already exposed by the local Hermes surface and host policy. Do not add hidden model reasoning or provider data.

### D-07 Direct fallback discovery

Recommendation: manual/QR-provisioned endpoints first; optional mDNS conveys discovery metadata only. Never infer trust from LAN/Tailscale membership.

## Deployment decisions deliberately deferred

Relay domain, Azure region, exact SKU, HA/private endpoints, backup duration, log retention, operator access model, custom certificate, production quota, and APK signing custody require deployment/release approval and measured scale. They do not alter the provider-neutral protocol.

## Decision-change rule

Changing D-01, offline sensitive queueing, remote secret/sudo entry, generic terminal/shell scope, pairing recovery/export, multi-replica routing, or Android exported/network policy requires a new ADR, threat-model update, schema/traceability update, and security review before implementation.
