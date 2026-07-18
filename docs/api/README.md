# API Documentation

## Milestone 3 surface

The authentication and API gateway factories expose the same bounded Milestone
3 surface. The gateway is a separate process factory; it currently composes the
authentication surface in-process rather than calling it over the network.

### System and authentication routes

- `GET /v1/system/health/startup`
- `GET /v1/system/health/live`
- `GET /v1/system/health/ready`
- `POST /v1/auth/oidc/start`
- `GET /v1/auth/oidc/callback`
- `POST /v1/auth/oidc/exchange`
- `GET /v1/auth/session`
- `POST /v1/auth/logout`
- `GET /v1/auth/devices`
- `DELETE /v1/auth/devices/{device_id}`
- `POST /v1/auth/ws-tickets`
- `WS /v1/ws/{channel}`

OIDC uses Authorization Code with RFC 7636 S256 PKCE, state, nonce, issuer, and
audience validation. The backend callback redirects to the native custom URI
with only a short-lived, one-time grant code. Exchanging that code returns an
opaque session token; subsequent native requests use `Authorization: Bearer`.

### WebSocket boundary

An authenticated client first requests a short-lived, single-use ticket bound to
either `system.health` or `session.events`. The WebSocket accepts text JSON only,
bounds frame size and subscription count, and accepts `subscribe`,
`unsubscribe`, and `heartbeat` controls. It emits `ack` or `heartbeat`
WebSocket envelopes and a health envelope after a `system.health` subscription.

### Contracts

Authentication request and response bodies are defined separately in
`packages/auth-contracts/schemas/v1/auth.schema.json`. Runtime health, error, and
WebSocket messages use the accepted Milestone 2 envelope:

- `schemaVersion: "1.0.0"`
- UUIDv7 `messageId`
- RFC 3339 UTC `Z` `occurredAt`
- UUIDv7 correlation metadata
- one of the accepted `health`, `error`, or `websocket` payloads

The TypeScript client validates all response bodies and incoming envelopes,
constructs bearer requests and ticket URLs, and reconnects only with a fresh
ticket. It does not expose broker, market, strategy, order, execution, risk,
reconciliation, or AI operations.

## Error model

Errors use the same versioned message envelope and correlation metadata as
other messages. The payload requires a stable uppercase `code`, a safe human
message, and an explicit `retryable` flag. A `field` may identify invalid input.
Unknown payload fields are rejected, and messages must not expose credentials,
internal stack traces, broker secrets, or raw database errors.

Focused API, contract, and client suites passed during implementation. Final
full Milestone 3 acceptance remains pending.
