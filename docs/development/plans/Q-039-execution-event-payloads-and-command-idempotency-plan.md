# Q-039 implementation plan: Execution event payloads and command idempotency

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-039-execution-event-payloads-and-command-idempotency-spec.md`](../specs/Q-039-execution-event-payloads-and-command-idempotency-spec.md)  
**Depends on:** Q-009

## Current-system context

`schema/stream/topics.yaml` declares `decisions`, `orders`, `fills`, `risk`,
`ledger` and `deployments` as durable, and each has
`payload_schema: schema/stream/envelope.schema.json`. Only the job topics have
payload schemas of their own (`schema/stream/payloads/job-*.schema.json`,
added by Q-009, with examples in `schema/stream/examples/`).
`tools/validate.py::check_stream_consistency` resolves `payload_schema` and
`check_stream_routing` checks `key` against `coalesce_key`. The execution
topics do not coalesce, so they have no routing check today.
`schema/stream/replay/` holds `watermark`, `history-page`, `history-expired`
and `latest`, but no execution snapshot. `tools/generate.py` emits every
`*.schema.json` under `api`, `catalog`, `edge` and `stream` to
`generated/{python,typescript,rust}`. `make generate-check` diffs a clean
generation against the committed output.

The backend's execution state lives in `q_backend/src/q_backend/storage/db/execution_models.py`
(`ExecutionDeployment`, `ExecutionDecision`, `ExecutionOrder`,
`ExecutionFill`, `ExecutionNetPosition`, `PaperAccount`,
`ExecutionLedgerEntry`, `ExecutionRiskEvent`, `ExecutionControlState`). Its enums are in
`q_backend/src/q_backend/execution/domain.py`: `DeploymentLifecycle`,
`DecisionOutcome`, `ExecutionOrderStatus`, `ReconciliationState`,
`RiskRejectionCode`, `LedgerEntryType`, `PositionSide`, `BrokerMode`. The API
response models in `q_backend/src/q_backend/api/schemas/execution.py` already
serialize decimals as strings. The frontend's view of the same data is
`q_frontend/src/types/execution.ts`.

`schema/edge/execution.yaml` says `intent_placement: … via
intent_magic(order_id) and intent_comment(order_id)`. Those functions are in
`q_backend/src/q_backend/execution/brokers/metatrader.py`:
`magic = (base ^ (uuid.int & 0x7FFFFFFF)) & 0x7FFFFFFF` with `base = 0`, and
`comment = "q:" + uuid.hex[:24]`. `schema/edge/examples/lookup-outcome-filled.json`
shows `"comment": "q-intent-018f"`, which that derivation can never produce.
`tests/test_gateway_capture.py` shows the established way to test against
backend source: `Q_BACKEND_PATH`, parsing rather than importing.

`schema/api/FINDINGS.md` Finding 3 records the missing idempotency keys and
Finding 4 the missing execution snapshot. Both are triaged "later task".

## Interfaces produced

```
schema/stream/payloads/execution-deployment.schema.json   ExecutionDeploymentState   (entity: deployment)
schema/stream/payloads/execution-decision.schema.json     ExecutionDecisionState     (entity: decision)
schema/stream/payloads/execution-order.schema.json        ExecutionOrderState        (entity: order; intent_id, status, reconciliation_state)
schema/stream/payloads/execution-fill.schema.json         ExecutionFillEvent         (entity: fill + position_after: ExecutionPosition)
schema/stream/payloads/execution-risk.schema.json         ExecutionRiskEvent         (oneOf kind: risk_rejection | kill_switch)
schema/stream/payloads/execution-ledger.schema.json       ExecutionLedgerEvent       (entity: ledger_entry + account_after: ExecutionAccount)
schema/stream/payloads/execution-common.schema.json       $defs: Decimal, ExecutionPosition, ExecutionAccount, ExecutionControl, vocabularies
schema/stream/replay/execution-snapshot.schema.json       ExecutionSnapshot {deployments, accounts, positions, orders,
                                                           recent: {decisions, fills, risk}, control, limits, watermark}
schema/stream/examples/execution-*.json                   one per entity kind + snapshot
schema/stream/topics.yaml                                 six payload_schema pointers changed
schema/api/idempotency.yaml                               header name, key format, ttl, covered commands, error codes
schema/api/error.schema.json                              + idempotency_key_required, idempotency_key_reused,
                                                           idempotency_in_progress
schema/edge/execution.yaml                                intent_placement → intent_derivation {formula, vectors}
schema/edge/examples/*.json                               comments/magics corrected to derived values
schema/edge/execution/account-response.schema.json      AccountResponse {login, server, currency, trade_allowed,
                                                           terminal_trade_allowed, balance, equity, margin_free}
schema/edge/execution.yaml                                + operation account: GET /v1/account
tools/validate.py                                         check_execution_payloads, check_idempotency, check_intent_vectors
generated/{python,typescript,rust}/*                      regenerated
```

Payload envelope-level conventions, applied to every execution payload:

```json
{
  "entity": "order",                    // const per schema, or kind discriminator on risk
  "id": "uuid",
  "deployment_id": "uuid",              // null only for account-level ledger events and the kill switch
  "account_id": "uuid",
  "updated_at": "RFC 3339 UTC",
  "...entity fields...": "decimals as strings matching ^-?\\d+(\\.\\d+)?$"
}
```

## Implementation decisions

- **Full-state payloads, not diffs.** The terminal's store applies events by
  replacing entities keyed by `(entity, id)`. Replacement makes at-least-once
  relay delivery harmless even before `seq` deduplication, and makes the
  snapshot and the event the same shape. The cost is a few hundred bytes per
  event on topics that see a handful of events per bar.

- **One `execution-common.schema.json` with `$defs`**, referenced by the six
  payloads and by the snapshot. Shared shapes cannot then drift between event
  and snapshot. The check in the validator compares resolved shapes anyway,
  because a local override inside a payload would otherwise go unnoticed.

- **Vocabularies are copied from `domain.py` enums verbatim**, including values
  such as `cancelled` that no current code path produces. A contract narrower
  than the database would reject a legitimate row.

- **Positions ride on fills, balances ride on ledger entries.** There is no
  `positions` or `accounts` topic in the policy, and adding one is a topic-policy
  change this phase does not need: every position change is caused by a fill,
  and every balance change by a ledger entry. The snapshot carries both
  collections for the initial state.

- **Kill switch is a `risk` event with `kind: kill_switch`**, because the kill
  switch is the global risk control and the terminal shows it beside risk
  rejections. `deployments` stays per-deployment.

- **Routing keys carry `deployment_id` (or `account_id`)** even though the topics
  do not coalesce. The Q-009 rule already allows keys on non-coalescing topics.
  The stream endpoint can later filter per deployment without decoding, and no
  consumer is allowed to depend on it.

- **Snapshot limits are declared in the schema** (`limits: {recent_decisions,
  recent_fills, recent_orders, recent_risk}`), with defaults of 50 each written
  in the example. The terminal then knows the snapshot is a window, and fetches
  older rows from the existing paged REST routes.

- **Idempotency lives in a policy document, `schema/api/idempotency.yaml`,**
  because the header must appear in the captured OpenAPI, and the capture comes
  from the backend (Q-044). The policy file is the contract the backend
  implements and the capture is later checked against:
  `header: Idempotency-Key`, key = UUID string, `ttl: PT24H`, the replay rule
  (same key + same method + path + body hash → stored status and body; a key
  whose first request has not committed yet → `409 idempotency_in_progress`
  with `Retry-After`), and
  `required_for`: create account, create deployment, deployment actions, kill
  switch update, order resolution. `optional_for` stays empty for now.

- **The derivation moves into the contract with vectors.** Five vectors: the
  nil UUID, the max UUID, one with the top bit of the low 31 bits set, and two
  random ones, each computed from the backend functions at a pinned commit.
  `magic_base` is fixed at 0 in the contract, because nothing in the backend
  sets another value. A test reads the functions from `Q_BACKEND_PATH` by
  parsing their source and evaluating only those two function bodies, the same
  technique `test_gateway_capture.py` uses. It is skipped when the variable is
  unset, as that test is.

- **The wrong `q-intent-018f` example comments are corrected** to derived values.
  They are examples, not wire changes, but a contract whose own examples violate
  its derivation would teach the wrong thing to the edge implementer.

- **`/v1/account` is a new operation, not new health fields.** Health is a
  shared schema (`edge/common/health`) that both edges serve, and the data
  gateway has no business reporting a trading account. The worker needs the
  login for the allowlist gate and `trade_allowed` for the trading-disabled
  rejection that `MetaTraderBroker._preflight` performs today. Balances are
  plain numbers here, as in every other edge schema, because they are MT5's
  own floats. Exact decimals begin at the ledger.

- **FINDINGS 3 and 4 are updated** to "contract declared by Q-039; implemented
  by Q-044 / Q-043", and not closed, because the routes do not exist yet.

## Ordered implementation

- [x] 1. Work on the branch `Q-039-execution-event-payloads-and-command-idempotency`
   in `q_contracts`, created from `development` by `./work start`. Confirm
   `make check` passes before any change.
- [x] 2. Write failing tests in `tests/test_execution_payloads.py`: every execution
   topic points at a non-envelope payload; one example per entity validates;
   a missing `id`, `deployment_id`, `position_after` or `account_after` fails;
   a numeric decimal fails; an unknown order status fails. Confirm they fail.
   Commit.
- [x] 3. Write `execution-common.schema.json` with the vocabularies from
   `domain.py` and the shared `$defs`, then the six payload schemas and their
   examples. Derive the fields from `execution_models.py` and from the API
   response models, and cross-check them against `q_frontend/src/types/execution.ts`.
   List any field the frontend shows that no payload carries, and add it.
   Point `topics.yaml` at the new schemas. Confirm step 2's tests pass. Commit.
- [x] 4. Add `check_execution_payloads` to `tools/validate.py`: execution topics
   must not point at the envelope, and every snapshot entity must resolve to the
   same shape as its payload entity. Add tests for both failure cases. Commit.
- [ ] 5. Write `schema/stream/replay/execution-snapshot.schema.json` and its example,
   with the six-topic watermark and `limits`. Add a test that it validates and
   that removing a topic from the watermark fails. Commit.
- [ ] 6. Write `schema/api/idempotency.yaml` and add the two error codes to
   `error.schema.json`. Add `check_idempotency` (header name present, TTL
   parses, every `required_for` entry names an operation present in
   `openapi.yaml`) and tests. Update `schema/api/README.md`. Commit.
- [ ] 7. Replace `intent_placement` in `schema/edge/execution.yaml` with
   `intent_derivation`: the formula, `magic_base: 0`, the rule that the edge
   derives and refuses disagreeing caller values (error code
   `intent_field_mismatch`, added to the edge error schema), and five vectors.
   Correct the edge examples. Add the `account` operation with its response
   schema, connected and disconnected examples, and tests. Add `check_intent_vectors` (vectors agree with the
   formula, computed in the validator) and
   `tests/test_intent_derivation.py` (vectors agree with the backend's functions
   via `Q_BACKEND_PATH`). Commit.
- [ ] 8. Regenerate: `uv run python tools/generate.py --out generated`. Confirm the
   new types appear in all three languages and `make generate-check` is clean.
   Commit.
- [ ] 9. Update `schema/stream/README.md` (execution topics section),
   `schema/edge/README.md`, and FINDINGS 3 and 4. Commit.
- [ ] 10. Run `make check` and
   `Q_BACKEND_PATH=/home/gui/projects/q/q_backend uv run pytest tests/test_intent_derivation.py`.
   Fix, re-run, commit.
- [ ] 11. **Human:** human-verifiable criteria 1 and 2.

## Validation

- **Unit:** each payload schema and example; decimal pattern; vocabularies;
  snapshot/payload shape equality; idempotency policy; derivation vectors.
- **Integration:** derivation vectors against backend source at a pinned path.
- **Regression:** every existing test, the envelope and control frames unchanged,
  `make generate-check` clean.
- **Manual:** payload parity read against the frontend workspace; derivation read
  against §6.2.

```bash
cd /home/gui/projects/q/q_contracts
make check
Q_BACKEND_PATH=/home/gui/projects/q/q_backend uv run pytest tests/test_intent_derivation.py -v
uv run pytest tests/test_execution_payloads.py tests/test_stream_consistency.py -v
```

## Handoff

List the six payload schemas with their entity fields. List every field that
step 3's frontend cross-check added. Give the five derivation vectors and
confirm the backend test ran, not skipped. Name the corrected edge examples.
Quote the new idempotency policy file and the account response schema. Give the commit that consumers should
pin, because Q-040, Q-043, Q-044 and Q-046 pin it.
