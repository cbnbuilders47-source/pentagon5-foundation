# Testing Strategy

## Objectives

Define honest, layered evidence for the foundation and authorized Milestone 3
runtime. A configured test is not a passed test, skipped work is not success,
and focused suites do not prove full acceptance. Every gate must distinguish
PASS, FAIL, NOT RUN, and BLOCKED.

No tests or implementation were reused from previous code.

## Evidence states

- **PASS**: the recorded command completed successfully for the identified
  revision and environment.
- **FAIL**: the command ran and produced a failing assertion, finding, or tool
  error.
- **NOT RUN**: prerequisites exist but execution has not occurred.
- **BLOCKED**: required source, configuration, service, credential, environment,
  or authorization does not exist.

CI steps must preserve non-zero exit codes. Security and validation gates may
not use `continue-on-error` or equivalent suppression.

## Files

- `.pre-commit-config.yaml` defines local static checks.
- `.github/workflows/foundation.yml` checks shape, docs, TOML, YAML, Markdown,
  shell files, and future Compose dependency health.
- `.github/workflows/security.yml` checks secrets, vulnerabilities, dependency
  changes, manifests, and SBOM generation.
- `docs/operations/MILESTONE_1.md` is the execution evidence record.
- `docs/operations/MILESTONE_2.md` records contract and database evidence.
- `docs/operations/MILESTONE_3.md` records focused runtime evidence and the
  pending final gate.

## Commands

Current local checks:

```sh
make contracts-check
make runtime-test
make database-test
make frontend-test
make desktop-build
make rust-test
make verify
make acceptance
```

Compose dependency gate:

```sh
docker compose -f docker-compose.yml config --quiet
docker compose -f docker-compose.yml up --detach --wait --wait-timeout 120
docker compose -f docker-compose.yml ps
```

These commands validate only checked-in source and locked dependencies.

## Tests

### Milestone 1

1. Repository contract: exact required controls and documents exist.
2. Documentation contract: every document has required evidence sections.
3. Configuration parsing: YAML and any TOML are syntactically valid.
4. Text quality: Markdown, whitespace, line endings, and merge markers.
5. Shell quality: ShellCheck for tracked shell scripts, when present.
6. Compose: validate the existing definition, start its dependencies, and
   inspect every declared container health check.
7. Security: Gitleaks, Trivy, OSV-Scanner, dependency review, and SPDX SBOM.

### Milestone 2

1. JSON Schema draft and reference validation.
2. Valid, invalid, serialization, compatibility, and event-envelope fixtures.
3. Empty-database migration upgrade, downgrade, and repeat upgrade.
4. Foreign-key, uniqueness, state-transition, append-only, and numeric
   precision constraints.
5. UTC timestamp normalization and development-seed idempotence.
6. Repository ownership, security scans, and Docker restart recovery.

### Milestone 3 Python 3.12+ FastAPI runtime

- Independent authentication and gateway factory tests.
- OIDC PKCE, provider validation, replay, grant, session, device, and global
  RBAC tests.
- Strict configuration, secret-file, CORS, body, timeout, safe-log, UUIDv7,
  health, error-envelope, and observability tests.
- Integration tests against disposable dependencies.
- Migration `0002`, readiness, Compose health, lifecycle, and restart tests.

### Milestone 3 Tauri 2/Rust/React/TypeScript/Vite desktop

- Type checks, API-client envelope tests, callback parsing, reconnect behavior,
  React state tests, and production builds.
- Rust formatting, Clippy, URL validation, Keychain command-boundary tests, and
  unsigned `.app` build.
- Accessibility, signing, notarization, DMG, updater, and release tests are not
  authorized.

### Milestone 3 lifecycle

- Contract-driven flows across separately started server and desktop processes.
- Network interruption, expired identity, denied authorization, and server
  upgrade compatibility.
- No test may require the desktop to own or terminate the server.

## Results

- Milestone 1 local YAML, TOML, and Bash parsing: PASS.
- Milestone 1 local foundation and security equivalents: PASS.
- Milestone 1 hosted workflows: NOT RUN.
- Compose validation, health, teardown, and restart recovery: PASS.
- Foundation contract tests: PASS, four tests.
- Milestone 2 contract tests: PASS, 20 tests.
- Milestone 2 migration and database tests: PASS, 9 tests.
- Milestone 2 complete local acceptance and restart recovery: PASS.
- Focused Milestone 3 Python, auth contract, TypeScript, and Rust suites: PASS
  during implementation.
- Final full Milestone 3 `make acceptance`: PENDING.

## Known issues

- No coverage baseline or flaky-test policy is approved.
- No target CI platform matrix beyond `ubuntu-latest` static checks exists.
- Scheduled security scan effectiveness depends on repository and GitHub
  security feature availability.
- Dependency review can require GitHub Dependency Graph availability.
- Runtime performance, resilience, and accessibility targets are undefined.
- A live production OIDC provider and release-distribution tests are outside the
  focused suites.

## Security

Test data must be synthetic and non-sensitive. Test secrets must be short-lived,
least-privileged, and unavailable to pull requests from untrusted contexts.
Assertions should test authorization denial, not only successful authentication.
Logs and artifacts require review for token, path, and personal-data leakage.

Security scanners fail on tool errors and qualifying findings. An SBOM is
retained briefly as a CI artifact and must identify the tested revision.

## Acceptance

- Evidence states are unambiguous.
- Current CI covers every artifact that actually exists.
- Authorized runtime behavior has executable tests.
- Server independence has a named factory and lifecycle test.
- No broker, market, strategy, order, execution, risk, reconciliation, AI,
  signing, notarization, DMG, or updater test claims exist.
- Contract and database tests remain separable from service startup.
- Commands and results are traceable to a revision when execution occurs.

Milestone 1 or 2 acceptance cannot be used to waive the Milestone 3 gate.

## Next milestone

Milestone 4 is not authorized. Any broader service, trading, packaging, or
updater tests require a separate scope decision and must preserve independent
backend lifecycle validation.
