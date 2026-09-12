# Event Stream Boundary

This directory holds schemas and policies governing the asynchronous event stream message bus.

## What Belongs Here

- The logical stream envelope schema (`envelope.schema.json`) defining common message metadata (topic, seq, epoch, origin_ts, payload_kind).
- The topic policy configuration (`topics.yaml`) declaring topic classes, retention rules, and backpressure policies.
- Control payload schemas for streaming subscriptions, cursor events, and stream synchronization.

## What Does Not Belong Here

- Synchronous REST endpoints or job payloads (belong in `schema/api/`).
- Edge gateway protocols or execution edge contracts (belong in `schema/edge/`).
- Dataset lake manifests or column catalog definitions (belong in `schema/catalog/`).
- Generated serializers, decoders, or SDK packages (belong in `generated/`).

## Populating Task

This boundary is populated by task **Q-002** (`Stream Envelope and Topic Policy`).
