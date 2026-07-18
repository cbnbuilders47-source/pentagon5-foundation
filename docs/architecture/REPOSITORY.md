# Repository Architecture

## Objectives

Record the accepted foundation through the authorized Milestone 3 runtime,
authentication, API, and macOS desktop boundaries.

## Current layout

Milestones 1 and 2 established governance, shared contracts, and the PostgreSQL
model. Milestone 3 adds bounded runtime source and tests:

```text
.
├── .github/
│   ├── CODEOWNERS
│   ├── dependabot.yml
│   └── workflows/
│       ├── foundation.yml
│       └── security.yml
├── root governance, tool, and environment-example files
├── docker-compose.yml
├── apps/macos-desktop/ Tauri, Rust, React, TypeScript, and Vite shell
├── backend/ shared Python runtime controls
├── services/ authentication and API gateway factories plus excluded boundaries
├── packages/ versioned contracts, fixtures, and TypeScript API client
├── infrastructure/ migrations, Compose, monitoring, and deployment
├── tests/ contract, runtime, security, and database checks
└── docs/ architecture, API, deployment, operations, security, and testing
```

The exact current file set remains fail-closed in the repository-contract CI
job. Authentication and gateway are independent FastAPI process factories; the
desktop consumes their stable contracts and does not supervise either process.

## Excluded layout

The README-only broker, market-data, strategy, order-router, execution, risk,
reconciliation, reporting, notification, admin-console, and AI boundaries have
no authorized runtime. Milestone 4, signing, notarization, DMG packaging, and
updater work are also excluded.

## Files

- `.github/CODEOWNERS` establishes review ownership, subject to owner validation.
- `.github/dependabot.yml` covers GitHub Actions and Python tooling updates.
- `.github/workflows/foundation.yml` enforces shape and static validation.
- `.github/workflows/security.yml` scans secrets, dependencies, and filesystem
  vulnerabilities and emits an SBOM.
- `.pre-commit-config.yaml` mirrors deterministic local checks.
- Root `README.md`, `SECURITY.md`, `Makefile`, and `pyproject.toml` define the
  foundation's operator, policy, automation, and Python quality contracts.
- `docker-compose.yml` defines six dependency/observability services plus
  independent authentication and API gateway containers.
- `backend/` owns strict shared configuration, logging, security, database,
  envelope, UUIDv7, metrics, tracing, and request controls.
- `services/authentication/` owns OIDC, opaque sessions, devices, and global
  RBAC; `services/api-gateway/` owns the desktop-facing process factory.
- `apps/macos-desktop/` and `packages/api-client/` own the minimal native client.
- README-only excluded boundaries do not contain runtime source.
- `packages/shared-types/` and `packages/event-contracts/` own immutable v1
  schemas; `packages/test-fixtures/` owns synthetic compatibility fixtures.
- `packages/auth-contracts/` owns separate versioned authentication schemas.
- `infrastructure/database/` owns current metadata, migrations `0001` and
  `0002`, and development-only seeds.
- `docs/` contains the architecture, security, deployment, testing, and
  operations records required by the Milestone 1 gate.

The root `.env.example` is a safe development template; no root `.env` or
credential is included.

## Commands

```sh
pre-commit install --install-hooks
pre-commit run --all-files --show-diff-on-failure
```

Repository shape is also checked by the `Repository contract` CI job. Use Git
commands only within this repository when reviewing the change.

## Tests

- Every required file exists and is non-empty.
- Every document contains the nine required evidence sections.
- YAML and TOML parse without errors.
- Markdown passes markdownlint.
- Tracked shell scripts pass ShellCheck when such scripts exist.
- Compose configuration and health are checked against `docker-compose.yml`.
- Python, TypeScript, React, Rust, and independent factory tests cover the
  authorized runtime.

## Results

- Milestone 1 and 2 evidence remains recorded in their historical documents.
- Focused Milestone 3 Python, contract, TypeScript, and Rust suites: PASS during
  implementation.
- Final full Milestone 3 acceptance: PENDING.

## Known issues

- The CODEOWNERS team name must be verified against the eventual GitHub
  organization before branch protection requires it.
- Action references use reviewed release tags rather than immutable commit
  hashes; pinning exact digests is a follow-up supply-chain hardening task.
- Contract generation remains manual; runtime validators must stay aligned with
  the canonical JSON Schemas.

## Security

Repository policy follows least privilege: default workflow permission is
`contents: read`, checkout credentials are not persisted, and pull-request
permission is granted only to dependency review. CI must fail on validation or
scanner findings; it must not suppress failures with unconditional success.

Generated files, lockfiles, and third-party actions require review. Secrets,
credentials, private keys, personal data, and production configuration must
never be committed.

## Acceptance

- The accepted Milestone 1 baseline remains present.
- Milestone 2 contracts remain immutable and migration `0002` is additive.
- Implemented and excluded runtime boundaries are clearly distinguished.
- Desktop and backend lifecycle independence is tested.
- Static and security workflows have explicit timeouts and minimal permissions.
- Results do not claim execution that did not occur.

Final acceptance is not complete until the full Milestone 3 gate passes.

## Next milestone

Milestone 4 is not authorized. Broker, market, strategy, order, execution, risk,
reconciliation, AI, signing, notarization, DMG, and updater work require a
separate scope decision.
