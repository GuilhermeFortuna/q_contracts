# Q-092: Bar completeness in the data gateway contract

**Status:** written spec awaiting human review; the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2) is the status of record.
**Batch:** 16 — Research data and backtest correctness
**Depends on:** none
**Implementation plan:** [Plan](../plans/Q-092-bar-completeness-in-the-data-gateway-contract-plan.md)

## Purpose

`schema/edge/data-gateway.yaml` describes `/v1/ohlcv` as "Bulk OHLCV bar history" and says nothing about limits. The gateway stops at 50,000 bars and answers HTTP 200 with the cut range, so a consumer cannot tell a complete range from a truncated one. On 2026-10-06 a five-year `WDO$N` `M10` request returned 50,000 bars ending 2025-05-13 while the terminal held 70,032 bars through that day.

The same contract already keeps the other bulk endpoints honest: `/v1/ticks` rejects an oversized range with `tick_range_too_large`, and `/v1/trades` reports `truncated` in its metadata. Bars do neither. This task defines how a bar response states its completeness so that Q-093 can implement it in the gateway and its client.

## Contract change

Edit `/v1/ohlcv` in `schema/edge/data-gateway.yaml` only.

- The response gains a `metadata` member: a JSON object stored in the archive's `metadata` entry, with the encoding `/v1/trades` already uses.
  - `truncated` (boolean): true when the gateway stopped at its bar limit before reaching `end`.
  - `max_bars` (integer, minimum 1): the limit the gateway applied to this response.
- A structured `continuation` rule records how a caller obtains the rest of a truncated range: request again with `start` set to one second after the last returned bar's time and the same `end`, and repeat until a response reports `truncated: false`. A continuation response may hold no bars.
- The endpoint description states the meaning of both values: with `truncated: true` the arrays hold the first `max_bars` bars of the inclusive range in ascending time; with `truncated: false` they hold every bar MetaTrader 5 supplied for it. Neither value is a statement about how much history the broker or terminal keeps.
- `equal_length_requirement` keeps applying to the arrays and not to `metadata`. Array names, dtypes and optionality are unchanged.

## Versioning

The change is additive under `VERSIONING.md`: one new response member, no request that was accepted becomes rejected, and existing arrays keep their shape. `schema_major` stays 1 and `schema_version` stays `"1.0"`, as for the additive `/v1/trades`.

Rejecting an oversized range, the approach `/v1/ticks` takes, was not chosen. It would tighten validation of previously accepted requests, which the versioning policy treats as breaking and which would require a parallel `/v2/` endpoint.

`data-gateway.yaml` is not a generator input, so no JSON Schema, generated binding or consumer vendored file changes.

## Acceptance

1. `uv run python tools/validate.py` reports no problems and `make generate-check` shows no generated diff.
2. A focused test loads the contract and asserts that `/v1/ohlcv` declares `metadata.truncated` as a boolean and `metadata.max_bars` as an integer, declares the continuation rule, and still declares exactly the existing arrays with their dtypes and optionality.
3. The same test asserts `/v1/ticks` and `/v1/trades` are unchanged in structure.
4. `COMPAT.md` gains a short Q-092 handoff note: Q-093 pins the merged commit; no consumer regeneration is needed.

## Delivery boundary

Contract text, one focused test and the compatibility note. No gateway or client code, no new error code and no change to other endpoints.

Two capture tests in `tests/test_gateway_capture.py` already fail when `Q_BACKEND_PATH` points at a backend checkout, because the gateway serves `/v1/ohlcv/recent` and `/v1/trades` routes the test's expected set does not list and the contract does not declare `/v1/ohlcv/recent`. The gateway also emits error codes the shared error vocabulary lacks (`invalid_count`, `invalid_datetime`, `invalid_range`, `missing_parameter` and per-lane 503 codes). That drift predates this task, is recorded in the Batch 16 document for a separate decision, and is not corrected here.
