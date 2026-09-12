# Q-009: Stream payload and replay contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q_contracts/docs/system-architecture.md`  
**Depends on:** Q-006  
**Implementation plan:** [`../plans/Q-009-stream-payload-and-replay-contracts-plan.md`](../plans/Q-009-stream-payload-and-replay-contracts-plan.md)

## Purpose

Task Q-002 established the fundamental event stream envelope and the authoritative topic policy in `topics.yaml`, and task Q-006 established deterministic multi-language contract code generation and consumer vendoring. However, several critical stream capabilities outlined in the target system architecture (`docs/system-architecture.md` §4) remain unspecified in machine-readable contracts:

1. **Routing and coalescing keys:** The envelope lacked an explicit routing/coalesce key field for topic dispatch, client filtering, and backpressure coalescing.
2. **Job payloads:** Stream topics `jobs.progress` and `jobs.terminal` temporarily referenced the envelope schema itself rather than typed payload shapes for live job progress and terminal outcomes.
3. **Resume cursors and rejection control frames:** The `SubscribeFrame` lacked a structured mechanism for clients to provide resume cursors upon reconnecting, and no frame existed to reject unfulfillable or invalid subscriptions.
4. **Replay contracts:** The snapshot-then-delta protocol (§4.2) requires REST history replay by sequence watermark, ephemeral `latest` value synchronization, and transactional `watermark` queries to reconcile state without races. These replay payloads had no schemas.
5. **WebSocket binary framing:** Logical Arrow IPC payloads inside envelopes incur a 33% expansion penalty when base64-encoded into JSON text frames. High-throughput streaming requires a binary framing standard that prepends envelope metadata to raw binary Arrow IPC batches.
6. **Topic policy as generated data:** In Q-006, policy YAML documents were intentionally omitted from code generation. Consumers in Python, TypeScript, and Rust had no programmatic access to declared topic classes, retention limits, and backpressure policies without duplicating them or manually parsing YAML at runtime.

This task delivers additive, backward-compatible schemas and contracts for all of these capabilities, integrates `topics.yaml` into multi-language code generation as typed data, and verifies everything with extensive schema and mutant test suites.

## Requirements

### Envelope routing key

- The logical stream envelope schema (`schema/stream/envelope.schema.json`) adds an optional `routing_key` string property.
- `routing_key` represents the partitioning, dispatch, or coalesce key of the event (e.g. `symbol`, `symbol:timeframe`, or `job_id`).
- The property is optional (`required` remains unchanged), ensuring strict backward compatibility for existing envelope producers and consumers.

### Job progress and terminal payloads

- A typed JSON schema for ephemeral job progress updates exists at `schema/stream/jobs/progress.schema.json` with title `JobProgressPayload` and ID `stream/jobs/progress`.
  - Requires `job_id`, `status`, and `progress`.
  - Enforces `progress` as a number between 0.0 and 1.0.
  - Accepts optional `detail`, `error`, and `timestamp` fields.
- A typed JSON schema for durable terminal job states exists at `schema/stream/jobs/terminal.schema.json` with title `JobTerminalPayload` and ID `stream/jobs/terminal`.
  - Requires `job_id` and `status`.
  - Enforces `status` in `["completed", "failed", "cancelled"]`.
  - Accepts optional `error`, `result`, and `completed_at` fields.
- `schema/stream/topics.yaml` updates `payload_schema` for `jobs.progress` and `jobs.terminal` to point to these new schemas, replacing the temporary self-referential envelope placeholder.

### Subscribe resume cursors and rejection frame

- `schema/stream/control/subscribe.schema.json` adds an optional `cursors` property mapping topic names to transport replay cursor strings (e.g. Redis stream IDs), allowing reconnecting clients to resume from known positions.
- A new server rejection control frame exists at `schema/stream/control/subscription-rejected.schema.json` with title `SubscriptionRejectedFrame` and ID `stream/control/subscription-rejected`.
  - Requires `topics` (non-empty array of topic names) and `reason` (human-readable string).
  - Accepts optional `code` (machine-readable rejection identifier).

### Replay contracts: history, latest, and watermark

- A schema for outbox sequence range replay exists at `schema/stream/replay/history.schema.json` with title `HistoryResponse` and ID `stream/replay/history`.
  - Requires `topic`, `epoch`, `from_seq`, `to_seq`, and `entries`.
  - `entries` is an array of stream envelopes typed against `schema/stream/envelope.schema.json`.
- A schema for ephemeral latest-state queries exists at `schema/stream/replay/latest.schema.json` with title `LatestResponse` and ID `stream/replay/latest`.
  - Requires `topic`, `epoch`, `seq`, and `payload`.
  - Accepts optional `origin_ts`, `routing_key`, and `producer_id`.
- A schema for snapshot watermark reconciliation exists at `schema/stream/replay/watermark.schema.json` with title `WatermarkResponse` and ID `stream/replay/watermark`.
  - Requires `watermarks` (map of durable topic names to non-negative integer sequence watermarks).
  - Accepts optional `epoch`.

### WebSocket binary framing

- A schema for WebSocket binary framing headers exists at `schema/stream/framing.schema.json` with title `WebSocketBinaryHeader` and ID `stream/framing`.
- Documents the binary wire framing protocol:
  - 4 bytes unsigned integer (`uint32_be`): length of header JSON in bytes.
  - `header_length` bytes: UTF-8 JSON object matching `WebSocketBinaryHeader`.
  - Remaining bytes: raw binary payload (e.g. unencoded Arrow IPC stream batch).
- Carries all envelope metadata fields (`topic`, `schema_major`, `seq`, `epoch`, `producer_id`, `origin_ts`, `payload_kind`, `payload_schema`, and optional `routing_key`) plus `payload_length` (integer >= 0).

### Topic policy generated as data

- `tools/generate.py` includes `schema/stream/topics.yaml` as an input generation source for the `stream` generation unit.
- Topic policies are emitted as typed data in all three consumer languages:
  - **Python:** `TopicRetention`, `TopicBackpressure`, and `TopicPolicy` dataclasses, a `TOPIC_POLICIES` dictionary mapping topic name to `TopicPolicy`, and a `TOPIC_NAMES` tuple.
  - **TypeScript:** `TopicRetention`, `TopicBackpressure`, and `TopicPolicy` interfaces, a `TOPIC_POLICIES` constant record, and a `TOPIC_NAMES` array.
  - **Rust:** `TopicRetention`, `TopicBackpressure`, and `TopicPolicy` structs, `pub const TOPIC_NAMES: &[&str]`, `pub fn get_topic_policy(topic: &str) -> Option<TopicPolicy>`, and `pub fn all_topic_policies() -> Vec<(&'static str, TopicPolicy)>`.

## Constraints and non-goals

- **Additive and backward-compatible:** Existing valid JSON envelopes and control frames must continue to validate without error.
- **No streaming server implementation:** Transport handlers, Redis `XREAD`/`XADD`, outbox relays, and WebSocket servers belong in `q_backend`. This task defines the wire schemas, framing rules, and generated types.
- **No changes to existing required envelope fields:** Fields required in Q-002 (`topic`, `schema_major`, `seq`, `epoch`, `producer_id`, `origin_ts`, `payload_kind`, `payload_schema`, `payload`) remain required.

## Acceptance criteria

### Agent-verifiable

1. `envelope.schema.json` validates envelopes with and without `routing_key`.
2. Missing `routing_key` does not invalidate existing envelope examples.
3. `schema/stream/jobs/progress.schema.json` and `schema/stream/jobs/terminal.schema.json` validate representative job examples and fail mutant examples missing required fields.
4. `topics.yaml` points `jobs.progress` and `jobs.terminal` to their respective payload schemas, and `check_stream_consistency` passes cleanly.
5. `subscribe.schema.json` validates subscription requests with and without `cursors`.
6. `subscription-rejected.schema.json` validates rejection examples and fails when `topics` or `reason` is missing.
7. `history.schema.json`, `latest.schema.json`, and `watermark.schema.json` validate their respective example responses and fail invalid/mutant payloads.
8. `framing.schema.json` validates binary framing headers.
9. `tools/generate.py` deterministically emits typed topic policy data in Python, TypeScript, and Rust, and `make check` passes without drift.
10. The complete test suite (`make check`) passes 100%.

### Human-verifiable

1. Review `schema/stream/README.md` to confirm the documented framing and replay flows accurately mirror `docs/system-architecture.md` §4.
2. Confirm the emitted `TOPIC_POLICIES` in Python, TypeScript, and Rust provides immediate compile-time access to topic class and retention settings.
