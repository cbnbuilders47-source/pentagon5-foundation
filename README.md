# Pentagon5 Foundation

This repository contains the accepted Milestone 1 foundation and the authorized
Milestone 2 shared-contract and PostgreSQL database foundation.

## Current scope

- No trading functionality is implemented.
- No authentication functionality is implemented.
- No mock services or mock applications are implemented.
- No desktop, web, or backend application is implemented.
- No real broker, market-feed, strategy, authentication, or order-placement
  integration is implemented.
- Every service is intended to remain independently deployable and operable; boundaries must not depend on another service's process or local filesystem.

`packages/shared-types`, `packages/event-contracts`, and
`packages/test-fixtures` contain language-neutral contract artifacts. Other
application, service, and package boundaries remain **NOT IMPLEMENTED**.

## Approved future stack

The approved future stack is documented here for repository orientation only:

- macOS desktop: Tauri 2, Rust, React, TypeScript, and Vite
- admin console: TypeScript and React
- backend services: Python 3.12+ and FastAPI
- data and messaging: PostgreSQL, Redis, and event contracts
- local infrastructure: Docker Compose, PostgreSQL, Redis, MinIO, OpenTelemetry,
  Prometheus, and Grafana
- future cloud delivery: containerized, independently operated server services

No product application is implemented. Local dependency infrastructure,
versioned contracts, and database migrations exist for structural validation.

## Repository map

- `apps/` — future user-facing applications
- `services/` — future independently operated backend services
- `packages/` — versioned shared contracts and future shared libraries
- `infrastructure/` — database migrations, monitoring, and deployment boundaries
- `docs/api/` — contract catalog and API error-model documentation
- `tests/` — contract, database, security, and end-to-end boundaries

## Setup command overview

The repository-defined validation commands are:

```sh
make doctor
make bootstrap
make stack-config
make contracts-check
make database-test
make database-migrate
make database-seed
make stack-up
make stack-health
make verify
make acceptance
make stack-down
```

`.env.example` contains development-only local dependency settings. It contains
no broker, exchange, Apple signing, or production credential.
