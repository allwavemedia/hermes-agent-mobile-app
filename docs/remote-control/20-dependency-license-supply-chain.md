# Dependency, License, and Supply-Chain Audit

Snapshot date: 2026-07-26. Versions are planning candidates verified from current official registries/docs; implementation must rerun resolution/audit and commit exact locks. Hermes’s MIT license remains compatible with the candidates below.

## Proposed direct runtime dependencies

| Component | Candidate | License | Reason / decision |
|---|---:|---|---|
| React Native | 0.86.0 | MIT | Current supported Android New Architecture baseline |
| React | 19.2.8 | MIT | RN peer |
| React Navigation native | 7.3.14 | MIT | Computer/session stacks |
| Native Stack | 7.18.6 | MIT | Native navigation behavior |
| `react-native-screens` | 4.26.2 | MIT | Navigation peer |
| `react-native-safe-area-context` | 5.8.0 | MIT | Navigation peer |
| `nanostores` | 1.4.1 | MIT | Aligns with Hermes shared style; small projections |
| `@nanostores/react` | 1.1.0 | MIT | React binding |
| `ajv` | 8.20.0 | MIT | JSON Schema validation |
| `canonicalize` | 3.0.0 | Apache-2.0 | RFC 8785 Appendix G implementation; avoids security-sensitive custom JSON canonicalization |
| Relay `ws` | 8.21.1 | MIT | Focused WS server/client |
| Relay `pg` | 8.22.0 | MIT | PostgreSQL without ORM |
| `jose` | 6.2.4 | MIT | Standards-based JWS/JWK/JWT for relay/Node adapters and shared-vector tests; not bundled into Android as a WebCrypto assumption |
| Python `rfc8785` | 0.1.4 | Apache-2.0 | Trail of Bits no-dependency JCS implementation; direct member of the opt-in remote-control extra |
| Python `keyring` | 25.7.0 | MIT | Native Windows/macOS secure stores; backend allowlist required |
| Google Code Scanner | 16.1.0 | Google Android SDK terms | No camera permission; manual fallback mandatory |
| AndroidX Biometric | 1.1.0 stable | Apache-2.0 | BiometricPrompt compatibility |
| AndroidX DataStore | 1.2.1 | Apache-2.0 | Public metadata persistence |

Python already directly pins `cryptography==46.0.7` and `websockets==15.0.1`, and already includes `PyJWT[crypto]`; reuse them. `pywin32` is already a Windows dependency. Keep `rfc8785==0.1.4` in the opt-in `remote-control` extra and later add `keyring>=25.7,<26` for host secure storage. The framework-neutral TypeScript package accepts a narrow crypto provider instead of importing `node:crypto` or assuming React Native WebCrypto; Node uses `jose`, and Android uses maintained JCA/Keystore primitives behind `NativeHermesIdentity`. If security/platform testing favors direct `win32crypt` plus macOS Security APIs, ADR-003 must be amended and `keyring` removed.

## Test/development candidates

| Dependency | Candidate | License | Use |
|---|---:|---|---|
| `fast-check` | 4.9.0 | MIT | Protocol/reducer property tests |
| `@testing-library/react-native` | 14.0.1 | MIT | Android component tests |
| Detox | 20.51.4 | MIT | Android E2E |
| PostgreSQL official image | supported major, digest-pinned | PostgreSQL | Integration/Compose |

Do not add Axios, an ORM, Redux, a generic native networking bridge, a custom crypto package, `EncryptedSharedPreferences`, Firebase/FCM, or a QR camera library in MVP. Use platform/standard library where it reduces authority and supply-chain area.

## Existing-code implications

`ajv`, `ws`, and `nanostores` already occur in the monorepo lock graph, but each new workspace declares its own direct imports. Do not rely on hoisting. Root npm workspaces already include `apps/*`, so no workspace glob change is needed. `package-lock.json` and `uv.lock` are authoritative and committed.

## License obligations

- Preserve MIT/Apache/PostgreSQL notices in source distribution and release notices.
- Record Google Code Scanner/Play services terms and data behavior; no camera permission does not mean no Google dependency.
- Generate third-party notices and SBOM for APK, relay image, and Python host environment.
- Reject GPL/AGPL/SSPL or unknown-license runtime additions unless maintainers explicitly approve legal impact.
- Container base images and OS packages are part of the audit, not exempt.

## Supply-chain controls

- npm uses `npm ci`, committed lock, registry allowlist, scripts reviewed, and `npm audit` as signal rather than automatic `audit fix`.
- Python uses `uv sync --frozen` against `uv.lock`; supported Python 3.11–3.13 only.
- Gradle dependency locking and verification metadata; repositories limited to Google/Maven Central; dynamic versions forbidden.
- GitHub Actions pinned to commit SHAs; PR workflows cannot access release secrets.
- Build container bases pinned by digest; generate SBOM and vulnerability scan.
- Dependabot/Renovate-style updates are isolated, tested, and reviewed; security upgrades can exceed planned pins only with lock/SBOM refresh.
- Verify package provenance/maintainer changes and typosquatting before first addition.

## Current environment findings

| Tool | Readiness |
|---|---|
| Git 2.55 / Git LFS 3.7 / GitHub CLI 2.96 | Ready; authenticated as `allwavemedia` |
| Node 24.18 / npm 11.16 | Usable for planning; CI pins Node 22 |
| Python 3.14.6 / uv 0.11.26 | System Python is unsupported for Hermes; uv-managed Python 3.13 environment is ready and used for protocol checks |
| Official Android CLI 1.0.15857036 | Ready at `C:\ProgramData\AndroidCLI\android.exe` |
| JDK/Android Studio/SDK/Gradle/ADB/signing tools | Not found on the current process path; no install or global change made |
| Docker 29.6 / Compose 5.3 | Client ready; daemon stopped |
| Azure CLI 2.88 | Ready and authenticated; no resources created |
| Tailscale | Missing |
| Windows firewall/Defender | Enabled |
| Proxy | WinHTTP direct; no proxy environment found |
| macOS tooling | Not assessable on Windows; runner/device required |

No installation or global configuration was performed during planning. Missing prerequisites are Gate 1 work, not reasons to weaken the architecture.

## Task 3 implementation audit

The 2026-07-26 Task 3 lock review added only:

- runtime `canonicalize@3.0.0` (Apache-2.0, Node >=18 declaration, no transitive dependency);
- development-only `jose@6.2.4` (MIT, no dependencies) for the Node shared-vector adapter;
- opt-in Python `rfc8785==0.1.4` (Apache-2.0, no dependencies).

`uvx pip-audit --local --skip-editable --progress-spinner off` reported no known Python vulnerabilities. The scoped `npm audit --workspace apps/remote-control-protocol --omit=dev` report contains a high PostCSS advisory, but `npm explain postcss` traces the installed copy to pre-existing bootstrap/Desktop/web `@nous-research/ui`/Vite paths, not to the protocol workspace or any Task 3 addition. Full-root audit also reports pre-existing DOMPurify and React Router findings. This slice does not mutate those unrelated dependency trees; they remain repository release-gate findings to remediate separately. No automatic audit fix was run.

## Audit gate

Before merging each implementation slice: exact direct/transitive inventory, license scan, vulnerability scan, maintainer/provenance review, native authority review, lock diff review, SBOM diff, and removal check for unused dependencies. A high/critical exploitable issue blocks release unless patched or the feature/dependency is removed.
