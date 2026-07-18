# Pentagon5 Foundation

This repository contains the Milestone 1 foundation, Milestone 2 shared
contracts and PostgreSQL model, and the authorized Milestone 3 runtime and
macOS desktop foundation.

## Current scope

- Shared Python runtime controls and independent authentication and API gateway
  FastAPI factories are implemented.
- Authentication provides OIDC Authorization Code with PKCE, a one-time native
  login grant, opaque fingerprinted sessions, device revocation, and global
  role-based access control (RBAC).
- The accepted HTTP and ticketed WebSocket surface is limited to system health,
  authentication, sessions, devices, and the `system.health` and
  `session.events` channels.
- A constrained TypeScript API client and minimal Tauri 2 macOS Keychain shell
  consume that surface. The desktop does not own or supervise the backend.
- Broker, market-data, strategy, order, execution, risk, reconciliation, and AI
  runtimes are not implemented.

Authentication contracts are versioned separately in
`packages/auth-contracts`. Migration `0002_identity_authentication` adds only
OIDC identities, transient flows, one-time grants, WebSocket tickets, and
session events. Other documented application and service boundaries remain
unimplemented.

## Implemented stack

- macOS shell: Tauri 2, Rust, React, TypeScript, Vite, and macOS Keychain.
- Backend: Python 3.12+, FastAPI, PostgreSQL, Prometheus metrics, and optional
  OpenTelemetry export.
- Local Compose: PostgreSQL, Redis, MinIO, OpenTelemetry Collector, Prometheus,
  Grafana, authentication, and API gateway services.
- Contracts: shared event envelopes plus separate authentication schemas.

## Repository map

- `apps/macos-desktop/` — minimal native authentication and health shell
- `services/authentication/` — OIDC, sessions, devices, and global RBAC
- `services/api-gateway/` — independent desktop-facing FastAPI factory
- `backend/` — shared runtime configuration, security, and observability
- `packages/` — versioned contracts, fixtures, and TypeScript API client
- `infrastructure/` — database migrations, monitoring, and deployment boundaries
- `docs/api/` — contract catalog and API error-model documentation
- `tests/` — contract, database, security, and end-to-end boundaries

## Setup command overview

The repository-defined validation commands are:

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

Focused Python, contract, TypeScript, and Rust suites passed during Milestone 3
implementation. Final full `make acceptance` evidence is pending and must not be
inferred from those focused runs.

`.env.example` contains development-only settings and no production credential.
Milestone 4, signing, notarization, DMG packaging, updater work, and all excluded
trading runtimes remain unauthorized.
