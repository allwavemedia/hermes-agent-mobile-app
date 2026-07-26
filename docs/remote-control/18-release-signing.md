# Release and Signing

## MVP distribution

Distribute a signed Android APK through GitHub Releases only after implementation/security gates. Do not publish to Play Store. Every release includes:

- versioned universal or documented ABI APK;
- SHA-256 checksum file;
- CycloneDX/SPDX SBOM;
- build provenance/attestation;
- release notes with protocol compatibility, migration, security and rollback notes;
- link to source commit/tag;
- verification instructions.

## Versioning

App uses SemVer for user release and integer `versionCode`. Protocol compatibility is independent and advertised at runtime. Release tag proposal: `android-remote-v0.1.0`. Pre-release builds use GitHub prerelease tags and distinct application ID suffix so they cannot overwrite production pairing state.

## Signing key lifecycle

Signing key generation is explicitly outside this planning stage. Later:

1. Generate an Android upload/release key in an offline controlled environment using current Android tooling.
2. Store the keystore and passwords as separate GitHub Environment secrets protected by required reviewers; maintain an offline encrypted backup under documented custody.
3. Workflow materializes secrets only in an ephemeral runner directory, masks variables, invokes Gradle without command-line passwords where possible, verifies the signed artifact, then securely cleans workspace.
4. No signing key is stored in repository, artifact cache, logs, PR workflow, fork workflow, or developer debug config.
5. Pull-request CI builds unsigned/debug artifacts only. Release signing runs only from a protected tag/environment after approval.

There are no Android recovery codes or pairing-key backups; APK signing-key custody is a separate software distribution concern.

## Reproducible pipeline

GitHub Actions pins third-party actions by full commit SHA. Workflow:

1. checkout tag with clean tree;
2. setup Node 22 and JDK 17;
3. install npm dependencies with `npm ci`;
4. run schema, TypeScript, Android unit/lint, and integration gates;
5. run Gradle release bundle/APK with dependency verification and locked versions;
6. sign;
7. run `apksigner verify --verbose --print-certs`;
8. inspect package with `aapt2 dump badging` and manifest policy test;
9. install/smoke on API 24 and current emulator;
10. generate checksum, SBOM, provenance, scan;
11. publish immutable GitHub Release only if every gate passes.

Expected signer certificate digest is held in a reviewed repository text file after key generation; workflow compares it. APK signature scheme v2+ is mandatory for API 24+. Debug keys are never accepted in release.

## Update UX

MVP may check the official GitHub Releases API for metadata while the app is open. It does not self-install silently. User sees current/new version, source/release URL, checksum/signature guidance, and Android package installer prompt. Unknown repository/origin, downgrade, changed signer, or incompatible protocol blocks the update recommendation.

## Rollback

GitHub Releases are immutable. Rollback publishes a new higher `versionCode` built from the prior safe source plus compatibility/security fixes; Android does not accept a lower version code as an ordinary update. Server/host feature flags preserve at least the prior protocol minor. Revoking a bad APK release does not revoke paired devices automatically; incident response decides whether trust epochs must change.

## Release approvals

Required evidence:

- all required CI and platform tests;
- security findings resolved/accepted;
- dependency/license/SBOM review;
- macOS/Windows secure-store/startup proof;
- Android physical-device biometric/Keystore/pin proof;
- relay restore/expiry/zero-retention proof;
- signed APK install/upgrade/rollback rehearsal;
- no production code outside approved implementation PRs.
