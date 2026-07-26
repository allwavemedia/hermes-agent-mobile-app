# ADR-002: Trusted-Relay MVP, No E2EE Claim

Status: Proposed—explicit Gate 1 acceptance required

Date: 2026-07-26

## Context

Temporary queueing, multi-device routing, attachments, abuse controls and simple self-hosting are required. A correct E2EE group/key-rotation/revocation/recovery design is not proven.

## Decision

Relay workers may decrypt content in MVP. Use TLS 1.2 minimum and 1.3 preferred in transit, AES-256-GCM per-computer encryption at rest, and ES256 device/host signatures for sensitive authorization/integrity. TLS 1.2 is limited to modern AEAD/ECDHE policy for the Android API 24 floor; older versions are disabled. Offer zero relay content retention and pinned direct fallback. Product copy never says E2EE or zero knowledge.

## Consequences

Operators/relay compromise can expose routed content; this is a visible residual High risk. Security-sensitive command forgery remains outside relay authority. A future E2EE design must supersede this ADR and solve multi-device, queued blob, metadata, rotation/revocation and recovery semantics.

## Rejected

Mislabeling TLS as E2EE, custom cryptography, or blocking MVP on an undocumented key protocol.
