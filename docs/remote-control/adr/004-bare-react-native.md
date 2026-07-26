# ADR-004: Bare React Native New Architecture

Status: Proposed

Date: 2026-07-26

## Decision

Use bare React Native 0.86/current supported patch, TypeScript, Android API 24, and New Architecture. Use small Kotlin TurboModules for identity/biometrics, direct pinned transport, pairing intake, and lifecycle security.

## Rationale

TypeScript shares protocol/reducer logic with relay and existing Hermes conventions. Bare RN permits Android manifest/network/Keystore/Biometric controls. Focused modules minimize native authority.

## Rejected

WebView/PWA (weak lifecycle/device-key/direct pin integration), native-only Kotlin (duplicate portable logic), Expo-managed assumptions (insufficient control without prebuild/eject complexity), and a generic privileged native bridge.
