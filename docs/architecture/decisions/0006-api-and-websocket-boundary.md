# ADR 0006: API and WebSocket Boundary

- Status: accepted
- Date: 2026-07-18

## Context

Milestone 2 published broad structural domain and message contracts, including
future trading entities. Milestone 3 authorizes only identity, service health,
and desktop connectivity. A generic entity endpoint would accidentally expose
future data and bypass explicit authorization boundaries.

## Decision

The API gateway exposes only allowlisted system-health, authentication, device,
session, and WebSocket-ticket routes. It does not expose generic entity,
command, query, trading, broker, market, strategy, execution, risk, or AI routes.

REST errors and health responses use accepted Milestone 2 message envelopes.
WebSockets require a short-lived, single-use ticket issued through authenticated
REST. The only channels are `system.health` and `session.events`. Control frames
must be accepted v1 WebSocket envelopes and are bounded by size and subscription
count.

The gateway and authentication application have independent executable
factories. Milestone 3 uses a temporary modular deployment in which the gateway
mounts the authentication surface in-process; a later milestone may introduce a
network service boundary only with explicit service identity and failure-policy
decisions.

## Consequences

- Published Milestone 2 v1 schemas remain unchanged.
- Authentication contracts live in a separate versioned package.
- The desktop cannot issue or simulate trading operations.
- Server processes are never started, stopped, or supervised by Tauri.
