# Event Stream Boundary

This directory holds schemas and policies governing the asynchronous event stream message bus.

## What Belongs Here

- The logical stream envelope schema (`envelope.schema.json`) defining common message metadata (`topic`, `schema_major`, `seq`, `epoch`, `producer_id`, `origin_ts`, `payload_kind`, `payload_schema`, `payload`, and optional `routing_key`).
- The topic policy configuration (`topics.yaml`) declaring topic classes (durable vs. ephemeral), retention rules, backpressure policies, and payload schemas. Emitted as typed data bindings.
- Control frame schemas under `control/` for streaming subscriptions (`subscribe`, `subscribed`, `subscription-rejected`), cursor expiration (`cursor-expired`), backpressure overflow notifications (`lagging`), and epoch invalidations (`epoch-changed`).
- Replay schemas under `replay/` for outbox sequence range replay (`history`), ephemeral latest state (`latest`), and transactional snapshot watermarks (`watermark`).
- Job stream payload schemas under `jobs/` for live progress updates (`progress`) and terminal outcomes (`terminal`).
- Transport framing schemas (`framing.schema.json`) defining binary wire headers for WebSocket streaming (opcode 0x02).

## What Does Not Belong Here

- Synchronous REST endpoints or OpenAPI definitions (belong in `schema/api/`).
- Edge gateway protocols or execution edge contracts (belong in `schema/edge/`).
- Dataset lake manifests or column catalog definitions (belong in `schema/catalog/`).
- Generated serializers, decoders, or SDK packages (belong in `generated/`).

## Populating Tasks

This boundary was populated by task **Q-002** (`Stream Envelope and Topic Policy`) and expanded with additive payload, replay, and framing contracts by task **Q-009** (`Stream Payload and Replay Contracts`).
