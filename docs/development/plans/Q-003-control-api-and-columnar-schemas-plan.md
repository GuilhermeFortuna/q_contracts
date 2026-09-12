# Q-003 implementation plan: Control API and columnar payload schemas

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-003-control-api-and-columnar-schemas-spec.md`](../specs/Q-003-control-api-and-columnar-schemas-spec.md)  
**Depends on:** Q-001

## Current-system context

`q_backend` is a FastAPI application assembled in
`src/q_backend/api/main.py`, which mounts fourteen routers at lines 43–56:
`system`, `strategies`, `strategy_builder`, `market`, `backtest`, `optimization`,
`walkforward`, `strategy_search`, `features`, `neural`, `execution`,
`experiments`, `storage`, `news`. Their request and response models live in
`src/q_backend/api/schemas/` as fourteen Pydantic modules of the same names, plus
`common.py`, which today holds only `BulkDeleteBacktestsRequest`,
`BulkDeleteOptimizationsRequest`, and `BulkDeleteResponse` — there is no shared
error model. Job orchestration lives beside the routers in
`api/backtest_jobs.py`, `api/optimization_jobs.py`, `api/neural_jobs.py`,
`api/alpha_research_jobs.py`, `api/discovery_ab_jobs.py`, and
`api/encoder_ablation_jobs.py`; `backtest_jobs.py` writes progress through
`_persist_progress(run_id, status, error)` at line 83 using the bare strings
`"running"`, `"completed"`, `"failed"`, and `_status_for_run` at line 325 reads
live Redis progress and falls back to the database row.

What already exists and is under-used: FastAPI generates an OpenAPI document
from those Pydantic models at `/openapi.json` with no extra work, and
`q_frontend/src/types/` already contains twelve hand-written mirrors
(`backtesting.ts`, `execution.ts`, `optimization.ts`, and so on) whose only reason
to exist is that nothing consumes the generated document. On the columnar side,
`src/q_backend/market_data/local_store.py` writes Parquet through
`_write_year_parquet` and `_month_parquet_path`, with bar columns taken from the
`OHLCV` model in `market_data/models.py`, and `gateway/mt5_gateway.py` defines
`COLUMNAR_TICK_KEYS = ("time_msc", "bid", "ask", "last", "volume", "flags")` at
line 133 with `time` as raw MT5 epoch seconds and start/end parameters as
**naive Brasília wall-clock** strings — a convention stated only in that module's
docstring. The gap this task closes is that the generated document is thrown
away, the hand-written mirrors are authoritative for the frontend, and the
columnar conventions exist only in prose.

## Interfaces produced

```
// q_contracts/schema/api/
openapi.yaml                 the captured control surface
error.schema.json            the single error shape, referenced by every failing operation
FINDINGS.md                  discrepancies found while capturing, one per heading
examples/jobs/*.json         one example per job lifecycle payload

// q_contracts/schema/api/arrow/
bars.schema.json             OHLCV columnar batch
ticks.schema.json            tick columnar batch
```

```jsonc
// schema/api/arrow/bars.schema.json — Arrow field declarations
{
  "name": "bars",
  "fields": [
    {"name": "time",         "type": "timestamp[s]",  "nullable": false,
     "tz": "naive-wallclock-America/Sao_Paulo",
     "doc": "raw MT5 epoch seconds as returned by copy_rates_range; no timezone math applied"},
    {"name": "open",         "type": "float64", "nullable": false},
    {"name": "high",         "type": "float64", "nullable": false},
    {"name": "low",          "type": "float64", "nullable": false},
    {"name": "close",        "type": "float64", "nullable": false},
    {"name": "tick_volume",  "type": "int64",   "nullable": false, "unit": "ticks"}
  ]
}
```

```jsonc
// schema/api/arrow/ticks.schema.json — field order matches COLUMNAR_TICK_KEYS exactly
{
  "name": "ticks",
  "fields": [
    {"name": "time_msc", "type": "timestamp[ms]", "nullable": false,
     "tz": "naive-wallclock-America/Sao_Paulo"},
    {"name": "bid",      "type": "float64", "nullable": false},
    {"name": "ask",      "type": "float64", "nullable": false},
    {"name": "last",     "type": "float64", "nullable": false},
    {"name": "volume",   "type": "int64",   "nullable": false},
    {"name": "flags",    "type": "uint32",  "nullable": false,
     "doc": "MT5 tick flag bitfield, passed through unmodified"}
  ]
}
```

```python
# q_contracts/tools/capture_api.py
def fetch_openapi(base_url: str) -> dict:
    """GET {base_url}/openapi.json from a running q_backend."""

def normalize(document: dict) -> dict:
    """Strip volatile keys and sort every mapping so two captures diff cleanly."""

def routes_of(document: dict) -> set[tuple[str, str]]:
    """(path, lowercase method) pairs, the comparison unit for drift."""

# q_contracts/tools/validate.py  (extended)
def check_api_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Every failing operation references error.schema.json; every arrow schema
    resolves under the identifier form topics.yaml uses; every declared field
    carries a type, and timestamp fields carry a tz."""
```

## Implementation decisions

- **The document is captured from the running application, not written by hand.**
  A hand-written OpenAPI document for a fourteen-router surface is wrong on the
  day it is finished and wrong differently every day after. Capturing means the
  description's accuracy is a property of a command, and the drift test in step 9
  turns that property into a failing build rather than a runtime surprise in a
  workspace nobody opened this week.

- **The captured document is normalized before being committed.** FastAPI's
  generator emits mappings in construction order and includes keys that vary
  between runs; committing the raw output makes every capture a large, unreadable
  diff and makes the drift test compare noise. `normalize` sorts and strips so
  that a real change is visible and a re-run is a no-op.

- **Drift is compared on `(path, method)` pairs rather than on the whole
  document.** Comparing whole documents makes the test fail on every harmless
  description edit, and a test that fails for harmless reasons gets deleted. The
  pair set is the part whose disagreement is always a real defect: an endpoint
  the contract promises and the backend does not serve, or the reverse.

- **A single `error.schema.json` is introduced even though the backend has no
  shared error model today.** Every consumer must handle failure, and fourteen
  per-router shapes means fourteen client branches. Declaring one shape now, and
  recording the backend's divergence from it as a finding, puts the work where it
  belongs: the contract states the target, the finding names the gap, and a later
  task closes it. Declaring nothing would leave each consumer to invent one.

- **Discrepancies become `FINDINGS.md` entries, never silent fixes.** A field the
  frontend reads that the backend never sends is not a schema defect — it is a
  frontend bug with a schema symptom, and reconciling it inside a schema change
  hides it. Each finding names the endpoint or field, the expectation, and the
  observed behavior, and is triaged by a human in the acceptance step.

- **The bar timestamp is declared `timestamp[s]` with an explicit
  `naive-wallclock-America/Sao_Paulo` convention rather than UTC.** The existing
  pipeline passes naive datetimes straight to `copy_rates_range` and the gateway
  does no timezone math by contract (`mt5_gateway.py` docstring, lines 41–45).
  Declaring these as UTC would be a one-line change that silently shifts every
  stored bar by the offset, and the error would appear as a plausible-looking
  three-hour skew in backtests rather than as a crash. The convention is ugly and
  it is what the data is; a later task may migrate it, and that migration needs
  this declaration to exist first.

- **`flags` is `uint32` and documented as passed through unmodified.** Decoding
  the MT5 tick flag bitfield into named booleans in the contract would fix the
  meaning of bits that MetaQuotes owns and that the gateway currently forwards
  verbatim; a bit added upstream would then be lost rather than merely unnamed.

- **Tick field order matches `COLUMNAR_TICK_KEYS` exactly.** The gateway builds
  `.npz` arrays under those keys and the client reads them back by name, but
  Q-006 will generate Rust and C++ struct definitions where order is layout.
  Matching the existing tuple order means the generated struct and the existing
  producer describe the same thing in the same sequence, and a reviewer comparing
  them sees a match rather than a permutation.

- **The columnar schemas live under `schema/api/arrow/` and not under
  `schema/stream/`, despite being referenced by the topic policy.** A bar is the
  same bar whether it arrives over the stream or from a REST history call; filing
  it under the stream would imply otherwise and would leave the REST description
  referencing across a boundary directory. `check_api_consistency` verifies the
  identifiers resolve in the form `topics.yaml` uses, so the cross-reference is
  enforced rather than assumed.

- **`make check-live` is a separate target from `make check`.** `make check` must
  run with nothing else running, because it is what CI runs and what an author
  runs on every save. Requiring a live backend would make the common case
  fail for an irrelevant reason. The live check is a deliberate, human-invoked
  step, and it is the one the acceptance criteria name.

## Ordered implementation

1. Create the branch `Q-003-control-api-and-columnar-schemas-spec`.
2. Write `tools/capture_api.py` with `fetch_openapi`, `normalize`, and
   `routes_of`. Write the failing unit tests first, over a small fixture
   document: `normalize` is idempotent (`normalize(normalize(d)) == normalize(d)`),
   `normalize` sorts a two-key mapping into key order, and `routes_of` over a
   fixture with `GET /a` and `POST /a` returns exactly `{("/a","get"),("/a","post")}`.
   Confirm they fail, implement, confirm they pass. Commit.
3. Start `q_backend` locally, run the capture, and commit the normalized
   `schema/api/openapi.yaml`. Record in the commit message the backend commit hash
   it was captured from.
4. Write `schema/api/error.schema.json` declaring the single error shape. Write a
   failing test that it validates an example error body and rejects one missing
   its message field. Confirm failure, implement, confirm pass. Commit.
5. Walk the fourteen routers against the captured document and write
   `schema/api/FINDINGS.md`, one heading per discrepancy, each naming the endpoint
   or field, the expectation, and the observed behavior. Include at minimum: the
   absence of a shared error model; any operation that can fail without declaring
   an error response; any path in `q_frontend/src/api/client.ts` or
   `src/api/queries/` with no counterpart in the captured document; the absence of
   the stream-protocol history and `latest` endpoints §4.2 requires. Commit.
6. Add job lifecycle examples under `schema/api/examples/jobs/` — submission, the
   returned identifier, a running status, a progress value, a terminal success,
   and a terminal error — using the literal status strings `"running"`,
   `"completed"`, `"failed"` that `_persist_progress` writes. Write a failing test
   that each validates against its operation's schema in the captured document.
   Confirm failure, fix the examples or record a finding where the document and
   the running behavior disagree, confirm pass. Commit.
7. Write `schema/api/arrow/bars.schema.json` and `ticks.schema.json` as above.
   Commit.
8. Write a failing test that reads a real stored artifact from the lake — a
   Parquet file produced by `local_store._write_year_parquet` and an `.npz`
   produced by the gateway's `/v1/ticks` route, both checked into
   `tests/fixtures/` — and asserts that its column names and dtypes match the
   Arrow schema field-for-field in order. Confirm it fails, correct the schema to
   match the data (never the reverse), confirm it passes. Commit.
9. Write failing tests for `check_api_consistency`: an arrow schema with a field
   lacking a `type` yields one problem naming the field; a timestamp field lacking
   `tz` yields one problem naming it; an operation declaring a failure response
   that does not reference `error.schema.json` yields one problem naming the
   operation; a `payload_schema` identifier in `topics.yaml` that does not resolve
   to a file under `schema/api/arrow/` yields one problem. Confirm they fail,
   implement, wire into `check_tree`, confirm they pass. Commit.
10. Add the `check-live` Make target and the drift test it runs: fetch
    `/openapi.json` from `Q_API_BASE_URL` (default `http://127.0.0.1:8000`),
    normalize it, and assert `routes_of(captured) == routes_of(committed)`, failing
    with the symmetric difference printed. The test skips, rather than fails, when
    the backend is unreachable, so `make check` stays green offline. Commit.
11. Human step, matching human-verifiable criterion 2: start the backend, run
    `make check-live`, and exercise at least one operation per router, confirming
    each response validates.
12. Human step, matching human-verifiable criterion 1: triage every entry in
    `FINDINGS.md` as a later task or an accepted deviation, recording the decision
    beside it.
13. Run the full validation suite and commit. Report the handoff.

## Validation

- **Unit:** `normalize` idempotence and sort order; `routes_of` pair extraction;
  error schema accept and reject; each `check_api_consistency` rule against a tree
  violating exactly that rule.
- **Integration:** every job lifecycle example validates against the captured
  document; `make check` runs discovery, per-file checks, stream consistency from
  Q-002, and API consistency in one pass.
- **Regression:** the Arrow schemas are compared against real artifacts —
  a lake Parquet file and a gateway `.npz` — field name, dtype, and order. This is
  the locked baseline: if a later task changes the schema, this test is what
  catches that stored data no longer matches it.
- **Manual:** steps 11 and 12.
- **Measurement:** none. This task claims no performance property.

```bash
# capture and offline validation
cd /home/gui/projects/q/q_contracts
make check
uv run pytest tests/ -k "api or arrow" -v

# live drift check, criterion 2
cd /home/gui/projects/q/q_backend && uv run uvicorn q_backend.api.main:app --port 8000 &
cd /home/gui/projects/q/q_contracts && make check-live
```

## Handoff

Report the `q_backend` commit hash the document was captured from and the count of
paths and operations captured, broken down by router, so the coverage claim is
checkable rather than asserted. Report every entry in `FINDINGS.md` with its
triage decision, and call out separately any finding that is a live defect rather
than a description gap — a frontend reading a field the backend does not send is
the case to name loudly. Report the exact column names and dtypes read from the
real Parquet and `.npz` fixtures alongside the schema's declared fields, so the
match is shown rather than claimed. State explicitly whether the bar timestamp
convention was confirmed to be naive Brasília wall-clock in the stored data, and
what evidence was used. Confirm `make check` passes with no backend running.
