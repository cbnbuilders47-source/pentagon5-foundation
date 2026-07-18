# Authentication Contracts

Versioned JSON Schema definitions for the PENTAGON5 authentication, session,
device, and WebSocket-ticket API. The `schemas/v1` directory is immutable after
publication. These contracts are separate from the existing shared domain and
event contract packages.

The only WebSocket channel identifiers in v1 are `system.health` and
`session.events`. Session and ticket values are opaque and must never be logged
or persisted by clients. Native login uses a short-lived one-time code at the
custom desktop callback and a separate exchange request; provider callbacks
never put session tokens in URLs.
