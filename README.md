# q_contracts

`q_contracts` is the single source of truth for all cross-process payload contracts across the system.

Consumers do not import from `q_contracts` as a package dependency via a package registry. Instead, consumers vendor generated types and schemas pinned to a specific git commit hash in this repository.

## Repository Layout

The repository organizes schemas by the system boundary they describe, not by the repository that consumes them:

```
schema/                  Hand-authored schema definitions (source of truth)
  api/                   Control and configuration API boundary (REST endpoints, jobs, columnar schemas)
  stream/                Event stream boundary (envelope schema, topic policies, stream control)
  edge/                  Edge process boundary (gateway wire formats, order execution contracts)
  catalog/               Dataset catalog boundary (lake manifests, dataset-identity schemas)
generated/               Generated code and serialized schemas (populated by generation tools)
tools/                   Validation and code generation tooling
  validate.py            Automated schema and boundary validation tool
tests/                   Unit tests for validation tooling
VERSIONING.md            Versioning rules, breaking change policies, and pinning guidelines
Makefile                 Unified developer interface (make check)
```

- **`schema/`**: Hand-authored contracts. No external consumer reads from `schema/` directly.
- **`generated/`**: Downstream generated code. External consumers vendor exclusively from this output.

## Boundary Guide: Where Does a Schema Belong?

When adding a new contract, identify the boundary class:

1. **`schema/api/` (Control API):**
   - Synchronous REST endpoints, administrative operations, job payloads.
   - Arrow schema definitions for columnar API query responses.
   - Governed by OpenAPI and Arrow schema specifications.

2. **`schema/stream/` (Event Stream):**
   - Asynchronous message bus topics and stream events.
   - Message envelope structure (`envelope.schema.json`) and topic definitions (`topics.yaml`).
   - Streaming control messages (subscriptions, cursors, epoch changes).

3. **`schema/edge/` (Edge Wire Contracts):**
   - Wire contracts for edge processes (e.g. Wine/Windows bridge processes).
   - Execution edge protocols with intent-at-most-once semantics.
   - Low-level telemetry and gateway IPC/network payloads.

4. **`schema/catalog/` (Dataset Catalog):**
   - Lake dataset manifests and partitioning metadata.
   - Schema identity, hashing, and immutability rules for lake storage.
   - Parquet/Arrow table and column layout contracts.

## How to Add a Schema

1. Determine the appropriate boundary directory (`api/`, `stream/`, `edge/`, or `catalog/`).
2. Create your schema file with the `.schema.json` extension (or `.yaml` for topic/manifest policies).
   - For example: `schema/stream/custom_event.schema.json`.
3. Schema identifiers are strictly derived from the file's path relative to `schema/` without extension:
   - For `schema/stream/custom_event.schema.json`, the expected identifier is `stream/custom_event`.
   - If you include an `$id` field, it must exactly match the derived identifier (`"stream/custom_event"`).
4. Declare the supported schema dialect in `$schema`:
   - Use `"https://json-schema.org/draft/2020-12/schema"`.
5. Run the validation suite to verify the schema:
   ```bash
   make check
   ```
   No central registry file needs to be edited. Schema files placed in a boundary directory are automatically discovered and validated.

## Single Validation Command

All validation checks (code formatting, linting, schema validation, and test suite) are executed via a single command:

```bash
make check
```

This runs:
1. `black --check .` (Code formatting)
2. `ruff check .` (Static analysis and linting)
3. `python tools/validate.py` (Schema tree validation)
4. `pytest` (Unit tests)

Continuous integration (CI) executes this exact command on all pushes and pull requests.
