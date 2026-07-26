# ADR-008: Selective Offline Queue and Zero Retention

Status: Proposed—offline prompt policy requires Gate 1 acceptance

Date: 2026-07-26

## Decision

Default relay content window is 15 minutes/10 MiB per computer. Only an explicitly selected low-risk `prompt.submit` may wait for an offline host, maximum five minutes, when the host advertised support and revision/capability/policy hashes still match. All sensitive actions are online-only. Computer-level zero retention uses live routing only and retains minimum identity/revocation/security metadata.

## Rationale

Short prompt queue improves transient usability without allowing stale approvals, terminal/file/config/new-session actions. Zero retention gives a stronger privacy choice without deleting canonical local Hermes history.

## Consequences

Zero-retention reconnect may require host snapshot and relay attachment staging is unavailable. Backups can retain previously persisted default-mode ciphertext until backup expiry; copy/runbooks disclose this.
