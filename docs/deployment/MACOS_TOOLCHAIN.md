# macOS Toolchain

## Objectives

Define how the authorized Milestone 3 macOS shell is built and verified. The
desktop uses Tauri 2, Rust, React, TypeScript, and Vite. Python 3.12+ FastAPI
remains a separately started server stack and is not embedded in the desktop
lifecycle.

## Toolchain policy

Milestone 3 baseline:

- macOS 13 or newer with full Xcode; Apple Silicon is primary.
- Node.js 24 with npm.
- Rust and Cargo dependencies are resolved by the committed Cargo lockfile.
- Tauri 2, React, TypeScript, Vite, and npm dependencies are locked.
- Python 3.12+ and FastAPI are resolved separately for the backend.

Apple signing, hardened runtime, entitlements, notarization, update signatures,
and disk-image packaging require a later release milestone. Milestone 3 builds
the unsigned `.app` target only; it makes no release-distribution claim.

## Files

- `apps/macos-desktop/` contains the React/Vite client and Tauri/Rust shell.
- `docs/architecture/SYSTEM_CONTEXT.md` separates desktop and server.
- `docs/security/FOUNDATION.md` defines native capability constraints.
- `package-lock.json` and `src-tauri/Cargo.lock` lock desktop dependencies.
- Tauri capabilities permit only core window behavior and deep-link handling;
  native commands expose bounded Keychain and validated OIDC launch operations.
- `.github/workflows/foundation.yml` checks authorized frontend, backend, Rust,
  and unsigned app builds but has no signing, notarization, DMG, or updater job.

## Commands

Inventory and validation commands:

```sh
sw_vers
xcode-select --print-path
clang --version
node --version
npm --version
rustc --version
cargo --version
python3 --version
make frontend-test
make desktop-build
make rust-test
```

Inventory commands report local state only. Validation commands type-check and
test the client, build the Vite and unsigned `.app` targets, and run Rust
formatting, Clippy, and unit tests. Do not sign, notarize, package a DMG, or
configure an updater.

## Tests

- Vite unit and production-build tests.
- Rust formatting, linting, unit, and capability tests.
- FastAPI tests on server runners independent from macOS desktop jobs.
- Callback parsing, exact API-envelope, reconnect, Keychain boundary, and OIDC
  URL-validation tests.
- Signing, notarization, DMG, update, and clean-install tests remain excluded.

## Results

- Focused Vite/TypeScript and Rust suites and unsigned app build: PASS during
  implementation.
- Final full Milestone 3 acceptance: PENDING.
- Signing, notarization, DMG, and updater validation: NOT AUTHORIZED.

## Known issues

- The configured minimum is macOS 13; broader architecture validation remains
  pending.
- Apple Developer team, certificate custody, and notarization credentials are
  not assigned.
- Universal binary and cross-architecture test strategy is open.
- Update framework, rollback behavior, and release channels are outside
  Milestone 3.

## Security

Tauri must use a deny-by-default capability model. Native commands require
specific schemas, path validation, authorization where applicable, and tests.
Do not enable generic shell execution, unrestricted filesystem access, or broad
network allowlists. Frontend content security policy must prohibit unsafe
sources unless narrowly justified.

Signing credentials must reside in an approved secret system and be exposed
only to protected release contexts. Pull requests must never receive them.
The FastAPI server uses its own runtime, credentials, release process, and
availability controls; desktop termination must not affect it.

## Acceptance

- Implemented tools and deferred release work are distinguished.
- The unsigned `.app` build is not represented as distributable packaging.
- Server independence is explicit.
- Signing and native capability risks are recorded.
- Focused build evidence is not represented as final acceptance.

This document does not authorize release packaging.

## Next milestone

Milestone 4 is not authorized. Keep signing, notarization, DMG, updater, broker,
market, strategy, order, execution, risk, reconciliation, and AI work deferred
until separately approved.
