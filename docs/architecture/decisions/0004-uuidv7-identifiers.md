# ADR 0004: Application-Generated UUIDv7 Identifiers

- Status: Accepted
- Date: 2026-07-18

## Context

Persistent entities need globally unique identifiers that can be created before
a database round trip. Random UUIDv4 values cause poor index locality at
write-heavy tables, while database sequences expose ordering and complicate
distributed creation.

## Decision

Application services generate UUIDv7 identifiers before inserts. PostgreSQL
stores them in native `uuid` columns and does not supply identifier defaults.
UUIDv7 provides time-ordered index locality while retaining sufficient
randomness for distributed generation.

The UUID timestamp is routing and locality metadata only. It is not an
authoritative event time and must not replace `created_at`, `occurred_at`, or
other `timestamp with time zone` columns. Applications must use a standards
compliant UUIDv7 generator, preserve all 128 bits, and never derive identifiers
from user data or secrets.

Deterministic development seed identifiers are syntactically valid,
version-marked UUIDv7 values reserved for mock data. They must not be generated
in production.

## Consequences

- Insert callers must always provide primary keys.
- Database nodes need no UUID extension or sequence coordination.
- IDs generally sort by generation time, but ordering must use explicit
  timestamp columns when correctness depends on time.
