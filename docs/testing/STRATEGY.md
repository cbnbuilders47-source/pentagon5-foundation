# Testing Strategy

## Objectives

Define honest, layered evidence before product source exists. A configured test
is not a passed test, skipped work is not success, and static checks cannot
prove runtime behavior. Every gate must distinguish PASS, FAIL, NOT RUN, and
BLOCKED.

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

## Commands

Current local check:

```sh
pre-commit run --all-files --show-diff-on-failure
```

Compose dependency gate:

```sh
docker compose -f docker-compose.yml config --quiet
docker compose -f docker-compose.yml up --detach --wait --wait-timeout 120
docker compose -f docker-compose.yml ps
```

Future stack-specific commands must be added only with their manifests, locked
dependencies, source, and assertions.

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

### Future Python 3.12+ FastAPI server

- FastAPI unit tests for business and authorization rules.
- API schema and backward-compatibility tests.
- Integration tests against disposable dependencies.
- Health, readiness, migration, shutdown, and recovery tests.
- Deployment test proving the server continues with no desktop running.

### Future Tauri 2/Rust/React/TypeScript/Vite desktop

- Vite component and state tests.
- Browser-level tests against a controlled API.
- Tauri command schema, permission, and native integration tests.
- macOS accessibility, update, install, and failure-mode tests.

### Future end to end

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
- Server, desktop, end-to-end, and packaging tests: NOT APPLICABLE to
  Milestone 1; their source and artifacts are not authorized.

## Known issues

- No coverage baseline or flaky-test policy is approved.
- No target CI platform matrix beyond `ubuntu-latest` static checks exists.
- Scheduled security scan effectiveness depends on repository and GitHub
  security feature availability.
- Dependency review can require GitHub Dependency Graph availability.
- Runtime performance, resilience, and accessibility targets are undefined.

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
- Runtime tests are deferred rather than simulated.
- Future server independence has a named acceptance test.
- No backend, frontend, Rust, app, or DMG test job exists before source.
- Commands and results are traceable to a revision when execution occurs.

Milestone 1 acceptance cannot be used to waive the Milestone 2 authorization
gate.

## Next milestone

Once authorized, define API contracts and add the smallest executable test for
each new source boundary. Require a FastAPI health test and an independent
server lifecycle test before connecting Vite/Tauri. Establish coverage,
platform, performance, and test-data policies before broad implementation.
