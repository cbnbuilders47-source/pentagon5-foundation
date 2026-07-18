# Shared Types

## NOT IMPLEMENTED

Runtime and generated language bindings are not implemented.

## Milestone 2 schema boundary

`schemas/v1/common.schema.json` defines version, UUIDv7, UTC timestamp, canonical decimal, pagination, idempotency, correlation, causation, and audit primitives. `schemas/v1/domain.schema.json` defines the strict v1 domain models.

These Draft 2020-12 schemas are the source of truth. Consumers must reject unknown fields and unsupported schema versions. Published v1 definitions are immutable.
