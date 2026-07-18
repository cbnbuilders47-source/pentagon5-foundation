# API Gateway

The gateway is an independently launchable FastAPI process exposing the
Milestone 3 system and authentication route surface. It deliberately contains
no broker, market, strategy, order, risk, execution, reconciliation, or AI
routes.

For Milestone 3 only, the gateway mounts the authentication module in-process
as a temporary modular deployment. The authentication and gateway factories
remain separately executable and are tested independently. This is not network
isolation; a later deployment milestone may move the same auth surface behind a
separate network boundary.

Run with `uvicorn pentagon5_gateway.app:create_app --factory`. The process uses
the shared Python runtime for strict configuration, JSON logs, Prometheus
metrics, request correlation, OTLP tracing, and database-backed readiness. Its
WebSocket surface is restricted to one-time ticket access for `system.health`
and `session.events`.
