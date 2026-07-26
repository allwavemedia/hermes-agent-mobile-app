# Hermes Android Remote Control — Planning Package

Status: Gate 0 complete; Gate 1 proposed, pending the decisions in [Gate report](25-gate-0-gate-1-report.md).

Planning baseline: upstream `NousResearch/hermes-agent` commit `21a2185f86f64be10d28bec1ecc576d89230f761`, inspected 2026-07-26.

Phase boundary: documentation only. This package does not authorize implementation.

## Decision in one paragraph

Build a computer-first bare React Native Android client, a versioned framework-neutral TypeScript protocol package, an optional Hermes host broker, and a provider-neutral relay. The host and phone both dial outward to the relay. Hermes continues to execute on the paired Windows or macOS computer, and every mobile control is constrained by a host-advertised capability snapshot and the existing Hermes approval/tool/workspace boundary. The relay may decrypt routed content in MVP and therefore is **not E2EE**; TLS protects transport, AES-256-GCM protects queued content at rest, and device/host ES256 signatures prevent the relay from forging security-sensitive commands or approvals. An authenticated, certificate-pinned LAN/Tailscale path uses the identical protocol and policy checks.

## Reading order

1. [Executive brief](00-executive-brief.md)
2. [Current state and source inventory](01-current-state-source-inventory.md)
3. [Capability-gap matrix](02-capability-gap-matrix.md)
4. [Product requirements](03-product-requirements.md)
5. [System architecture](04-system-architecture.md)
6. [Protocol and schemas](05-remote-control-protocol.md)
7. [Pairing and key lifecycle](06-pairing-identity-key-lifecycle.md)
8. [Threat model](07-threat-model.md)
9. [Relay design](08-relay-design.md)
10. [Host/Desktop integration](09-host-desktop-integration.md)
11. [Android architecture](10-android-architecture.md)
12. [UX flows](11-ux-flows.md)
13. [Data and persistence](12-data-persistence.md)
14. [File transfer](13-file-transfer.md)
15. [Reconnection and queueing](14-reconnection-queueing.md)
16. [Audit and observability](15-audit-observability.md)
17. [Testing](16-testing.md)
18. [Deployment and operations](17-deployment-operations.md)
19. [Release and signing](18-release-signing.md)
20. [Migration and rollback](19-migration-rollback.md)
21. [Dependency, license, and supply-chain audit](20-dependency-license-supply-chain.md)
22. [Exact file-by-file change plan](21-file-by-file-change-plan.md)
23. [Test-first implementation plan](22-test-first-implementation-plan.md)
24. [Acceptance traceability](23-acceptance-traceability-matrix.md)
25. [Security review findings](24-security-review-findings.md)
26. [Gate 0 / Gate 1 report](25-gate-0-gate-1-report.md)
27. [Assumptions and open decisions](26-assumptions-open-decisions.md)

Normative machine-readable artifacts are under [`schemas/`](schemas/); diagram sources are under [`diagrams/`](diagrams/); architecture decisions are under [`adr/`](adr/).

## Package completeness

All files in `Hermes_Android_Remote_Control_Prompt_Package_2026-07-26` were accessible, read, and verified against the supplied `CHECKSUMS.sha256`. The package contained `00_MASTER_ORCHESTRATOR_PROMPT.md`, prompts `01` through `13`, `README.md`, `MANIFEST.json`, and `CHECKSUMS.sha256`. No package content was invented.

## Normative language

“MUST”, “MUST NOT”, “SHOULD”, and “MAY” are used as requirements. A capability absent from the host’s signed capability snapshot is denied by default. Documents record a plan, not an implemented guarantee.
