# Q-066: Paper deployment contract extensions

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** [`docs/system-architecture.md` §4.2, §4.5, §6.1, §9](../../system-architecture.md)  
**Depends on:** Q-039 (Done)  
**Implementation plan:** [`../plans/Q-066-paper-deployment-contract-extensions-plan.md`](../plans/Q-066-paper-deployment-contract-extensions-plan.md)

## Purpose

The execution stream identifies a deployment by strategy name and compiled-config
hash, but does not identify a configuration revision or the paper costs applied
to its fills. The order payload has no explicit dispatch-attempt timestamp.
Q-067 and Q-068 need those fields before the terminal can audit an edited paper
deployment from decision to simulated fill. This task extends the existing
contracts additively. It does not build a second execution path.

## Requirements

### Revision and cost snapshots

- A deployment has `config_revision`, a positive integer distinct from
  `strategy_version`. Revision 1 is created with the deployment; each accepted
  configuration edit increments it once. `strategy_version` continues to name
  strategy implementation compatibility, not operator edits.
- Deployment and decision payloads carry `config_revision` and
  `paper_cost_config`. The latter is an object with exact-decimal string fields
  `point_value`, `slippage_points`, `cost_per_contract`, and `cost_bps`.
  Quote freshness remains a system risk setting. These fields are snapshots, so
  older decisions retain the costs and revision that produced them.
- The existing execution snapshot uses the same deployment and decision shapes
  as the durable events. A terminal that replaces state by entity ID continues
  to converge after edits and replay.
- Additions are optional at the schema level so historical version-1 events
  remain valid. New Q-067/Q-068 producers always populate them. The schema
  major remains 1.

### Dispatch and paper receipt

- Order payloads gain nullable `dispatch_attempted_at`: the time the worker
  durably records that it is about to call its broker adapter. It is evidence
  of an attempted dispatch, not proof that the adapter received the call.
- Existing `submitted_at`, terminal status, reconciliation fields and
  `rejection_reason` remain the broker-result record. An ambiguous crash stays
  `unknown` until reconciled; no contract text equates `dispatch_attempted_at`
  with a fill.
- Fill payloads already carry `quote_bid`, `quote_ask`, `quote_timestamp`,
  `price`, `fee` and `slippage`; the example must show all of them for a paper
  fill. The documented audit chain is decision ID → order intent ID → dispatch
  attempt → paper fill/rejection → ledger and position.

### Control API shape

- Document the Q-067 catalog/create/edit routes and Q-068 paper-performance
  routes in `schema/api/README.md`, including `Idempotency-Key` on create/edit,
  decimal strings for money, and revision-conflict behavior. The backend tasks
  recapture their actual OpenAPI after implementation; this task does not hand
  edit generated OpenAPI.
- Paper performance history is paged REST data. It is not added to the six
  durable execution topics: the terminal fetches it on deployment selection
  and when a completed-bar deployment event arrives.

## Constraints and non-goals

- No backend, terminal, MT5 edge or `q_core` implementation in this task.
- No new stream topic, envelope change, changed event retention or new broker
  mode. Existing consumers must be able to ignore the additive fields.
- No claim that a top-of-book quote proves market depth or actual broker fill.

## Acceptance criteria

1. Deployment and decision examples with revision 1 and decimal cost fields
   validate; revision 0 or JSON-number money fails. Historical examples without
   the new fields still validate.
2. The execution snapshot validates with the new deployment and decision
   shapes, and its entity-shape parity check passes.
3. Order examples cover `dispatch_attempted_at` as a timestamp or null. An
   unknown order with a dispatch attempt and no fill remains valid.
4. A paper fill example includes quote side, timestamp, fill price, fee and
   slippage; the example validates without implying broker execution.
5. Generated Python, TypeScript and Rust models are regenerated from the source
   schemas, `make check` passes, and the consumer vendoring order is documented.
