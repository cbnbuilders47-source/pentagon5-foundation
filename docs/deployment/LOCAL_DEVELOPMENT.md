# Local Development

## Objectives

Provide a reproducible validation path for the accepted foundation, versioned
contracts, PostgreSQL migrations, and authorized Milestone 3 backend and macOS
desktop runtime.

No previous application code was reused. All foundation files in this
repository were created for Milestone 1. Do not source configuration from
another checkout.

## Prerequisites

- Git.
- Full Xcode on macOS.
- Node.js 24 and npm.
- Current stable Rust, Cargo, and rustup.
- Python 3.12 or 3.13 with `uv`.
- Docker Desktop with the Compose v2 plugin.
- Network access to install isolated pre-commit hook environments.

Docker is required to execute the local dependency health check.
If the daemon or Compose plugin is unavailable, runtime evidence is BLOCKED; it
must not be represented as a passing health check.

## Files

- `Makefile` and `.pre-commit-config.yaml` are local validation entry points.
- `docker-compose.yml` defines six local dependency/observability services and
  independent authentication and API gateway containers.
- `infrastructure/scripts/doctor.sh` validates the full foundation toolchain.
- `infrastructure/scripts/stack-health.sh` verifies running dependency health.
- `.github/workflows/foundation.yml` is the hosted validation source of truth.
- `.github/workflows/security.yml` defines hosted security evidence.
- `docs/operations/MILESTONE_1.md` records actual execution results.
- `docs/operations/MILESTONE_2.md` records contract and database acceptance.
- `docs/operations/MILESTONE_3.md` records focused runtime results and the
  pending final gate.
- `packages/shared-types/` and `packages/event-contracts/` own JSON schemas.
- `infrastructure/database/` owns SQLAlchemy metadata, Alembic migrations, and
  development-only seeds.
- `backend/`, `services/authentication/`, and `services/api-gateway/` own shared
  runtime controls and independent FastAPI factories.
- `packages/auth-contracts/`, `packages/api-client/`, and
  `apps/macos-desktop/` own the auth schema and constrained native client.
- `.env.example` contains development-only defaults. A copied `.env` is local,
  private, and ignored.

## Commands

From the repository root:

```sh
make doctor
make bootstrap
make stack-config
make secrets-init
make contracts-check
make runtime-test
make database-test
make database-migrate
make database-seed
make stack-up
make stack-health
make frontend-test
make desktop-build
make rust-test
make verify
make acceptance
make stack-down
```

`make stack-down` preserves named development volumes. Destructive volume
removal requires a separate explicit operator action.

`make secrets-init` creates ignored local OIDC-client and session-HMAC secret
files. A reachable development OIDC provider and matching client registration
are still required for an interactive login.

## Tests

- Run all pre-commit hooks against all tracked files.
- Confirm changed documents contain all required evidence headings.
- Confirm authorized identity source remains bounded and excluded runtime
  boundaries remain documentation-only.
- Review workflow permissions and timeout limits.
- Validate Compose rendering before starting dependencies and require every
  started dependency to report a declared healthy state.
- Validate versioned contract fixtures and backward compatibility.
- Upgrade an empty temporary database, downgrade it, upgrade it repeatedly,
  and enforce schema constraints.
- Exercise strict runtime configuration, OIDC PKCE and one-time grants, opaque
  sessions, global RBAC, REST/WebSocket envelopes, API-client validation,
  Keychain command boundaries, and independent backend factories.

## Results

- Historical Milestone 1 and 2 results remain in their evidence documents.
- Focused Milestone 3 Python, contract, TypeScript, and Rust suites: PASS during
  implementation.
- Final `make acceptance`, including Compose lifecycle and restart evidence:
  PENDING.

## Known issues

- Installation method varies across macOS environments.
- Pre-commit downloads third-party hook environments on first run.
- Dependency defaults are development-only and must not be promoted to
  production configuration.
- Interactive OIDC login needs an operator-supplied development provider.
- The gateway currently uses the auth surface in-process; network service
  identity is deferred.

## Security

Use a dedicated development environment. Never put credentials in repository
files, command arguments, Vite variables, terminal transcripts, or Compose
files. Review hook updates before installation. Docker services must bind only
to required interfaces, use non-default credentials supplied outside version
control, and avoid privileged mode.

FastAPI services are started and operated independently. The Tauri desktop
connects to the gateway but does not install, own, restart, or terminate it.
Opaque session tokens and device keys are stored only through macOS Keychain.

## Acceptance

- A developer can identify and run every current static check.
- Authorized runtime checks are distinguished from excluded components.
- Instructions do not require files outside the authorized repository.
- Instructions do not create unauthorized broker, market, strategy, order,
  execution, risk, reconciliation, AI, packaging, or updater source.
- Dependency cleanup preserves named volumes unless explicitly removed.

Full local validation must pass before Milestone 3 acceptance is recorded.

## Next milestone

Milestone 4 is not authorized. Broker, market, strategy, order, execution, risk,
reconciliation, AI, signing, notarization, DMG, and updater work remain outside
these commands.
