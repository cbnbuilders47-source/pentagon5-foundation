# Event Contracts

## NOT IMPLEMENTED

Transport and broker integrations are not implemented.

## Milestone 2 schema boundary

`schemas/v1/message.schema.json` defines strict, versioned envelopes for commands, queries, responses, domain events, errors, health, WebSocket control messages, and audit messages. Pagination, idempotency, audit, correlation, and causation metadata reuse shared definitions.

All order commands require client-generated idempotency keys. Manual broker exits are represented as reconciliation data; this package does not implement a broker.
