# Repository Architecture

## Objectives

Record the accepted Milestone 1 baseline and the authorized Milestone 2
contract/database layout without creating application source boundaries.

## Current layout

Milestone 1 established a 58-file baseline. Milestone 2 adds only versioned
contract, migration, fixture, test, decision, and evidence artifacts:

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
├── apps/ and services/ documentation-only ownership boundaries
├── packages/ versioned shared contract schemas and fixtures
├── infrastructure/ migrations, dependencies, monitoring, and deployment
├── tests/ executable contract and database checks
└── docs/ architecture, API, deployment, operations, security, and testing
```

The exact current file set remains fail-closed in the repository-contract CI
job. No service or application process is introduced.

## Future layout

After a separate future authorization, a proposal may introduce clearly owned
application areas such as:

```text
apps/
  desktop/       # Future Tauri 2/Rust/React/TypeScript/Vite client
services/
  api/           # Future Python 3.12+ FastAPI server
packages/
  shared-types/  # Existing language-neutral Milestone 2 contracts
```

The proposal is not permission to create application source. Workspace tooling,
packaging, and service ownership require a later gate.

## Files

- `.github/CODEOWNERS` establishes review ownership, subject to owner validation.
- `.github/dependabot.yml` covers GitHub Actions and Python tooling updates.
- `.github/workflows/foundation.yml` enforces shape and static validation.
- `.github/workflows/security.yml` scans secrets, dependencies, and filesystem
  vulnerabilities and emits an SBOM.
- `.pre-commit-config.yaml` mirrors deterministic local checks.
- Root `README.md`, `SECURITY.md`, `Makefile`, and `pyproject.toml` define the
  foundation's operator, policy, automation, and Python quality contracts.
- `docker-compose.yml` and `infrastructure/` define the six local dependencies,
  health tooling, observability configuration, and ownership boundaries.
- Boundary READMEs assign future ownership without introducing runtime source.
- `packages/shared-types/` and `packages/event-contracts/` own immutable v1
  schemas; `packages/test-fixtures/` owns synthetic compatibility fixtures.
- `infrastructure/database/` owns current metadata, migrations, and
  development-only seeds.
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

## Results

- Repository shape validation: PASS; the exact 83-file contract has no extras.
- Pre-commit validation: PASS.
- Local equivalent of GitHub-hosted CI: PASS; hosted execution is pending.
- Application build/test: NOT APPLICABLE to Milestone 1; no application source
  exists or is authorized.
- Compose configuration, health, teardown, and restart recovery: PASS.

## Known issues

- The CODEOWNERS team name must be verified against the eventual GitHub
  organization before branch protection requires it.
- Action references use reviewed release tags rather than immutable commit
  hashes; pinning exact digests is a follow-up supply-chain hardening task.
- The future monorepo package manager and contract generation approach are open.

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
- Every Milestone 2 file is enumerated by the fail-closed repository contract.
- Current and future layouts are clearly distinguished.
- No backend, frontend, Rust, app, or DMG build job exists before source.
- Static and security workflows have explicit timeouts and minimal permissions.
- Results do not claim execution that did not occur.

Passing these checks closes only the shared-contract and database-foundation
gate. It does not authorize application source.

## Next milestone

Milestone 3 remains unauthorized. Vite/Tauri, FastAPI, authentication, broker,
market-feed, strategy, and order-placement jobs may be added only after a
separate gate with corresponding source and executable tests.
