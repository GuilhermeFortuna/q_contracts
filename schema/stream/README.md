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
