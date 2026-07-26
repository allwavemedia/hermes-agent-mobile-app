# ADR-006: Snapshot Plus Ordered Bounded Replay

Status: Proposed

Date: 2026-07-26

## Decision

Each remotely enabled session has an epoch and monotonic sequence. Clients start from a signed snapshot and apply contiguous events. Acknowledged cursors enable bounded replay; gaps/expired epochs force snapshot reset. Commands use idempotency receipts and expected revision/run.

## Rationale

Mobile networks and app lifecycle make disconnect normal. Current Hermes history and live events lack a durable cursor. Snapshot/replay converges without making relay/Android a transcript authority.

## Consequences

Host maintains a 15-minute/10-MiB journal. Clients may refresh after longer outages. Sequence correctness and transport independence require property/chaos tests.
