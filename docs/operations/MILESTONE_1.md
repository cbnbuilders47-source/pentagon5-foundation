# Milestone 1: Foundation Gate

## Objectives

Milestone 1 creates the complete repository foundation: root governance, local
dependency infrastructure, ownership boundaries, least-privilege CI, security
automation, and architecture/development/test records without product source.

Constraints:

- Work is isolated to this foundation repository.
- No previous code was inspected, copied, referenced, or reused.
- Root governance, Compose, monitoring, health scripts, README-only ownership
  boundaries, and executable foundation contract tests are approved Milestone
  1 deliverables.
- No Rust, frontend, backend, application, trading, authentication, mock
  environment, or DMG implementation is included.
- The future client is Tauri 2/Rust/React/TypeScript/Vite and the future
  independent server is Python 3.12+ FastAPI.
- The server continues independently of the desktop.
- Milestone 2 is unauthorized until an explicit gate decision.

## Files

Created Milestone 1 artifact groups:

- Root governance and environment files: `README.md`, `SECURITY.md`,
  `.gitignore`, `.dockerignore`, `.editorconfig`, `.env.example`,
  `.pre-commit-config.yaml`, `.markdownlint-cli2.jsonc`, `.python-version`,
  `pyproject.toml`, `uv.lock`, and `Makefile`.
- Local infrastructure: `docker-compose.yml`, health/doctor scripts, pinned
  PostgreSQL, Redis, MinIO, OTel, Prometheus, and Grafana configuration.
- README-only ownership boundaries under `apps/`, `services/`, `packages/`,
  and `infrastructure/`.
- Test ownership directories and executable repository invariants under
  `tests/`.
- `.github/CODEOWNERS`
- `.github/dependabot.yml`
- `.github/workflows/foundation.yml`
- `.github/workflows/security.yml`
- `.pre-commit-config.yaml`
- `docs/architecture/SYSTEM_CONTEXT.md`
- `docs/architecture/REPOSITORY.md`
- `docs/security/FOUNDATION.md`
- `docs/deployment/LOCAL_DEVELOPMENT.md`
- `docs/deployment/MACOS_TOOLCHAIN.md`
- `docs/testing/STRATEGY.md`
- `docs/operations/MILESTONE_1.md`

No product runtime source or generated success artifact is part of this
milestone.

## Commands

Local validation:

```sh
make doctor
make bootstrap
make stack-config
make stack-up
make stack-health
make verify
make stack-down
```

Hosted foundation validation:

```text
Foundation validation / Repository contract
Foundation validation / TOML, YAML, Markdown, and shell
Foundation validation / Compose dependency health
```

Hosted security validation:

```text
Foundation security / Secret scan
Foundation security / Vulnerability and misconfiguration scan
Foundation security / Known dependency vulnerabilities
Foundation security / Pull request dependency review
Foundation security / Generate SBOM
```

Do not substitute a desktop or server command: no product runtime source is
authorized or present.

## Tests

| Evidence | Expected behavior | Acceptance result |
| --- | --- | --- |
| Repository contract | Exact required tree, no extra files | PASS: 58 files |
| Documentation contract | Milestone evidence has nine sections | PASS |
| YAML | Parse all YAML documents | PASS: 7 files |
| TOML | Parse all TOML documents | PASS: 1 file |
| Markdown | markdownlint checks every document | PASS |
| Shell | Bash parses infrastructure scripts | PASS |
| Compose config | Validate the single reviewed definition | PASS |
| Dependency health | Start dependencies and require healthy containers | PASS |
| Secret scan | detect-secrets and Gitleaks scan source | PASS |
| Vulnerability scan | Trivy fails on high/critical findings | PASS |
| Dependency scan | OSV scans locked dependencies | PASS |
| SBOM | Generate SPDX JSON | PASS |
| Desktop/server runtime | Exercise independent processes | NOT APPLICABLE |

The Compose definition was validated, started, stopped, restarted, and checked
for health locally. Named volumes survived clean teardown and recovery.

## Results

Runtime acceptance evidence, 2026-07-18 on macOS:

- Exact repository contract: PASS, 58 required files and no extras.
- Milestone evidence contract: PASS, all 9 required headings.
- YAML parsing: PASS, 7 files.
- TOML parsing: PASS, 1 file.
- Bash syntax validation: PASS for both infrastructure scripts.
- Private `.env` creation from `.env.example`: PASS; generated file is ignored
  and contains local development values only.
- Targeted credential-pattern and non-loopback Compose binding scan: PASS, no
  matches.
- Toolchain doctor and locked dependency sync: PASS.
- Compose configuration and six dependency health checks: PASS.
- PostgreSQL 17.2 connectivity and Redis read/write connectivity: PASS.
- Database migrations: NOT APPLICABLE; Milestone 1 defines no migration or
  initialization script.
- Pre-commit, Ruff formatting/linting, mypy, and four pytest contract tests:
  PASS.
- Frontend and Rust project checks: NOT APPLICABLE; Milestone 1 intentionally
  contains no product manifest or source.
- Actionlint, Gitleaks, Trivy, OSV, and SPDX SBOM generation: PASS locally.
- Clean stop and cached-image restart with all six services healthy: PASS.
- Hosted GitHub Actions execution: NOT RUN locally; equivalent checks passed.
- The first multi-image pull was slow and its concurrent Compose start was
  interrupted after four containers remained in `Created`. Direct starts
  recovered the first run; the clean stop/restart test then passed normally
  through the repository-defined command.

## Known issues

1. The repository contract is exactly 58 newly created Milestone 1 files,
   including `uv.lock`, `.python-version`, `.markdownlint-cli2.jsonc`, and
   executable foundation contract tests.
2. The CODEOWNERS team identifier requires validation in the hosting
   organization before required-review enforcement.
3. Workflow actions use release tags; immutable commit pinning remains a
   supply-chain hardening action.
4. GitHub dependency review may require Dependency Graph availability.
5. Hosted workflows still require execution after the repository is published.
6. Apple signing, notarization, and production deployment choices remain future
   gated decisions.

## Security

Workflow defaults are `contents: read`. Checkout credentials are not persisted.
The dependency-review job alone receives `pull-requests: read`; no workflow has
repository write, package write, deployment, identity-token, or security-event
write permission.

Validation and scanner commands preserve failures. Dependency runtime checks
require declared health checks and fail if any started container is absent,
stopped, unhealthy, or has no health status. Missing runtime inputs are
reported as BLOCKED, not silently described as passing.

The future desktop is an untrusted API client. The future FastAPI server owns
authorization and continues independently if Vite/Tauri is closed, uninstalled,
offline, or faulty. Secrets do not belong in repository files, Vite bundles,
desktop-managed processes, CI logs, or untrusted pull-request contexts.

## Acceptance

Milestone status: **ACCEPTED** for the local Milestone 1 runtime gate.

- [x] Exact 58-file repository tree exists and ownership boundaries are
  documented.
- [x] `make doctor` validates the full required toolchain.
- [x] Root TOML, YAML, and shell files parse.
- [x] `docker compose config` succeeds using `.env.example`.
- [x] PostgreSQL, Redis, MinIO, OTel, Prometheus, and Grafana start and become
  healthy.
- [x] Compose host bindings are loopback-only and the targeted credential scan
  found no secret-shaped assignment.
- [x] `make verify` and all pre-commit hooks pass.
- [x] Local equivalents of foundation and security workflows pass.
- [x] Local setup, macOS toolchain, security, testing, operations, and
  repository documentation exist.
- [x] Commands, results, known issues, security considerations, status, and
  next-milestone gate are recorded.
- [x] Milestone 2 remains unauthorized.

Publishing and hosted workflow execution remain operational follow-up work;
they do not authorize Milestone 2.

## Next milestone

Milestone 2 remains unauthorized. A gate request must identify approvers,
decisions, scope, acceptance tests, and rollback boundaries. Candidate scope is
limited to:

- A versioned API contract.
- An independently runnable Python 3.12+ FastAPI skeleton with health and
  lifecycle tests.
- A minimal Tauri 2/Rust/React/TypeScript/Vite client that consumes the
  contract.
- Reviewed dependency definitions and health checks.
- Locked toolchains and dependencies.

Do not scaffold, add jobs, or create source for those items until the gate is
explicitly approved.
