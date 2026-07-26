# ADR-005: Pair Computers, Not Sessions or Accounts

Status: Proposed

Date: 2026-07-26

## Decision

A two-minute one-time QR/manual offer pairs one Android public key to one computer public key. The relationship exposes a computer catalog; each session remains separately remote-disabled by default. No central user account or recovery export exists.

## Rationale

Computer-first trust supports multiple local sessions and future session creation while retaining explicit session authorization. It avoids repeated session pairing and central identity.

## Consequences

A paired phone can see safe computer/session metadata subject to policy, so device revocation and app lock are essential. Pairing does not auto-enable sessions or confer provider/tool/OS authority.
