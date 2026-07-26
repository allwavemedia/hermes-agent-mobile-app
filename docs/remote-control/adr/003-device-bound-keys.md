# ADR-003: Device-Bound Keys and Native Secure Stores

Status: Proposed

Date: 2026-07-26

## Decision

Use P-256/ES256 identities. Android private keys are non-exportable Keystore keys; high-risk signing uses BiometricPrompt `CryptoObject`. Host keys use `keyring` 25.7.x only when its backend is Windows Credential Locker or macOS Keychain; otherwise enablement fails closed. Pairing creates no export/recovery code.

## Rationale

Standard platform-backed primitives provide proof of possession, biometric binding, and revocation without central accounts or shared long-lived secrets. `keyring` reduces platform code but requires a strict backend allowlist.

## Consequences

Lost device/key means re-pairing. Host identity rotation revokes all devices. Real Windows/macOS service-context testing is a release blocker. Direct platform APIs replace `keyring` if that test fails; plaintext fallback is never acceptable.
