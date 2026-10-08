# Q-097 implementation plan: Imported backtest runs in the control API

> **For implementation agents:** Read the linked specification and repository instructions. Use superpowers:executing-plans when available. Launch only through `./work start Q-097 --agent <agent> --worktree` after written-plan approval. Implement natively; delegation requires separate authorization.

**Goal:** The control API contract can describe importing a finished backtest and telling script runs from stack runs.
**Architecture:** One additive endpoint and three additive fields in the OpenAPI document; generated types flow to `q_backend` and `q_frontend`.
**Tech stack:** OpenAPI, the repository's Python generator, Python/TypeScript/Rust outputs, pytest.
**Spec:** [Specification](../specs/Q-097-imported-backtest-runs-in-the-control-api-spec.md)
**Status:** implemented on task branch; awaiting merge.

## Global constraints

- Additive only: no existing field, enum value, path or operation id changes.
- Reuse `BacktestRequest` and `BacktestResponse` by reference; do not copy their properties into new schemas.
- Generated files change only through the generator.
- Commit focused units on the task branch; no push, merge or protected-branch checkout.

## Review focus

- A response without `origin` still validates and means `stack`.
- The import request cannot be mistaken for a job request: it is a separate path and schema.
- Service-owned rules are written in the operation description, not implied.
- `idempotency.yaml` is untouched.

## Ordered implementation

### 1. Define the import operation and origin fields

**Files:** Modify `schema/api/openapi.yaml`; add fixtures under `schema/api/examples/`; create `tests/test_backtest_import_contracts.py`.
**Interfaces:** `BacktestImportRequest`, `BacktestImportResponse`, `BacktestProvenance`; `origin` on `BacktestRunListItem` and `BacktestRunDetailResponse`; `provenance` on the detail; `origin` query parameter on the run list.

- [x] Add failing tests: a complete import fixture validates; fixtures missing `config`, `result` or `provenance` are rejected; an `origin` outside the enum is rejected; existing run list and detail fixtures still validate.
- [x] Run `uv run pytest tests/test_backtest_import_contracts.py tests/test_api_consistency.py -q` and confirm the new cases fail because the schemas are missing.
- [x] Add the schemas, the path and the query parameter as the spec defines them.
- [x] Run the same command and confirm it passes (`21 passed`).
- [x] Commit this unit.

### 2. Generate outputs and document

**Files:** Modify `generated/` through the generator; extend `tests/test_generate.py`; modify `schema/api/README.md` and `COMPAT.md`.

- [x] Add a failing generator test that the three outputs carry the `origin` enum and the `BacktestProvenance` fields.
- [x] Regenerate, then run `make check`.
- [x] Write the README section and the `COMPAT.md` entry.
- [x] Commit this unit.

## Verification and handoff

- [x] Run `make check` once after the final change (`240 passed, 7 skipped, 1 deselected`).
- [x] Record the commands actually run and their results in this plan; do not claim unrun checks passed.
- [ ] Use `./work board set Q-097 in-review -m "<changes; checks and results; follow-ups>"`. State that Q-099 and Q-101 need the merged commit pushed to the remote.
