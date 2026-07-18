# API Documentation

## NOT IMPLEMENTED

HTTP routes, generated API reference, and transport implementations are not implemented.

## Milestone 2 contract reference

The canonical API shapes are Draft 2020-12 schemas:

- `packages/shared-types/schemas/v1/common.schema.json`
- `packages/shared-types/schemas/v1/domain.schema.json`
- `packages/event-contracts/schemas/v1/message.schema.json`

Every message carries `schemaVersion: "1.0.0"`, a UUIDv7 message ID, an RFC3339 UTC `Z` timestamp, and correlation metadata. Financial values are canonical decimal strings. Message categories are `command`, `query`, `response`, `domain_event`, `error`, `health`, `websocket`, and `audit`.

Order commands include a client-generated idempotency key. Responses can expose replay metadata. Pagination uses cursor requests and `hasNextPage`/`nextCursor` response metadata. Reconciliation can report external manual exits without implying a broker implementation.

Compatibility and representation policy are recorded in ADR 0001 and ADR 0002.

## Error model

Errors use the same versioned message envelope and correlation metadata as
other messages. The payload requires a stable uppercase `code`, a safe human
message, and an explicit `retryable` flag. A `field` may identify invalid input.
Unknown payload fields are rejected, and messages must not expose credentials,
internal stack traces, broker secrets, or raw database errors.
