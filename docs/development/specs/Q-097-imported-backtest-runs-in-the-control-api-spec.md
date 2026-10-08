# Q-097: Imported backtest runs in the control API

**Status:** written spec awaiting human review; the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2) is the status of record.
**Batch:** 17 — Research script runs in the Research stack
**Depends on:** none
**Implementation plan:** [Plan](../plans/Q-097-imported-backtest-runs-in-the-control-api-plan.md)

## Purpose

A backtest run in the Research stack exists only when the stack executed it. A backtest produced by a research script with `q_backend.research.backtest()` has no way in, so its results cannot be reviewed in Backtests history beside the stack's own runs.

This task defines the boundary for importing a finished backtest: one endpoint that accepts a completed result, and the fields that tell a script run apart from a stack run. Q-099 implements the endpoint, Q-100 calls it from the research library and Q-101 shows the runs.

## Contract

All changes are in `schema/api/openapi.yaml` and are additive.

### `POST /api/v1/backtests/import`

Operation id `import_backtest_api_v1_backtests_import_post`. Request body `BacktestImportRequest`:

| Field | Type | Meaning |
| --- | --- | --- |
| `config` | `BacktestRequest` | The run's configuration in the shape history already stores. `strategy` is the display name of the script strategy and need not be a registered strategy; `strategy_params` holds its parameters; `start` and `end` are the first and last bar times; `engine` is `candle`. |
| `result` | `BacktestResponse` | The full result: `metrics`, closed `trades`, `bars` and `indicators`. `run_id` is ignored on input. |
| `provenance` | `BacktestProvenance` | Where the run came from. |

`BacktestProvenance`:

| Field | Type | Meaning |
| --- | --- | --- |
| `script` | string | Path of the script that produced the run, as the script saw it |
| `strategy_class` | string | Qualified class name of the strategy |
| `strategy_source` | string or null | Source text of the strategy class when it could be read |
| `git_revision` | string or null | Commit of the repository holding the script |
| `git_dirty` | boolean or null | Whether that repository had uncommitted changes |

Responses: `201` with `BacktestImportResponse` (`run_id`); `422` when the body fails schema or service validation, using the existing validation error shape.

The description states the service-owned rules the schema cannot express: `result.bars` is non-empty and ascending, every indicator series has one value per bar, `config.ml_filter` is absent, and every import creates a new run.

The operation is not added to `idempotency.yaml`. A retried import creates a second run, which the user deletes from history like any other.

### Run origin

- `BacktestRunListItem` and `BacktestRunDetailResponse` gain `origin`, an enum of `stack` and `script` with default `stack`.
- `BacktestRunDetailResponse` gains optional `provenance` (`BacktestProvenance` or null), present for script runs.
- `GET /api/v1/backtests` gains the optional query parameter `origin` with the same enum; omitted, it returns every run.

A consumer that ignores the new fields keeps working: existing responses without `origin` mean `stack`.

## Generated outputs and documentation

- Regenerate the Python, TypeScript and Rust outputs with the repository generator.
- `schema/api/README.md` gains a short "Imported backtest runs" section: the route, the origin field, and the rule that script runs are reviewable but are not inputs to re-run, optimisation, walk-forward or ML filter training.
- `COMPAT.md` records the change as additive.

## Focused acceptance

1. A contract test validates a complete import request fixture and rejects one missing `config`, `result` or `provenance`.
2. Existing run list and detail fixtures without `origin` remain valid, and generated consumer types default `origin` to `stack`.
3. The three generated outputs express the same `origin` enum and `BacktestProvenance` fields.
4. `make check` passes offline. No live API capture is required before Q-099 exists.

## Delivery boundary

- No change to `BacktestRequest`, `BacktestResponse`, the job endpoints, the artifact or export endpoints, stream topics or the catalog schemas.
- No upload or execution of strategy code. `strategy_source` is descriptive text for the reviewer and is never executed by the stack.
- The merged commit must be pushed before Q-099 and Q-101 start, because their `make contracts` fetches the pinned revision from the remote.
