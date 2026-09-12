# Q-004 implementation plan: Wine edge wire contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-004-wine-edge-wire-contracts-spec.md`](../specs/Q-004-wine-edge-wire-contracts-spec.md)  
**Depends on:** Q-001

## Current-system context

`q_backend/gateway/mt5_gateway.py` is a single stdlib-plus-`MetaTrader5`-plus-`numpy`
HTTP server, deliberately outside `src/` so it can never import `q_backend`. Its
contract is its module docstring, lines 16–58: `SCHEMA_VERSION = "1.0"` (line 94),
all endpoints under `/v1/`, a dispatch table at lines 719–724 mapping
`/v1/health`, `/v1/symbol_info`, `/v1/symbols/search`, `/v1/available_range`,
`/v1/ohlcv`, `/v1/ticks` to `_route_*` handlers, `COLUMNAR_TICK_KEYS =
("time_msc", "bid", "ask", "last", "volume", "flags")` at line 133, `.npz` bodies
as `application/octet-stream` for the two array routes with JSON for the rest,
`start`/`end` as ISO-8601 naive Brasília wall-clock passed through with no
timezone math, and `503 mt5_unavailable` when the terminal is not initialized
while `/v1/health` still answers 200. An optional `--token` requires an
`X-Gateway-Token` header. `gateway/systemd/` holds the unit files that run it.

On the Linux side, `src/q_backend/market_data/clients/remote.py` is the
protocol-compatible client for that gateway, sitting beside `metatrader.py`,
`local.py`, `yfinance.py` and `base.py`. The execution side already has the
identity primitives the edge needs but no edge to send them to:
`src/q_backend/execution/brokers/metatrader.py` defines
`intent_magic(order_id, *, base=0)` at line 44 and `intent_comment(order_id)` at
line 49, sets both on every submission at lines 197–206, and at line 353 already
documents the fallback of matching an intent's magic and comment against deal
history — the lookup semantics, implemented in-process against a direct MT5
import. The gap this task closes is that the gateway's contract lives inside its
implementation, and the execution edge's contract does not exist at all, so the
lookup semantics that protect against duplicate orders cannot be built against
anything.

## Interfaces produced

```
// q_contracts/schema/edge/
data-gateway.yaml            captured from mt5_gateway.py; schema major 1
execution.yaml               new; schema major 1
common/health.schema.json    shared health response shape
common/error.schema.json     shared edge error vocabulary
execution/*.schema.json      request and response schema per operation
examples/                    fixtures the validity tests load
OBLIGATIONS.md               the process-level rules both contracts impose
```

```yaml
# schema/edge/execution.yaml — operations, request -> response
quote:     {symbol}                       -> {symbol, bid, ask, last, time_msc, age_ms}
check:     {intent_id, order}             -> {allowed, retcode, margin, reason?}
submit:    {intent_id, order}             -> SubmitOutcome
lookup:    {intent_id, window_start, window_end} -> LookupOutcome
positions: {symbol?}                      -> [Position]
deals:     {window_start, window_end, magic?} -> [Deal]
```

```jsonc
// schema/edge/execution/submit-outcome.schema.json — exactly three outcomes
{
  "oneOf": [
    {"outcome": "accepted",      "order_ticket": "int64", "retcode": "int"},
    {"outcome": "rejected",      "retcode": "int", "reason": "string"},
    {"outcome": "indeterminate", "reason": "string"}
  ]
  // a fourth kind is not representable; "duplicate_intent" is an error response,
  // not an outcome, because it describes the caller and not the order
}

// schema/edge/execution/lookup-outcome.schema.json — exactly four outcomes
{
  "oneOf": [
    {"outcome": "filled",      "deals": "[Deal]", "closes_intent": true},
    {"outcome": "rejected",    "retcode": "int",  "closes_intent": true},
    {"outcome": "not_found",                       "closes_intent": true},
    {"outcome": "unavailable", "reason": "string", "closes_intent": false}
  ]
}
```

```python
# q_contracts/tools/validate.py  (extended)
def check_edge_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Both contracts declare a schema major and a health operation; the submit
    outcome union has exactly three members and the lookup union exactly four;
    every lookup member declares closes_intent; the submit request requires
    intent_id; the quote response requires age_ms."""

# q_contracts/tests/test_gateway_capture.py
def gateway_routes() -> set[str]:
    """Read the dispatch table out of q_backend/gateway/mt5_gateway.py by parsing
    it as source, never by importing it — importing pulls in MetaTrader5."""
```

## Implementation decisions

- **Two contract documents with independent schema majors, not one edge
  contract.** The data gateway is deployed and working; the execution edge is
  unwritten and will change several times before it carries an order. A shared
  major would force a version bump on the working process every time the
  unwritten one moved, and each bump on the gateway is a coordinated restart of a
  Wine service. Separate majors mean the gateway's `1.0` stays `1.0`.

- **The gateway contract is captured from the implementation, and any
  disagreement is resolved in favor of the implementation.** The running gateway
  is what the deployed Linux client already speaks; a contract that "corrects" it
  would make the contract and the deployment disagree, and the first casualty
  would be a market-data fetch that silently returns nothing. The spec says the
  contract is wrong in that case, and the plan follows it literally.

- **The gateway's routes are read by parsing the source, not by importing it.**
  `mt5_gateway.py` imports `MetaTrader5` at module scope; importing it from a
  test in `q_contracts` would either fail or pull the stub from `q_backend`'s
  `[tool.uv.sources]`, which is a dependency `q_contracts` must not have. Parsing
  the dispatch-table literal keeps the check honest and keeps the repository
  self-contained as Q-001 requires.

- **`duplicate_intent` is an error response, not a fourth submit outcome.** An
  outcome describes what happened to the order; a duplicate submission means
  nothing happened to any order and the caller has a bug or has lost its state.
  Modelling it as an outcome would let a caller write a switch that treats it
  alongside `rejected` and mints a fresh intent — which is precisely the path
  that produces a second real order.

- **`indeterminate` is a first-class outcome rather than an HTTP error.** A
  timeout, a transport failure, and an unknown retcode are indistinguishable from
  the caller's side, and all three mean the same thing: an order may exist. If
  they arrive as errors, the natural client idiom is a retry, and a retry here is
  a duplicate order. Making it an outcome forces the caller to handle it in the
  same expression where it handles success.

- **`lookup` returns `closes_intent` as an explicit field per outcome rather than
  leaving it to the caller's table.** The distinction between `not_found`
  (closes: the order does not exist and never will in this window) and
  `unavailable` (does not close: we could not look) is the single most dangerous
  judgement in the protocol, and a caller that re-derives it from the outcome name
  will eventually get it backwards. Putting the answer in the payload means the
  contract carries it and the generated types carry it into every consumer.

- **`quote` returns `age_ms` computed by the edge rather than a timestamp the
  caller subtracts from its own clock.** The Wine prefix's clock and the Linux
  clock are the same host clock today, but the fallback topology in §6.3 is a
  Windows VM, where they are not. A freshness gate built on cross-host clock
  subtraction fails open — it reports stale data as fresh when the remote clock
  runs ahead — and failing open is the one direction this gate must never fail.

- **The intent identifier's placement in the broker-visible fields is part of the
  contract, named as the same `magic` and `comment` derivation the worker already
  uses.** `intent_magic` and `intent_comment` exist and work; specifying a new
  placement would mean the edge and the existing in-process broker path write
  different markers, and the lookup that searches deal history would miss orders
  placed by the other path during any transitional period.

- **The standard-library-only obligation is written in a shared `OBLIGATIONS.md`
  that both contracts reference, rather than repeated in each.** Repeating it
  means two copies that can be relaxed independently, and the relaxation is
  invisible: a process that imports one extra package works on the developer's
  machine and fails inside the Wine prefix, which is where nobody is debugging.

- **No response is described as "may also return other fields".** Additive
  changes are the repository's default per Q-001's `VERSIONING.md`, and that rule
  already covers extension. Writing an explicit escape hatch into a
  money-carrying contract invites an implementation to smuggle semantics into
  undocumented fields.

## Ordered implementation

1. Create the branch `Q-004-wine-edge-wire-contracts-spec`.
2. Write `tests/test_gateway_capture.py::test_gateway_routes_parse` first, failing:
   parse `../q_backend/gateway/mt5_gateway.py` as source, extract the dispatch
   table literal, and assert it yields exactly the six `/v1/` paths. Confirm it
   fails because the helper does not exist; implement `gateway_routes`; confirm
   it passes. Commit. Note the path to `q_backend` is supplied by an environment
   variable with no default, so the repository still contains no sibling path.
3. Write `schema/edge/common/health.schema.json` and
   `schema/edge/common/error.schema.json`, the latter declaring the vocabulary the
   gateway already uses including `mt5_unavailable`. Write failing tests that a
   health example with `{status, schema_version, mt5_connected, terminal_build}`
   validates and that one missing `mt5_connected` fails. Confirm, implement,
   confirm. Commit.
4. Write `schema/edge/data-gateway.yaml` declaring schema major 1, the six
   operations with their exact query parameters, the JSON responses for four of
   them, and the binary `.npz` responses for `/v1/ohlcv` and `/v1/ticks` including
   array names, dtypes, and the equal-length requirement. Declare the
   naive-wall-clock timestamp convention and the no-conversion rule. Declare the
   optional `X-Gateway-Token` header. Commit.
5. Write failing tests: the contract's declared paths equal `gateway_routes()`;
   the contract's `schema_version` string equals the `SCHEMA_VERSION` literal
   parsed from the gateway source; the contract's tick array names equal the
   `COLUMNAR_TICK_KEYS` tuple parsed from the same file, in order; the contract
   text asserts a naive wall-clock interpretation. Confirm they fail, correct the
   contract until they pass. Commit.
6. Write a failing test that loads a real `.npz` fixture produced by the running
   gateway's `/v1/ticks` (checked into `tests/fixtures/`) and asserts its array
   names and dtypes match the contract field-for-field. Confirm it fails, correct
   the contract to match the artifact, confirm it passes. Commit.
7. Write `schema/edge/OBLIGATIONS.md`: stdlib plus MetaTrader plus the array
   library only, never import `q_backend`, expose health with connectivity and
   terminal build, refuse a mismatched schema major, and — for the execution edge
   — bind to loopback only. Reference it from both contracts. Commit.
8. Write the execution edge request and response schemas under
   `schema/edge/execution/`: `order.schema.json`, `submit-request`,
   `submit-outcome`, `lookup-request`, `lookup-outcome`, `quote-response`,
   `check-response`, `position`, `deal`. Commit.
9. Write failing validity tests, one per acceptance criterion: a submit example
   without `intent_id` fails naming that field; a submit outcome with
   `"outcome": "duplicate_intent"` fails; each of the three legal submit outcomes
   validates; each of the four lookup outcomes validates and carries
   `closes_intent` with the values `true, true, true, false` respectively; a quote
   example without `age_ms` fails. Confirm they fail, implement the schemas until
   they pass. Commit.
10. Write `schema/edge/execution.yaml` declaring schema major 1 and the six
    operations against those schemas, stating in prose the at-most-one-submission
    rule, the never-retry rule, the stateless-across-restarts rule, and that a
    transport timeout is indistinguishable from `indeterminate`. Commit.
11. Write failing tests for `check_edge_consistency`, one per rule listed in its
    docstring, each over a temporary tree violating exactly that rule. Confirm they
    fail, implement, wire into `check_tree`, confirm they pass. Commit.
12. Human step, matching human-verifiable criterion 1: read `execution.yaml`
    against §6.2 and §6.3 and confirm no path exists by which one `intent_id`
    yields two submissions; record the paths considered.
13. Human step, matching human-verifiable criterion 2: diff the contract against
    lines 16–58 of `mt5_gateway.py` and confirm every behavioral statement is
    present or recorded as intentionally dropped.
14. Run the full validation suite and commit. Report the handoff.

## Validation

- **Unit:** each `check_edge_consistency` rule; each schema accept/reject pair in
  step 9; health schema accept and reject.
- **Integration:** `make check` over the whole tree, including Q-002's and Q-003's
  consistency checks alongside this task's.
- **Regression:** the captured gateway contract is compared against the running
  implementation on three axes — route set, schema version literal, and tick key
  tuple — plus a real `.npz` artifact. This is the locked baseline: the gateway's
  wire is `1.0` and must stay byte-compatible; a future change to
  `mt5_gateway.py` that alters any of the three fails these tests.
- **Manual:** steps 12 and 13.

```bash
cd /home/gui/projects/q/q_contracts
make check
Q_BACKEND_PATH=/home/gui/projects/q/q_backend uv run pytest tests/test_gateway_capture.py -v
uv run pytest tests/ -k edge -v
```

## Handoff

Report the six gateway paths as parsed from the dispatch table alongside the six
declared in the contract, and the `SCHEMA_VERSION` literal alongside the
contract's declared version, so the capture is shown to be faithful rather than
asserted. Report the tick array names and dtypes read from the real `.npz`
fixture beside the contract's declaration. For the execution edge, report the
three submit outcomes and the four lookup outcomes with their `closes_intent`
values, and state in one sentence per case what a caller must do on each — that
sentence is what the worker will be built from. Report the result of the
human review in step 12 as the list of paths considered by which one intent could
produce two submissions, and why each is closed. Report any behavioral statement
from the gateway docstring that was intentionally dropped, with its reason.
Confirm that `q_contracts` still contains no committed path into a sibling
checkout, and that the gateway source is reached only through an environment
variable with no default.
