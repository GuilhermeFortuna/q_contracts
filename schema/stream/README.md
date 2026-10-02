# Event Stream Boundary

This directory holds schemas and policies governing the asynchronous event stream message bus.

## What Belongs Here

- The logical stream envelope schema (`envelope.schema.json`) defining common message metadata (topic, seq, epoch, origin_ts, payload_kind, and optional routing `key`).
- The topic policy configuration (`topics.yaml`) declaring topic classes, retention rules, coalesce keys, and backpressure policies.
- Dedicated event payload schemas under `payloads/`:
  - Job execution payloads (`job-progress.schema.json`, `job-terminal.schema.json`).
  - Durable execution topics (`execution-decision.schema.json`, `execution-order.schema.json`, `execution-fill.schema.json`, `execution-risk.schema.json`, `execution-ledger.schema.json`, `execution-deployment.schema.json`) with shared primitives and vocabularies in `execution-common.schema.json`.
- Replay and snapshot response schemas under `replay/`:
  - Stream history and generic latest (`history-page.schema.json`, `history-expired.schema.json`, `latest.schema.json`, `watermark.schema.json`).
- Full execution state snapshot (`execution-snapshot.schema.json`) with 6-topic watermark, limits, and entity collections matching event payload shapes.

Deployment events carry an `archived` marker. Archived deployments remain in durable execution records for audit, but active deployment lists and snapshots omit them.
- Control payload schemas under `control/` for streaming subscriptions (`subscribe.schema.json` with resume cursors), rejections (`rejected.schema.json`), cursor events, and stream synchronization. Every server control frame carries a `type` discriminator; envelopes never do (see `framing.md` §2.1).
- Transport framing specification (`framing.md`) defining WebSocket text and binary frame formats for raw Arrow IPC delivery.

## What Does Not Belong Here

- Synchronous REST endpoints or captured OpenAPI schemas (belong in `schema/api/`).
- Edge gateway protocols or execution edge contracts (belong in `schema/edge/`).
- Dataset lake manifests or column catalog definitions (belong in `schema/catalog/`).
- Generated serializers, decoders, or SDK packages (belong in `generated/`).

## Populating Tasks

- **Q-002** (`Stream Envelope and Topic Policy`): Envelope schema, baseline topic policy, and initial control frames.
- **Q-009** (`Stream Payload and Replay Contracts`): Routing keys, dedicated job payloads, rejection and resume frames, replay/snapshot schemas, framing specification, and generated topic policy.
- **Q-039** (`Execution event payloads and command idempotency`): Six durable execution event payload schemas, execution snapshot schema with watermark and limits, and execution topic policy wiring.

## Trade tape and session history (Q-079)

`trades` is an ephemeral, non-coalescing tape with retention-only replay. Each
delivery is capped at 4096 source records and carries provider, symbol,
source-generation, exchange-timezone, session-key, and stable volume-unit
context as declared by `payloads/trade-delivery-context.schema.json`. The Arrow
delivery contains raw `volume` and optional `volume_real`; `volume_field` binds
the selected analysis value and `volume_unit` to the source generation. Its
rows use UTC `timestamp[ms]` and identify a row with
`(provider_id, symbol, source_generation, time_msc, occurrence)`. Occurrence is
assigned in source order among eligible trades within each complete millisecond
group; equal row values remain distinct. The gateway includes LAST, VOLUME, BUY,
or SELL update-flag records only when price and selected volume are finite and
positive. Quote-only updates are excluded even when last and volume are carried
forward. Invalid trade rows count against range coverage. Aggressor side is
left for `q_core` to derive; both or neither aggressor flags mean unknown side.

`trades.status` is a separately sequenced, latest-per-symbol status topic. Range
coverage (`complete`, `partial`, `unavailable`) is separate from aggressor
classification coverage and includes covered bounds and a reason. `complete`
means the provider served the requested range without truncation, invalid
records, or a detected source/transport gap; it does not claim the exchange
feed had no omissions. Status never recovers tape data.

GET `/api/v1/market/trades/snapshot?symbol=` returns an immutable ten-minute
token with session bounds, source context, counts, coverage, and a frozen
`(epoch, seq)` watermark from the publisher coordinator. The open millisecond
group is excluded until it closes. Subscribe and buffer live deliveries before
loading the pages from `/api/v1/market/trades/history`; discard buffered entries
at or below the frozen watermark and apply later sequences once. If replay
expires or the epoch changes, fetch a new snapshot. A changed source generation
invalidates prior tokens and requires a new session snapshot. See
`examples/trade-history-recovery.md` for an identical-row example.

In a snapshot descriptor, the top-level provider, symbol, source generation,
volume field, and volume unit must match the embedded source coverage status.
The schema validator checks those relationships in committed snapshot examples;
consumers reject descriptors whose duplicated context disagrees.
