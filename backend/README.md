# Shared Python Runtime

`pentagon5_runtime` provides strict environment and `*_FILE` secret loading,
PostgreSQL engine construction, JSON structured logging with secret redaction,
request correlation, Prometheus HTTP metrics, optional OTLP tracing, and health
helpers for independently operated FastAPI services.

Unknown `P5_` settings fail startup to catch deployment mistakes. Production is
the default environment, database URLs must use PostgreSQL, and services must
provide an explicit service name. The runtime also provides monotonic UUIDv7,
accepted Milestone 2 error/health/WebSocket envelopes, exact-origin CORS,
bounded request bodies, safe request timeouts, and validated correlation IDs.
