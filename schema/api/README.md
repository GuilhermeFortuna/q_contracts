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

## Populating Task

This boundary is populated by task **Q-003** (`Control API and Columnar Schemas`) and extended by **Q-039** (`Execution event payloads and command idempotency`).
