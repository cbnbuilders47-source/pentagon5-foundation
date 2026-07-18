# Local Development

## Objectives

Provide a reproducible Milestone 1 validation path for repository checks and
local dependency infrastructure without inventing an application runtime.

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
- `docker-compose.yml` defines the six local dependencies.
- `infrastructure/scripts/doctor.sh` validates the full foundation toolchain.
- `infrastructure/scripts/stack-health.sh` verifies running dependency health.
- `.github/workflows/foundation.yml` is the hosted validation source of truth.
- `.github/workflows/security.yml` defines hosted security evidence.
- `docs/operations/MILESTONE_1.md` records actual execution results.
- `.env.example` contains development-only defaults. A copied `.env` is local,
  private, and ignored.

## Commands

From the repository root:

```sh
make doctor
make bootstrap
make stack-config
make stack-up
make stack-health
make verify
make stack-down
```

`make stack-down` preserves named development volumes. Destructive volume
removal requires a separate explicit operator action.

## Tests

- Run all pre-commit hooks against all tracked files.
- Confirm changed documents contain all required evidence headings.
- Confirm no unauthorized product source was introduced.
- Review workflow permissions and timeout limits.
- Validate Compose rendering before starting dependencies and require every
  started dependency to report a declared healthy state.

## Results

- Toolchain doctor and developer bootstrap: PASS.
- Local pre-commit: PASS on every repository file.
- Local secret, vulnerability, dependency, workflow, and SBOM checks: PASS.
- Dependency configuration, startup, health, teardown, and restart: PASS.
- Desktop and server startup: NOT APPLICABLE to Milestone 1; no product source
  exists or is authorized.

## Known issues

- Installation method varies across macOS environments.
- Pre-commit downloads third-party hook environments on first run.
- There is no application configuration schema.
- Dependency defaults are development-only and must not be promoted to
  production configuration.
- No local server URL, desktop dev URL, or API contract exists.

## Security

Use a dedicated development environment. Never put credentials in repository
files, command arguments, Vite variables, terminal transcripts, or Compose
files. Review hook updates before installation. Docker services must bind only
to required interfaces, use non-default credentials supplied outside version
control, and avoid privileged mode.

The future FastAPI server is started and operated independently. A future Tauri
desktop may connect to it, but must not silently install, own, or terminate it.

## Acceptance

- A developer can identify and run every current static check.
- Out-of-scope runtime components are reported as NOT APPLICABLE.
- Instructions do not require files outside the authorized repository.
- Instructions do not create unauthorized product source.
- Future dependency cleanup is explicit and removes transient volumes.

Local validation alone does not approve Milestone 2.

## Next milestone

After explicit authorization, add versioned contracts, database migrations, a
Python 3.12+ FastAPI foundation, and the Tauri 2/Rust/React/TypeScript/Vite
shell with lockfiles and separate server/desktop startup commands. The FastAPI
command must work without the desktop running; that independence becomes an
acceptance test.
