# Milestone 3: Runtime and macOS Desktop Foundation

## Objectives

Milestone 3 implements authentication and authorization foundations, independent
FastAPI process skeletons, an API gateway, contract-driven REST and WebSocket
transport, strict runtime configuration, observability, health endpoints, and a
minimal Tauri 2 macOS desktop shell.

Broker integration, market feeds, strategies, order execution, risk
calculations, reconciliation behavior, AI, signing, notarization, DMG packaging,
and Milestone 4 work remain excluded.

## Files

- `backend/` contains shared Python runtime controls.
- `services/authentication/` owns OIDC, sessions, devices, and global RBAC.
- `services/api-gateway/` owns the desktop-facing process factory.
- `packages/auth-contracts/` contains separate versioned authentication schemas.
- `packages/api-client/` validates REST and WebSocket envelopes, creates
  ticketed connections, and reconnects with fresh tickets.
- `apps/macos-desktop/` contains the React, Vite, Tauri, Rust, deep-link, and
  macOS Keychain shell without backend process ownership.
- Migration `0002_identity_authentication` adds OIDC identities, encrypted
  transient flows/grants, fingerprinted tickets, and session events only.
- Docker Compose runs six dependency/observability services plus independent
  authentication and gateway containers.
- The accepted route surface is limited to health, OIDC, session, logout,
  devices, WebSocket tickets, and the `system.health` and `session.events`
  channels.

## Commands

```sh
make bootstrap
make contracts-check
make runtime-test
make database-test
make frontend-test
make desktop-build
make rust-test
make stack-up
make stack-health
make verify
make acceptance
```

## Tests

- Strict Python formatting, linting, typing, unit, contract, and PostgreSQL tests.
- OIDC PKCE, state, nonce, issuer, audience, replay, expiry, and grant tests.
- Default-deny global RBAC, HMAC token fingerprints, exact CORS, body limit,
  timeout, safe logging, UUIDv7, health, metrics, tracing configuration,
  error-envelope, and WebSocket tests.
- TypeScript API-shape, callback, envelope, reconnect, and React state tests.
- Rust URL validation, Keychain command boundary, formatting, Clippy, and tests.
- Compose configuration, service health, backend independence, and restart tests.

## Results

- `make verify`: PASS.
- `make acceptance`: PASS.
- Python unit, contract, and security tests: 57 passed.
- PostgreSQL migration and integration tests: 9 passed.
- API client tests: 10 passed; typecheck and production build passed.
- Desktop React tests: 8 passed; typecheck and Vite production build passed.
- Tauri Rust tests: 4 passed; formatting and Clippy with denied warnings passed.
- Eight Compose services became healthy; only the gateway publishes an
  application port.
- Gateway, authentication, Redis, PostgreSQL-outage, and full-stack restart
  recovery passed with migration `0002_identity_authentication` preserved.
- Gitleaks, Trivy, OSV-Scanner, detect-secrets, private-key, and npm-audit checks
  passed; SPDX SBOM generation succeeded. OSV exceptions are documented and
  expire on 2026-10-18.

## Known issues

- A live production OIDC provider and client registration are deployment inputs
  and were not committed.
- The gateway currently uses a documented modular in-process authentication
  surface; network service identity is deferred.
- Apple signing, notarization, installer packaging, updater behavior, and a
  production accessibility review are outside this milestone.

## Security

The desktop stores its opaque session token only in macOS Keychain. The backend
stores HMAC fingerprints rather than plaintext tokens. OIDC and login-grant
transient payloads are authenticated-encrypted, secrets support file indirection,
Tauri capabilities are deny-by-default, and no shell or broad filesystem
capability exists.

## Acceptance

Milestone 3 is accepted only when every inherited Milestone 2 check and every
new Python, database, TypeScript, Rust, Compose, security, lifecycle, and restart
check passes without an unexpected skip or suppressed failure.

All local acceptance criteria passed on 2026-07-18. Hosted GitHub Actions remain
not run locally.

## Next milestone

Milestone 4 is not authorized. This milestone does not authorize trading,
broker, market-data, strategy, execution, risk, AI, signing, notarization, DMG,
updater, or production deployment work.
