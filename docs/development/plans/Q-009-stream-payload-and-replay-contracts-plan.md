# Q-009 implementation plan: Stream payload and replay contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-009-stream-payload-and-replay-contracts-spec.md`](../specs/Q-009-stream-payload-and-replay-contracts-spec.md)  
**Depends on:** Q-006

## Current-system context

Prior to this task, `q_contracts/schema/stream/` contained:
- `envelope.schema.json`: the logical event stream envelope.
- `topics.yaml`: topic declarations and invariants, which was validated but omitted from code generation.
- `control/`: five control frame schemas (`subscribe`, `subscribed`, `cursor-expired`, `lagging`, `epoch-changed`).
- `examples/`: envelope examples.

Code generation in `tools/generate.py` and `tools/emitters/` generated:
- `generated/python/q_contracts/stream.py`
- `generated/typescript/stream.ts`
- `generated/rust/stream.rs`

Key gaps existed:
1. Envelope had no `routing_key` property for topic dispatch or coalesce keying.
2. `jobs.progress` and `jobs.terminal` in `topics.yaml` had placeholder `payload_schema` pointing back to `envelope.schema.json`.
3. `SubscribeFrame` had no resume `cursors` field, and no rejection frame existed.
4. No schemas existed for replay protocols: outbox `history`, ephemeral `latest`, and transactional snapshot `watermark`.
5. No framing schema existed for WebSocket binary transport (avoiding base64 overhead).
6. Topic policy from `topics.yaml` was not generated as typed data for consumers.

## Interfaces produced

```
// Schema tree additions and updates
schema/stream/envelope.schema.json              (updated with routing_key)
schema/stream/topics.yaml                       (updated job payload_schema references)
schema/stream/control/subscribe.schema.json     (updated with cursors)
schema/stream/control/subscription-rejected.schema.json
schema/stream/jobs/progress.schema.json
schema/stream/jobs/terminal.schema.json
schema/stream/replay/history.schema.json
schema/stream/replay/latest.schema.json
schema/stream/replay/watermark.schema.json
schema/stream/framing.schema.json

schema/stream/examples/
├── envelope-routing-key.json
├── job-progress.json
├── job-terminal.json
├── subscribe-with-cursors.json
├── subscription-rejected.json
├── replay-history.json
├── replay-latest.json
├── replay-watermark.json
└── websocket-binary-header.json
```

```
// Generated code additions in python, typescript, rust
TopicPolicy, TopicRetention, TopicBackpressure
TOPIC_POLICIES, TOPIC_NAMES
JobProgressPayload, JobTerminalPayload
SubscriptionRejectedFrame
HistoryResponse, LatestResponse, WatermarkResponse
WebSocketBinaryHeader
```

## Implementation decisions

- **Additive envelope modification:** `routing_key` is optional, keeping all existing envelopes valid.
- **Hierarchical schema organization:**
  - `schema/stream/jobs/` for job payloads (`stream/jobs/*` IDs).
  - `schema/stream/replay/` for replay payloads (`stream/replay/*` IDs).
  - `schema/stream/control/` for control frames (`stream/control/*` IDs).
- **Consistent `$id` convention:** Every schema specifies an `$id` matching `tools/validate.py`'s expected path rule: `stream/<subpath>/<filename-without-ext>`.
- **Generated topic policy representation:**
  - Topic policy data from `topics.yaml` is parsed during generation and emitted as deterministic, type-safe data structures in Python, TypeScript, and Rust.
  - Rust provides `pub fn get_topic_policy(topic: &str) -> Option<TopicPolicy>` with a zero-allocation `match` statement, plus `TOPIC_NAMES`.
  - Python provides typed dataclasses and a `TOPIC_POLICIES` dictionary mapping topic name to `TopicPolicy`.
  - TypeScript provides typed interfaces and `TOPIC_POLICIES: Record<string, TopicPolicy>`.
- **Deterministic output:** All collections and fields are sorted prior to code emission so that regenerating produces byte-identical output across runs.

## Detailed phase-by-phase work

1. **Phase 1: Stream schemas and examples:**
   - Add `routing_key` to `schema/stream/envelope.schema.json`.
   - Create `schema/stream/jobs/progress.schema.json` and `schema/stream/jobs/terminal.schema.json`.
   - Update `schema/stream/topics.yaml` `payload_schema` paths for `jobs.terminal` and `jobs.progress`.
   - Add optional `cursors` to `schema/stream/control/subscribe.schema.json`.
   - Create `schema/stream/control/subscription-rejected.schema.json`.
   - Create `schema/stream/replay/history.schema.json`, `schema/stream/replay/latest.schema.json`, and `schema/stream/replay/watermark.schema.json`.
   - Create `schema/stream/framing.schema.json`.
   - Create representative JSON examples under `schema/stream/examples/`.
   - Update `schema/stream/README.md`.

2. **Phase 2: Code generator and emitters:**
   - Update `tools/generate.py` `plan_units` to include `schema/stream/topics.yaml` in the stream generation unit.
   - Update `tools/emitters/python.py`, `tools/emitters/typescript.py`, and `tools/emitters/rust.py` to emit topic policy types and data.
   - Run `python tools/generate.py` to produce updated generated files in `generated/`.

3. **Phase 3: Test suite & validation:**
   - Add unit and mutant tests for all new schemas in `tests/test_stream_jobs.py`, `tests/test_stream_control.py`, `tests/test_stream_replay.py`, and `tests/test_stream_framing.py`.
   - Update `tests/test_generate.py` to assert correct emission of topic policy data, routing keys, and replay types.
   - Verify `make check` passes cleanly (generation check, black, ruff, validate.py, and pytest).

4. **Phase 4: Bookkeeping:**
   - Update `COMPAT.md` with verification status.
