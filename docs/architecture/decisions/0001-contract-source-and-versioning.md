# ADR 0001: Contract Source and Versioning

- Status: Accepted
- Date: 2026-07-18

## Context

Desktop, API, event, trading, and administrative components need one interoperable contract language. Silent producer changes are especially unsafe for persisted events and order workflows.

## Decision

JSON Schema Draft 2020-12 files in `packages/shared-types/schemas` and `packages/event-contracts/schemas` are the source of truth. Generated language types, when introduced, are derived artifacts and must not redefine validation rules.

Every entity and message carries `schemaVersion`, fixed to `1.0.0` for v1. Message envelopes are category-discriminated and reject unevaluated properties. Payload objects also reject additional properties.

Published v1 schemas are immutable. A change is backward compatible only when every frozen v1 fixture still validates without transformation. Additive optional fields are not added in place because strict v1 consumers reject them; they require a new schema version and parallel schema identifier. Required-field changes, field removal, type changes, enum narrowing, semantic reinterpretation, and relaxed identifier or numeric formats require a new major version.

Consumers select schemas by the explicit version and must reject unknown versions. Producers may publish multiple versions during migration. Persisted events retain the version with which they were written.

Order mutations require a client-generated idempotency key. Responses may report replay state. Correlation IDs trace a workflow, while causation IDs identify the immediately preceding message.

## Consequences

- Compatibility is executable through frozen fixtures.
- Strict schemas detect drift early but require deliberate version rollout for additions.
- Transport implementations and broker adapters remain outside the contract package.
