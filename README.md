# Pentagon5 Foundation

This repository contains **Milestone 1 only**: the approved repository structure, root configuration, and boundary documentation.

## Current scope

- No trading functionality is implemented.
- No authentication functionality is implemented.
- No mock services or mock applications are implemented.
- No desktop, web, or backend application is implemented.
- Every service is intended to remain independently deployable and operable; boundaries must not depend on another service's process or local filesystem.

All boundary directories currently contain documentation only and are marked **NOT IMPLEMENTED**.

## Approved future stack

The approved future stack is documented here for repository orientation only:

- macOS desktop: Tauri 2, Rust, React, TypeScript, and Vite
- admin console: TypeScript and React
- backend services: Python 3.12+ and FastAPI
- data and messaging: PostgreSQL, Redis, and event contracts
- local infrastructure: Docker Compose, PostgreSQL, Redis, MinIO, OpenTelemetry,
  Prometheus, and Grafana
- future cloud delivery: containerized, independently operated server services

No product application is implemented in Milestone 1. Local dependency
infrastructure and monitoring configuration are included for foundation
validation only.

## Repository map

- `apps/` — future user-facing applications
- `services/` — future independently operated backend services
- `packages/` — future explicitly shared libraries and contracts
- `infrastructure/` — future database, monitoring, and deployment definitions
- `docs/api/` — future API documentation
- `tests/` — reserved test-suite boundaries

## Setup command overview

Milestone 1 requires the toolchain documented by `make doctor`:

```sh
make doctor
make bootstrap
make stack-config
make stack-up
make stack-health
make verify
make stack-down
```

`.env.example` contains development-only local dependency settings. It contains
no broker, exchange, Apple signing, or production credential.
