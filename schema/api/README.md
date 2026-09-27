# Control API Boundary

This directory holds schemas describing the control and configuration API surface, including REST endpoints, job payloads, and columnar query payloads exchanged with the control service.

## What Belongs Here

- OpenAPI documents describing the control REST surface and job submission/status contracts.
- Apache Arrow schema definitions for columnar API responses and query payloads.
- Control-plane request and response contracts.

## What Does Not Belong Here

- Event stream message payloads or topic policies (belong in `schema/stream/`).
- Edge gateway protocol contracts or bridge payloads (belong in `schema/edge/`).
- Lake dataset catalog manifests (belong in `schema/catalog/`).
- Generated client code, server stubs, or language-specific bindings (belong in `generated/`).

## Command Idempotency Policy

Mutating control commands require a client-generated idempotency key in the `Idempotency-Key` request header (governed by `schema/api/idempotency.yaml`).

- **Header:** `Idempotency-Key`
- **Key format:** RFC 4122 UUID string.
- **TTL:** 24 hours (`PT24H`).
- **Replay semantics:**
  - Exact match (`method`, `path`, body hash): Returns the stored response without re-execution.
  - Key reuse with conflicting payload: Refuses request with error code `idempotency_key_reused`.
  - In-progress retry: Refuses request with HTTP 409 and error code `idempotency_in_progress`, indicating retry after delay (`Retry-After`).
  - Missing key on required command: Refuses request with error code `idempotency_key_required`.
- **Required operations:**
  - `create_execution_account_api_v1_execution_accounts_post` (`POST /api/v1/execution/accounts`)
  - `create_execution_deployment_api_v1_execution_deployments_post` (`POST /api/v1/execution/deployments`)
  - `deployment_action_api_v1_execution_deployments__deployment_id__actions_post` (`POST /api/v1/execution/deployments/{deployment_id}/actions`)
  - `update_kill_switch_api_v1_execution_kill_switch_put` (`PUT /api/v1/execution/kill-switch`)
  - `resolve_execution_order_api_v1_execution_orders__order_id__resolve_post` (`POST /api/v1/execution/orders/{order_id}/resolve`)

## Paper Deployment, Configuration Revision, and Performance Routes

The control API supports paper deployment configuration revisions, cost models, and performance tracking (introduced by contracts task **Q-066**, implemented in backend by **Q-067** and **Q-068**, and consumed in terminal by **Q-069**).

### Route Inventory

- **Strategy Catalog (`GET /api/v1/execution/strategy-catalog`):**
  - Returns registered strategies, parameter definitions, valid ranges, and default `paper_cost_config`.
  - Used by the terminal to render strategy selection and configuration forms.

- **Deployment Creation (`POST /api/v1/execution/deployments`):**
  - Requires `Idempotency-Key` header.
  - Initializes `config_revision = 1`.
  - Captures `paper_cost_config` snapshot.

- **Configuration Editing (`PATCH /api/v1/execution/deployments/{id}/configuration`):**
  - Mutating command requiring `Idempotency-Key` header.
  - Modifies strategy configuration and/or `paper_cost_config`.
  - **Revision-conflict semantics:** Clients must submit expected `config_revision` (or `If-Match`). If the server revision does not match, the server returns HTTP 409 Conflict (`revision_conflict`), preventing lost updates or race conditions from concurrent edits.
  - Each accepted edit increments `config_revision` by exactly 1.
  - Note: `strategy_version` remains tied to strategy code implementation compatibility and does not change on operator configuration edits.

- **Paper Performance (`GET /api/v1/execution/deployments/{id}/performance`):**
  - Returns summarized performance metrics (realized/unrealized PnL, win rate, Sharpe, drawdown, trade counts) for the deployment.

- **Paper Performance Marks (`GET /api/v1/execution/deployments/{id}/performance/marks`):**
  - Returns paged historical marks and equity series.
  - Supports standard paging query parameters (`limit`, `cursor` / `offset`).
  - **Streaming boundary note:** Performance history is paged REST data; it is intentionally excluded from the six durable execution stream topics. The terminal fetches performance marks on deployment selection and when a completed-bar deployment event arrives.

### Decimal and Monetary Precision

All monetary amounts, execution prices, quantities, and cost parameters (`point_value`, `slippage_points`, `cost_per_contract`, `cost_bps`) must be transmitted across the API boundary as exact-decimal strings (e.g. `"128505.00"`), never as JSON floating-point numbers.

### Consumer Vendoring Order

Contracts follow one-way pinned vendoring (`q_contracts` -> consumers):
1. **`q_contracts` (Q-066):** Adds schema extensions (`config_revision`, `paper_cost_config`, `dispatch_attempted_at`) and generates language bindings.
2. **`q_backend` (Q-067 & Q-068):** Pins `q_contracts` commit, vendors Python models, implements catalog/create/edit routes and paper performance endpoints, and recaptures `openapi.yaml`.
3. **`q_terminal` (Q-069):** Pins `q_contracts` commit, vendors TypeScript / Rust models, and implements terminal configuration editing and performance UI.

## Populating Task

This boundary is populated by task **Q-003** (`Control API and Columnar Schemas`), extended by **Q-039** (`Execution event payloads and command idempotency`), and extended by **Q-066** (`Paper deployment contract extensions`).
