# ADR-001: Stable Adapter and Listener Hub

Status: Proposed

Date: 2026-07-26

## Context

Desktop speaks broad internal `tui_gateway` JSON-RPC. A live session stores one transport, and resume/activate can replace it. Publishing that interface remotely would make mobile a competing owner and expose unstable excessive authority.

## Decision

Add a framework-neutral host adapter with explicit snapshot/subscribe/execute/capability methods. Add bounded nonblocking event listeners that receive normalized copies after existing local delivery. A remote subscriber is never assigned to `session["transport"]`. Commands map through an allowlist to current handlers.

## Consequences

Local behavior remains authoritative and independently testable; protocol evolution is decoupled from internal dictionaries. The adapter adds normalization/maintenance cost and must be updated when internal events change. Listener invariants block all later work.

## Rejected

Raw gateway exposure, transport tee as the public contract, SessionDB polling, and a second agent execution loop.
