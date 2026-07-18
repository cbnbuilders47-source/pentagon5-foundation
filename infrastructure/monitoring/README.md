# Monitoring Infrastructure

## Milestone 3 monitoring

Docker Compose runs OpenTelemetry Collector, Prometheus, and Grafana alongside
the independent authentication and API gateway services. Both FastAPI factories
expose `/metrics`, generate bounded-cardinality request counters and latency
histograms, propagate or create UUIDv7 request IDs, and optionally export traces
to the configured OTLP HTTP endpoint.

Startup and liveness return accepted health envelopes. Readiness performs a
bounded PostgreSQL check and returns an accepted retryable error envelope when
the database is unavailable. Compose health checks use readiness, and
Prometheus scrapes both backend containers.

Milestone 3 does not provide production dashboards, alert rules, retention
policy, SLOs, or paging. Focused observability and health tests passed during
implementation; final full acceptance remains pending.
