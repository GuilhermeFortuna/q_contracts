# Dataset Catalog Boundary

This directory holds schemas and identity rules that make lake data catalog-addressed and immutable.

## What Belongs Here

- Dataset manifest schemas defining dataset metadata, partitioning, and storage layouts.
- Dataset-identity schemas and hashing rules for immutable lake partitions.
- Columnar schema specifications for persisted parquet/arrow dataset collections.

## What Does Not Belong Here

- Live event stream schemas (belong in `schema/stream/`).
- REST control API endpoint schemas (belong in `schema/api/`).
- Edge process gateway contracts (belong in `schema/edge/`).
- Generated dataset readers or lake access libraries (belong in `generated/`).

## Populating Task

This boundary is populated by task **Q-005** (`Dataset Manifest and Catalog Schema`).
