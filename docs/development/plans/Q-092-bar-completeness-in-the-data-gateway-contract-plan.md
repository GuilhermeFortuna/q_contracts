# Q-092 implementation plan: Bar completeness in the data gateway contract

> **For implementation agents:** Read the linked specification and repository instructions. Use superpowers:executing-plans when available. Launch only through `./work start Q-092 --agent <agent> --worktree` after written-plan approval. Implement natively; delegation requires separate authorization.

**Goal:** Define completeness metadata and the continuation rule for `/v1/ohlcv`.
**Architecture:** One additive edit to the descriptive YAML contract, pinned by a focused structural test.
**Tech stack:** YAML, Python 3.12, pytest, the repository's `tools/validate.py`.
**Spec:** [Specification](../specs/Q-092-bar-completeness-in-the-data-gateway-contract-spec.md)
**Status:** written plan awaiting human review.

## Global constraints

- Additive only: `schema_major` 1 and `schema_version` `"1.0"` are unchanged; no array is renamed, retyped or made required.
- Edit `schema/edge/data-gateway.yaml` by hand; it is a source file. Do not edit anything under `generated/`.
- No new error code, JSON Schema or generator change. If one appears necessary, stop and report it rather than widening the task.
- Leave the pre-existing capture-test drift named in the spec alone.
- Commit focused changes on the task branch; no push, merge or protected-branch checkout.

## Review focus

- The metadata encoding matches `/v1/trades` (a JSON object in the `metadata` archive entry), so one client parser pattern serves both.
- The continuation rule is unambiguous about the next `start` (last returned bar time plus one second) and about an empty final page.
- The wording does not promise broker or terminal history completeness.

## Ordered implementation

### 1. Declare completeness metadata on `/v1/ohlcv`

**Files:** Modify `schema/edge/data-gateway.yaml`. Create `tests/test_ohlcv_completeness_contract.py`.
**Interfaces:** `/v1/ohlcv` `response.metadata.truncated` (boolean), `response.metadata.max_bars` (integer, minimum 1), and a structured `response.continuation` entry naming the next `start` and the unchanged `end`.

- [x] Add the focused test first. Load the YAML and assert the two metadata fields with their types, the continuation entry, the unchanged array names, dtypes and `optional` flags of `/v1/ohlcv`, and that `/v1/ticks` and `/v1/trades` keep their current array and metadata keys.
- [x] Run `uv run pytest tests/test_ohlcv_completeness_contract.py -q` and confirm it fails on the missing metadata, not on an import or path error.
- [x] Edit the contract: add `metadata` and `continuation`, and extend the endpoint description with the meaning of `truncated` true and false as the spec states it.
- [x] Run `uv run pytest tests/test_ohlcv_completeness_contract.py tests/test_edge_consistency.py tests/test_trade_contracts.py -q` and confirm they pass.
- [x] Commit this unit with a conventional message.

### 2. Record the consumer handoff

**Files:** Modify `COMPAT.md`.

- [x] Add a "Q-092 bar completeness handoff" note in the style of the Q-079 note: the change is additive and YAML-only, no generated output changes, and Q-093 updates `q_backend`'s `CONTRACTS_REV` to the merged commit.
- [x] Commit the note.

## Verification and handoff

- [x] Run `uv run python tools/validate.py` and `make generate-check`; confirm no problems and no generated diff.
- [x] Run `make check` once. The capture tests that need `Q_BACKEND_PATH` are skipped there by design; do not set that variable to chase the pre-existing route drift.
- [x] Record the commands actually run and their results in this plan; do not claim unrun checks passed.
- [x] Use `./work board set Q-092 in-review -m "<changes; checks and results; follow-ups>"`. Human review and finish own integration and publication, and Q-093 needs the merged commit to be reachable on the remote.

### Verification evidence

- `uv run pytest tests/test_ohlcv_completeness_contract.py -q`: failed initially on missing description/metadata assertions (`1 failed, 2 passed in 0.07s`), passed after contract updates (`3 passed in 0.06s`).
- `uv run pytest tests/test_ohlcv_completeness_contract.py tests/test_edge_consistency.py tests/test_trade_contracts.py -q`: `24 passed in 1.44s`.
- `uv run python tools/validate.py`: clean, exited 0 with no problems.
- `make generate-check`: generated 17 files, diff clean, exited 0.
- `make check`: `229 passed, 7 skipped, 1 deselected in 9.85s`, exited 0.

