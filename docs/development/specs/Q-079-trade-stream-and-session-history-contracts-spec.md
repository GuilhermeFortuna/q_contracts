# Q-079: Trade stream and session history contracts

**Status:** implementation complete on the local task branch; awaiting review. The [Q project board](https://github.com/users/GuilhermeFortuna/projects/2) remains the status of record.
**Batch:** 13 — persistent terminal setup and live market analysis
**Depends on:** Q-009
**Implementation plan:** [Plan](../plans/Q-079-trade-stream-and-session-history-contracts-plan.md)

## Purpose

Define a complete, ordered tape data path with session history, replay and explicit coverage.

## Current system

quotes carries the existing ticks Arrow schema but coalesces per symbol. That topic is suitable for latest quotes, not trade totals. Existing replay uses topic/epoch/seq; ticks currently declare an ambiguous naive-wallclock label despite forwarding raw MT5 epochs. New trade contracts must make UTC explicit without reinterpreting existing payloads.

## Required behavior

- Add trades as an ephemeral, non-coalescing topic with lag-on-overflow, retention duration P1D and 200000 retained batch entries. Batches contain at most 4096 source records. Replay is retention_only; session history is a separate source. Add trades.status as an ephemeral latest-per-symbol control topic with PT1H/10000 retention, coalescing on symbol. Its payload includes provider_id, symbol, source_generation, volume field/unit, covered bounds, coverage state/reason and last trade watermark. Status has its own topic sequence; it never substitutes for trade replay.
- Add a distinct trade Arrow schema. Required columns: time_msc timestamp[ms] UTC, price float64, volume float64, raw_flags int32, occurrence int64. Context binds provider_id, symbol, source_generation, exchange timezone/session key and a stable volume_unit to each snapshot/stream delivery. Side is derived in q_core, not guessed by the gateway.
- Record identity is (provider_id, symbol, source_generation, time_msc, occurrence), where occurrence is the zero-based source position among eligible trades at that millisecond. Preserve multiplicity, including equal rows; do not deduplicate by timestamp or price/volume hash. A source prefix/order correction changes source_generation and requires a new session snapshot.
- Eligible trades have a LAST/VOLUME/BUY/SELL update flag, finite positive price and volume. Quote-only rows are excluded even if they carry the prior last/volume. Both/neither aggressor flags remain eligible but have unknown side. Invalid trade records are counted and make source coverage incomplete.
- Declare additive /v1/trades gateway support: UTC half-open range inputs, COPY_TICKS_ALL retrieval followed by eligibility filtering, source-order occurrence assignment over complete millisecond groups, raw volume plus optional volume_real, availability and range-completeness metadata. Keep /v1/ticks unchanged.
- Add GET /api/v1/market/trades/snapshot?symbol= returning a snapshot token, current session bounds, source context, frozen trades watermark, coverage, counts and first-page URL. Add GET /api/v1/market/trades/history?snapshot_id=&cursor=&limit= returning Arrow IPC with generated metadata headers and a next cursor. Default page size 10000; max 50000.
- History pages are immutable for the token. Tokens are opaque, bound to one symbol/source generation/watermark, expire after 10 minutes, and return 410 on expiry; missing symbol returns 404, source absence 503. In-progress backfill returns 202 with Retry-After: 1 and a status token, never an empty complete snapshot.
- Each history page carries snapshot_id, source_generation, symbol, volume field/unit, page count, frozen epoch/seq and next_cursor in generated response headers; the header declarations use the X-Q-Trade- prefix. Snapshot cuts exclude the current millisecond group; the publisher carries it into a later live batch after it is closed. The snapshot watermark is captured by the same publisher coordinator that serializes session prefix and live delivery. Subscribe/buffer, load pages, discard transport entries at/below watermark, then apply higher sequences exactly once.
- Distinguish range coverage (complete/partial/unavailable plus bounds and reason) from aggressor-classification coverage. Complete means the provider successfully served the entire requested range with no truncation, invalid records or unfilled transport/source gap; it is not a claim about exchange-feed omissions.
- Publisher restart/source replacement invalidates snapshot generation. Replay expiry or a changed epoch requires another session snapshot; latest-per-key is never a tape recovery mechanism.

## Interfaces and ownership

q_contracts owns wire schemas and generated metadata; hosts own ingestion/storage and presentation.
Define schema/api/arrow/trades.schema.json, schema/stream/replay/trade-snapshot.schema.json, trade-history response/header declarations, schema/stream/payloads/trade-source-status.schema.json and schema/edge/data trade endpoint declarations. Extend stream control/context declarations additively; retain existing envelope schema_major 1 and existing ticks semantics. Generate Python/TypeScript/Rust output and update COMPAT.md for consumer handoff.

## Acceptance criteria

1. Schema/examples cover live batches, complete/partial snapshots, paged Arrow history metadata, 202/410/503 and source-generation replacement.
2. Topic-policy tests prove trades cannot coalesce and lags on overflow; existing quotes and bar topics retain their policies.
3. A documented history/live example proves duplicate delivery is discarded while identical same-millisecond trades remain distinct.
4. New UTC fields, page/range bounds, volume units, occurrence ordering and immutable token metadata validate consistently across generators.
5. make check passes offline; existing examples and generated types remain compatible.

## Implementation boundary

This issue authorizes only its listed deliverable after written-plan approval and
`./work start Q-079 --agent <agent> --worktree`. Dependencies must be Done.
Preserve the existing execution controls and research/operations ownership boundaries.
No live-order activation, new backend-process ownership or unrelated refactoring.
Use generated contracts and commit/tag pins; never edit vendored code by hand.

## References

- [MT5 tick structure and update/aggressor flags](https://www.mql5.com/en/docs/constants/structures/mqltick).
- [MT5 range retrieval and UTC timestamps](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py).
- Existing topic policy: `schema/stream/topics.yaml`; compatibility rules: `VERSIONING.md`.
