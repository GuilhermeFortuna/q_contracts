# Event Stream Boundary

This directory holds schemas and policies governing the asynchronous event stream message bus.

## What Belongs Here

- The logical stream envelope schema (`envelope.schema.json`) defining common message metadata (topic, seq, epoch, origin_ts, payload_kind, and optional routing `key`).
- The topic policy configuration (`topics.yaml`) declaring topic classes, retention rules, coalesce keys, and backpressure policies.
- Dedicated event payload schemas under `payloads/` (`job-progress.schema.json`, `job-terminal.schema.json`).
- Replay and snapshot response schemas under `replay/` (`history-page.schema.json`, `history-expired.schema.json`, `latest.schema.json`, `watermark.schema.json`).
- Control payload schemas under `control/` for streaming subscriptions (`subscribe.schema.json` with resume cursors), rejections (`rejected.schema.json`), cursor events, and stream synchronization.
- Transport framing specification (`framing.md`) defining WebSocket text and binary frame formats for raw Arrow IPC delivery.

## What Does Not Belong Here

- Synchronous REST endpoints or captured OpenAPI schemas (belong in `schema/api/`).
- Edge gateway protocols or execution edge contracts (belong in `schema/edge/`).
- Dataset lake manifests or column catalog definitions (belong in `schema/catalog/`).
- Generated serializers, decoders, or SDK packages (belong in `generated/`).

## Populating Tasks

- **Q-002** (`Stream Envelope and Topic Policy`): Envelope schema, baseline topic policy, and initial control frames.
- **Q-009** (`Stream Payload and Replay Contracts`): Routing keys, dedicated job payloads, rejection and resume frames, replay/snapshot schemas, framing specification, and generated topic policy.
