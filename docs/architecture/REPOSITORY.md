# Repository Architecture

## Objectives

Record the Milestone 1 repository contract and a non-binding future layout
without creating premature source boundaries. The repository begins as a clean
foundation: no previous code was copied, adapted, imported, or reused.

## Current layout

Milestone 1 owns the complete 58-file foundation contract:

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
├── apps/, services/, and packages/ ownership boundaries
├── infrastructure/ dependency, monitoring, and deployment foundations
├── tests/ ownership placeholders
└── docs/ architecture, API, deployment, operations, security, and testing
```

This shape is intentionally foundation-only. Root policy, placeholder
boundaries, local dependency infrastructure, health scripts, monitoring
configuration, and test placeholders are all approved Milestone 1 work.

## Future layout

After a separate Milestone 2 authorization, a proposal may introduce clearly
owned areas such as:

```text
apps/
  desktop/       # Future Tauri 2/Rust/React/TypeScript/Vite client
services/
  api/           # Future Python 3.12+ FastAPI server
packages/
  contracts/     # Generated or language-neutral API contracts
```

The proposal is not permission to create those paths. Their exact names,
workspace tooling, packaging, and ownership require review at the gate.

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

- Repository shape validation: PASS; the exact 58-file contract has no extras.
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

- All 58 authorized Milestone 1 files exist with no extras.
- Current and future layouts are clearly distinguished.
- No backend, frontend, Rust, app, or DMG build job exists before source.
- Static and security workflows have explicit timeouts and minimal permissions.
- Results do not claim execution that did not occur.

Passing these checks closes only the documentation-and-controls gate. It does
not authorize source creation.

## Next milestone

An authorized Milestone 2 design must decide workspace layout, dependency
managers, lockfile policy, API contract ownership, and the independent server
deployment model before source paths are created. Vite/Tauri and FastAPI jobs
may be added only with the corresponding source and executable tests.
