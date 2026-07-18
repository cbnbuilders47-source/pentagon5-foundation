# ADR 0002: Identifiers, Time, and Decimal Values

- Status: Accepted
- Date: 2026-07-18

## Context

Distributed creation, event ordering, audit precision, and exact financial arithmetic require representations that behave consistently across languages and storage systems.

## Decision

Contract identifiers are lowercase canonical UUIDv7 strings. UUIDv7 provides decentralized generation with time-ordered values; schemas enforce the version and RFC 4122 variant bits. Clients generate IDs needed before submission, including `clientOrderId`, correlation IDs, and idempotency keys where applicable.

Contract timestamps are RFC3339 `date-time` strings in UTC and must end in uppercase `Z`. Offsets, local timestamps, and numeric epochs are rejected at boundaries.

Financial decimal values are JSON strings, never JSON numbers. Canonical values:

- use ordinary base-10 notation without an exponent or leading plus;
- use no leading integer zeros;
- use no trailing fractional zeros or decimal point without a fraction;
- encode zero as `0`, never `-0`;
- retain a leading zero for magnitudes below one.

Examples accepted are `0`, `-0.25`, `10`, and `189.1`. Examples rejected are `10.0`, `01`, `1e3`, `-0`, and JSON numeric `10.5`.

## Consequences

- Services parse decimal strings into decimal/fixed-point types and serialize them canonically.
- Lexicographic ordering must not be used as numeric ordering.
- Timestamp normalization happens before contract serialization.
- Manual broker exits and reconciliation outcomes use the same identifier, time, and decimal rules as platform-originated executions.
