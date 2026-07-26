# ADR-007: Provider-Neutral Single-Replica Relay MVP

Status: Proposed

Date: 2026-07-26

## Decision

Build a Node TypeScript modular monolith with `ws`, `pg`, `jose`, and `ajv`; PostgreSQL plus storage interface; Docker Compose reference; Azure Container Apps/PostgreSQL/Blob reference. Support exactly one live-routing replica in MVP. Product identity is pairing keys, never Entra.

## Rationale

This is the smallest portable design with durable expiry/revocation and real WebSocket routing. It avoids premature Redis/Kubernetes/distributed presence.

## Consequences

Deploy/restart causes a reconnect window; replay handles correctness, not continuous availability. A multi-replica design requires a new ADR and fan-out/lease/partition tests.
