# Milestone 2: Shared Contracts and Database Foundation

## Objectives

Milestone 2 establishes versioned, language-neutral contracts and an
authoritative PostgreSQL schema without implementing application services,
authentication, desktop UI, broker connectivity, market feeds, strategies, or
live order placement.

## Files

The exact 83-file repository contract includes four ADRs, three versioned JSON
schemas, four fixture documents, SQLAlchemy metadata and its immutable 0001
snapshot, Alembic configuration and migration, a gated development seed, 29
executable tests, database entity-map documentation, and supporting Make and CI
configuration.

## Commands

The acceptance entry points are:

```sh
make bootstrap
make contracts-check
make database-migrate
make database-seed
make database-test
make verify
make acceptance
make stack-down
make stack-up
make stack-health
```

Local CI/security equivalents additionally ran actionlint, Gitleaks, Trivy,
OSV-Scanner, and Syft through reviewed container images.

## Tests

Mandatory coverage includes schema serialization and validation, immutable-v1
compatibility, event envelopes, empty database upgrade, downgrade, repeated
upgrade, exact entity presence, constraints, decimal precision, UTC timestamps,
invalid states, secret-column exclusion, development seeds, repository
boundaries, security scans, and Docker restart recovery.

## Results

- Toolchain doctor and locked installation: PASS.
- Ruff formatting/linting and strict mypy: PASS for 10 Python files.
- Contract and repository tests: PASS, 20 tests.
- PostgreSQL migration and constraint tests: PASS, 9 tests.
- Empty upgrade, downgrade, repeated upgrade, and seed idempotence: PASS.
- Exact repository contract: PASS, 83 files.
- Pre-commit: PASS, including JSON, TOML, YAML, Markdown, secrets, keys,
  shell, and Compose validation.
- Local actionlint, Gitleaks, Trivy, and OSV checks: PASS with no findings.
- SPDX JSON SBOM generation: PASS.
- Six-service Compose health: PASS.
- Clean teardown, restart, migration-version recovery, seed-data persistence,
  and Redis recovery: PASS.

## Known issues

Hosted GitHub Actions have not executed for this branch. CODEOWNERS identity
still requires hosting-organization verification, and action references remain
release tags rather than immutable commit SHAs. The PostgreSQL CI service uses
trust authentication only inside its disposable runner because committed test
credentials are prohibited.

## Security

Contracts and seeds contain only synthetic structural data. Credentials and
secrets are excluded from domain tables; the session model stores only a
non-reversible token fingerprint. Audit rows reject update, delete, and
truncate. Existing fatal secret, vulnerability, dependency, and repository
checks remain enabled.

## Acceptance

Milestone 2 local status is **ACCEPTED**. All mandatory local checks passed.
Hosted workflow execution remains publication evidence, not authorization for
Milestone 3.

## Next milestone

Milestone 3 remains unauthorized. No Milestone 3 source or integration may be
created as part of this work.
