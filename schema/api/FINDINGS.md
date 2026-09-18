# Control API Findings

This document records discrepancies discovered while capturing and auditing the `q_backend` control surface against client consumers (`q_frontend`, `q_terminal`, and stream subscribers). Each discrepancy represents a latent bug or architectural gap and has been triaged as either a **later task** or an **accepted deviation**.

---

## Finding 1: Absence of a Shared Error Model Across the Surface

- **Endpoint / Field:** Surface-wide (all 14 routers).
- **Expectation:** Every failing operation references a single, standard error shape (`schema/api/error.schema.json`: `{"message": string, "code"?: string, "details"?: any}`).
- **Observed Behavior:** `q_backend` defines no shared error model in `schemas/common.py`. Endpoints return either FastAPI's default `{"detail": ...}` structure (from `HTTPException` or `HTTPValidationError`) or custom per-router response schemas (e.g. `AiStrategyServiceErrorResponse` in `strategy_builder`). No shared error schema is referenced across endpoints.
- **Triage Decision:** Later task. Introduce a shared `ErrorResponse` Pydantic model in `q_backend` matching `schema/api/error.schema.json` and install a global exception handler.

---

## Finding 2: Operations Fail Without Declaring Error Responses in OpenAPI

- **Endpoint / Field:** 87+ operations across all 14 mounted routers (e.g., `GET /api/v1/backtest/{run_id}`, `DELETE /api/v1/optimizations/{study_id}`, `POST /api/v1/execution/deployments/{deployment_id}/actions`).
- **Expectation:** Operations that can fail with HTTP 400, 404, 409, 500, or 503 declare these response status codes and schemas in route metadata (`responses={...}`).
- **Observed Behavior:** 14 operations declare zero error responses, and 87 operations declare only FastAPI's automatic `422 Unprocessable Entity` validation error. Explicit 400, 404, 409, and 500 status codes raised via `raise HTTPException(...)` inside endpoint bodies are undeclared in the OpenAPI route specifications. The only explicit non-422 error declarations across the entire surface are `GET /api/v1/strategy-builder/models` (503) and `POST /api/v1/strategy-builder/interpret` (502, 503).
- **Triage Decision:** Later task. Audit router exception paths and declare explicit `responses={404: ...}` in FastAPI route decorators.

---

## Finding 3: Missing Client-Supplied Idempotency Keys on Mutating Commands

- **Endpoint / Field:** Mutating POST/PUT commands (`POST /api/v1/backtest`, `POST /api/v1/optimize`, `POST /api/v1/execution/deployments`, `POST /api/v1/execution/deployments/{deployment_id}/actions`).
- **Expectation:** Mutating operations accept an `Idempotency-Key` (or `X-Idempotency-Key`) header and guarantee stored-result-on-retry semantics.
- **Observed Behavior:** None of the mutating routes declare or accept an idempotency key header in their OpenAPI schema. Retrying a request (e.g. on client network timeout) risks dispatching duplicate jobs or re-executing stateful actions. While internal database constraints prevent duplicate execution decisions for `(deployment_id, bar_close_time)`, the control API boundary does not provide client-facing command idempotency.
- **Triage Decision:** Contract declared by Q-039 in `schema/api/idempotency.yaml` and `schema/api/error.schema.json`; implemented by Q-044.

---

## Finding 4: Absence of Stream-Protocol Outbox History and Latest Endpoints

- **Endpoint / Field:** Stream topic replay and snapshot endpoints for durable topics (`decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments`, `jobs.terminal`) and ephemeral topics (`quotes`, `bars.forming`, `bars.completed`, `jobs.progress`).
- **Expectation:** §4.2 of the system architecture requires REST history replay endpoints accepting sequence watermarks (`from_seq`) to support the subscribe-then-snapshot sequence and lag gap recovery, as well as `latest` snapshot endpoints for instant state synchronization.
- **Observed Behavior (Q-015, partial):** `q_backend` now exposes generic replay routes: `GET /api/v1/stream/{topic}/history`, `GET /api/v1/stream/{topic}/latest`, and `GET /api/v1/stream/jobs/snapshot`. History and latest work for job and market-data topics (`jobs.terminal`, `jobs.progress`, `quotes`, `bars.forming`, `bars.completed`). Execution durable topics (`decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments`) still have no snapshot producers in phase 4; history for them is served generically from the outbox when events exist, but no execution-specific snapshot endpoints exist yet. Legacy execution history endpoints (`/api/v1/execution/deployments/{deployment_id}/decisions`, and others) remain timestamp-paged and unchanged.
- **Triage Decision:** Resolved for job and market-data topics (Q-015). For execution topics (`decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments`): payload contracts and execution snapshot schema declared by Q-039 (`schema/stream/payloads/execution-*.schema.json`, `schema/stream/replay/execution-snapshot.schema.json`); implemented by Q-043 (outbox event emission) and Q-044 (snapshot route `GET /api/v1/stream/execution/snapshot`).
  - *Note (Q-009, Q-039):* Replay response shapes are defined in `schema/stream/replay/` and captured in `schema/api/openapi.yaml`.

---

## Finding 5: Inconsistent and Untyped Job Status and Lifecycle Schemas

- **Endpoint / Field:** Job status endpoints across routers (`GET /api/v1/backtest/{run_id}`, `GET /api/v1/optimize/{study_id}`, `GET /api/v1/neural/models/train/{job_id}`, `GET /api/v1/experiments/alpha-research/{job_id}`, `GET /api/v1/experiments/discovery-ab/{job_id}`, `GET /api/v1/experiments/encoder-ablation/{job_id}`).
- **Expectation:** All async job status payloads share a common lifecycle contract: consistent job identifier field, standard status enumeration (`queued`, `running`, `completed`, `failed`, `cancelled`), numeric progress float in `[0.0, 1.0]`, and structured result/error.
- **Observed Behavior:**
  - `BacktestStatusResponse` uses `run_id`, unconstrained `status: string`, `error: string | null`, and has no `progress` field.
  - `OptimizationStatusResponse` uses `study_id`, unconstrained `status: string`, `completed_trials`/`n_trials` integers, and no progress float.
  - `NeuralTrainStatusResponse` and `EncoderAblationStatusResponse` declare `progress` as `string | null` (free-form text like `"45%"` or `"Epoch 3/10"`).
  - `DiscoveryAbStatusResponse` and `AlphaResearchStatusResponse` declare `progress` as a numeric `float` with explicit `status` enums.
- **Triage Decision:** Later task. Standardize job orchestration status contracts across all background workers.

---

## Finding 6: Untyped Metrics, Trades, and Config Dictionaries in Backtest Models

- **Endpoint / Field:** `BacktestResponse.metrics`, `BacktestResponse.trades`, `BacktestRunDetailResponse.config`, `BacktestRunDetailResponse.result_summary`.
- **Expectation:** Backtest responses declare strongly-typed schemas for performance metrics (drawdown, win rate, PnL), individual trade records, and run configuration snapshots matching frontend expectations (`BacktestMetrics`, `Trade`, `BacktestRequest`).
- **Observed Behavior:** The backend Pydantic models use bare `dict[str, Any]` or untyped objects (`additionalProperties: true`), leaving `metrics`, `trades`, and `config` unvalidated in the OpenAPI specification.
- **Triage Decision:** Later task. Add typed Pydantic models for backtest performance metrics, executed trade records, and serialized configuration snapshots.

---

## Finding 7: System Health Schema Discrepancies (storageStatus and active_provider)

- **Endpoint / Field:** `GET /api/v1/system/health` -> `SystemHealthResponse` vs `q_frontend/src/types/api.ts` -> `SystemHealth`.
- **Expectation:** Frontend `SystemHealth` type matches the backend `SystemHealthResponse` schema.
- **Observed Behavior:**
  - Backend requires `storageStatus` (`StorageStatusResponse`), but frontend `SystemHealth` omits `storageStatus` entirely.
  - Backend `active_provider` enum includes `remote` (`mt5 | remote | local`), while frontend defines only `'mt5' | 'local'`.
  - Backend declares `mt5_available`, `active_provider`, `market_data_root`, and `market_data_inventory_count` as required fields, while frontend marks them as optional (`?:`).
- **Triage Decision:** Later task. Update frontend `SystemHealth` interface and queries to include `storageStatus` and the `remote` provider option.

---

## Finding 8: Duplicate and Divergent Market Data Endpoints

- **Endpoint / Field:** `/api/v1/market/ohlcv/{symbol}` vs `/api/v1/market-data/ohlcv`, and `/api/v1/market/ticks/{symbol}` vs `/api/v1/market-data/ticks`.
- **Expectation:** A single consolidated set of market data endpoints with uniform bar and tick data models.
- **Observed Behavior:**
  - `q_backend` mounts two competing routers: `/api/v1/market/*` (returns `OhlcvBarResponse` with `timestamp`/`volume` and `MarketTicksResponse` with `timestamp`/`last`/`side`) and `/api/v1/market-data/*` (returns `OHLCV` with `time`/`tick_volume`/`spread` and `Tick` with `time_msc`/`flags`).
  - `q_frontend` queries only call `/api/v1/market/*`. The `/api/v1/market-data/*` endpoints are uncalled legacy paths.
- **Triage Decision:** Later task. Deprecate `/api/v1/market-data/*` in favor of `/api/v1/market/*` and columnar Arrow streams.

---

## Finding 9: Frontend Query Path Parity Confirmed

- **Endpoint / Field:** All 93 API query invocations across `q_frontend/src/api/queries/`.
- **Expectation:** Every endpoint called by the frontend exists in the backend route table.
- **Observed Behavior:** All 93 distinct API call paths in `q_frontend` successfully match endpoints present in `schema/api/openapi.yaml`. There are no orphan or phantom endpoints called by the frontend.
- **Triage Decision:** Accepted deviation / No action required (100% path parity verified).
