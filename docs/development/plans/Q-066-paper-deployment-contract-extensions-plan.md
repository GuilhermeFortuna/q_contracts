# Q-066 implementation plan: Paper deployment contract extensions

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-066-paper-deployment-contract-extensions-spec.md`](../specs/Q-066-paper-deployment-contract-extensions-spec.md)  
**Depends on:** Q-039 (Done)

## Current-system context

`schema/stream/payloads/execution-deployment.schema.json` and
`execution-decision.schema.json` carry strategy identity and `config_hash`.
`execution-order.schema.json` has `submitted_at`, but no dispatch-attempt
field. `execution-fill.schema.json` already has quote fields. The execution
snapshot references the event shapes. `schema/api/openapi.yaml` is captured
from a running backend, and the generator emits Python, TypeScript and Rust.

## Interfaces produced

| Contract | Additive fields |
| --- | --- |
| `ExecutionDeploymentState` | `config_revision?: integer >= 1`, `paper_cost_config?: PaperCostConfig` |
| `ExecutionDecisionState` | `config_revision?: integer >= 1`, `paper_cost_config?: PaperCostConfig` |
| `ExecutionOrderState` | `dispatch_attempted_at?: RFC3339 timestamp or null` |
| `ExecutionCommon.$defs.PaperCostConfig` | `point_value`, `slippage_points`, `cost_per_contract`, `cost_bps` as decimal strings |

`PaperCostConfig` requires all four fields when present. Point value must be
positive; the three cost values must be nonnegative. The API documentation
names `GET /api/v1/execution/strategy-catalog`, catalog-based deployment
creation, `PATCH /api/v1/execution/deployments/{id}/configuration`,
`GET /api/v1/execution/deployments/{id}/performance`, and paged
`GET /api/v1/execution/deployments/{id}/performance/marks`.

## Implementation decisions

- Keep new fields optional in version-1 event schemas for historical replay;
  require them from new producers through Q-067/Q-068 tests.
- Keep `strategy_version` separate from `config_revision`. A cost-only edit can
  change revision while leaving the compiled-config hash unchanged.
- Reuse fill quote fields, and use a single order dispatch-attempt field rather
  than introducing a new topic or an unversioned details convention.
- Describe new API routes in the API README now; Q-067/Q-068 recapture OpenAPI
  from implemented routes. Do not manually modify the capture in this task.

## Ordered implementation

- [x] 1. On the Q-066 task branch, write failing schema tests in
  `tests/test_execution_payloads.py` for valid and invalid revision, cost and
  dispatch values, plus backward compatibility with existing examples.
- [x] 2. Add `PaperCostConfig` to `execution-common.schema.json`; extend the
  three event schemas and their examples. Expand the paper fill example to
  show the already-declared quote fields. Run the focused tests.
- [x] 3. Add the route and decimal/revision semantics to
  `schema/api/README.md`. Regenerate all language bindings through the
  repository generator; do not edit generated output by hand.
- [x] 4. Run `make check`. Confirm the snapshot/event shape check and generated
  drift check pass, then commit the focused contract change on the task branch.

## Review focus

- Old persisted events must still validate and replay.
- A cost-only revision must not be mistaken for a new strategy-code version.
- `dispatch_attempted_at` must not be presented as proof of receipt or fill.
- Money and quantities must remain exact decimal strings on the stream.
- The contract addition must not accidentally create a new durable topic.
