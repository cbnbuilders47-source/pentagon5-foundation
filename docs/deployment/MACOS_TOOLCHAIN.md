# macOS Toolchain

## Objectives

Define how future macOS desktop tooling will be selected and verified without
installing or claiming an application in Milestone 1. The approved desktop
stack is Tauri 2, Rust, React, TypeScript, and Vite. Python 3.12+ FastAPI is a
separate server stack and is not embedded into the desktop lifecycle.

## Toolchain policy

Approved foundation baseline:

- macOS 13 or newer with full Xcode; Apple Silicon is primary.
- Node.js 24 with npm.
- Current stable Rust during Milestone 1; Milestone 2 must add a
  repository-controlled Rust toolchain file.
- Tauri 2 CLI, React, TypeScript, and JavaScript API versions through lockfiles.
- Python 3.12+; FastAPI dependencies arrive with the independent server.

Apple signing, hardened runtime, entitlements, notarization, update signatures,
and disk-image packaging require a later release milestone. No app or DMG job
is valid before source, identity, and artifact requirements exist.

## Files

- `docs/deployment/MACOS_TOOLCHAIN.md` records policy only.
- `docs/architecture/SYSTEM_CONTEXT.md` separates desktop and server.
- `docs/security/FOUNDATION.md` defines native capability constraints.
- `.github/workflows/foundation.yml` intentionally has no Node, Rust, Tauri,
  frontend, backend, app, or DMG build jobs.

No toolchain pin, entitlement, icon, app metadata, package manifest, lockfile,
or signing configuration is created in Milestone 1.

## Commands

Inventory commands for a future authorized setup:

```sh
sw_vers
xcode-select --print-path
clang --version
node --version
npm --version
rustc --version
cargo --version
python3 --version
```

These commands report local state only. They do not establish the project's
supported matrix. Do not run Tauri scaffolding, package initialization, app
build, signing, notarization, or DMG creation under Milestone 1.

## Tests

Current:

- Markdown and required-section validation.
- Review that no premature desktop, server, app, or packaging job exists.

Future:

- Vite unit and production-build tests.
- Rust formatting, linting, unit, and capability tests.
- Tauri integration tests on the oldest supported macOS version.
- FastAPI tests on server runners independent from macOS desktop jobs.
- Entitlement, hardened-runtime, signature, notarization, and update checks.
- Clean-machine installation and uninstall tests.

## Results

- macOS inventory and foundation toolchain doctor: PASS.
- Vite/Tauri, Rust, and FastAPI project checks: NOT APPLICABLE to Milestone 1;
  no product source or manifests exist.
- Signing, notarization, and DMG validation: NOT APPLICABLE to Milestone 1;
  packaging is not authorized.

## Known issues

- Exact minimum macOS support remains subject to the first compiled Tauri test;
  Apple Silicon is primary and Intel is best-effort.
- Exact Tauri, React, Vite, FastAPI, Pydantic, and SQLAlchemy versions remain
  unselected until their package manifests are created.
- Apple Developer team, certificate custody, and notarization credentials are
  not assigned.
- Universal binary and cross-architecture test strategy is open.
- Update framework, rollback behavior, and release channel policy are open.

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

- Planned tools and deferred decisions are distinguished.
- No build or packaging claim is made without source.
- Server independence is explicit.
- Signing and native capability risks are recorded.
- Foundation toolchain evidence is recorded without claiming a product build.

This document is not authorization to scaffold the toolchain.

## Next milestone

Following an explicit Milestone 2 gate, approve a version matrix and create the
smallest source skeletons with lockfiles and executable checks. Add CI jobs only
alongside the source they validate. Keep signing, notarization, and DMG work
deferred until a separately approved release milestone.
