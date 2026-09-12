# Q-009: Stream payload and replay contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** [`q_contracts/docs/system-architecture.md` §4](https://github.com/GuilhermeFortuna/q_contracts/blob/d71ad64f11e7129549fa5ec8515875bdcec74cb0/docs/system-architecture.md#4-data-events-and-streaming)  
**Depends on:** Q-006  
**Implementation plan:** [`../plans/Q-009-stream-payload-and-replay-contracts-plan.md`](../plans/Q-009-stream-payload-and-replay-contracts-plan.md)

## Purpose

Q-002 fixed the envelope and the topic policy, but the stream still cannot be
built against them without inventing payloads by hand. The coalescing rules name
fields — `symbol`, `timeframe`, `job_id` — that exist in no schema, so a server
cannot coalesce without decoding every payload or making up a field. Both job
topics declare the envelope itself as their payload. A client that reconnects
has no way to offer a resume cursor, even though `cursor_expired` echoes one
back. The replay responses a client needs to close a gap have no shape. And
because topic policy is not generated, every consumer would copy retention and
backpressure values into its own code. This task closes those gaps additively,
so that the batch-02 backend and frontend tasks consume the stream protocol
rather than guess at it.

## Requirements

### Routing without decoding

- Every stream entry for a coalescing topic carries the values of that topic's
  coalesce key in a form a server can read without decoding the payload.
- The declared coalesce key of each topic and the routing values carried on its
  entries are checked to agree, so a topic cannot declare a key its entries do
  not carry.
- Entries for non-coalescing topics may carry routing values, but no consumer
  logic may depend on them being present.

### Job event payloads

- `jobs.progress` and `jobs.terminal` each have a payload schema of their own,
  and the topic policy points at it rather than at the envelope.
- A job event identifies the job by kind and identifier, so that two kinds of job
  that happen to share an identifier cannot be confused.
- Job status on the stream is drawn from one closed vocabulary. A terminal event
  is exactly one of completed, failed, or cancelled. The backend's current mix of
  status spellings is mapped into that vocabulary, not carried through.
- Progress is either a fraction between zero and one or explicitly absent. A job
  that has no numeric progress never reports a made-up fraction.
- A terminal event can carry an error message and never carries a result
  payload. Results stay behind their REST endpoints.

### Market data payloads

- Quote and bar entries declare which Arrow schema their payload conforms to, and
  the declared schema is the one the topic policy names.
- A bar entry identifies the bar's symbol and timeframe, and a quote entry its
  symbol, through routing values rather than through columns added to the Arrow
  schemas. The Arrow schemas describe lake data, and the lake data does not
  change.

### Subscription and resume

- A subscription request may carry a resume cursor per topic, so a client that
  reconnects can continue rather than re-snapshot every time.
- The server can reject a subscription, or one topic within it, with a reason
  drawn from a closed set that at least covers an unknown topic, an unsupported
  schema major, and the stream being unavailable.
- Every existing control frame keeps its fields, names, and required set.

### Replay responses

- A history page for a durable topic has a schema. It carries the entries in
  sequence order, the epoch they belong to, and whether more entries follow.
- A history request older than the retained window gets a distinct,
  schema-declared answer, so a client can tell "gone" from "empty".
- A latest-value response for an ephemeral topic has a schema carrying, for each
  routing key, the latest entry together with its sequence and epoch.
- A snapshot watermark has a schema: a map from topic to the last sequence the
  accompanying state reflects, together with that topic's epoch.

### Transport framing

- How an envelope travels over the WebSocket is specified, including a binary
  form for Arrow payloads that does not base64-encode them, because the logical
  envelope's base64 payload would inflate every quote by a third on the hottest
  path in the system.
- The framing is specified precisely enough for a TypeScript client and a Rust
  client to decode it with no other information.

### Policy is generated

- The topic policy — class, retention, backpressure, coalesce key, replay — is
  available to Python, TypeScript, and Rust consumers as generated data, so no
  consumer carries a hand-copied retention or backpressure value.
- Generated output stays deterministic and passes the existing drift check.

### Compatibility

- Every change is additive under `VERSIONING.md`. The envelope's schema major
  stays 1, and every entry that was valid before this task is still valid.
- The examples under `schema/stream/examples` are corrected to name payload
  schemas that match their topic, and new examples exist for every new schema.

## Constraints and non-goals

- **No change to the REST job status payloads.** Finding 5's inconsistent status
  responses are real. Fixing them means changing eight job managers' response
  models and every frontend consumer, which is a different task. This task maps
  the vocabulary at the stream boundary only.
- **No execution-topic payloads.** Decisions, orders, fills, risk, ledger, and
  deployments get payload schemas when their producers exist, in phase 4. A
  schema written before its producer is written against a guess.
- **No REST endpoint paths in OpenAPI.** The OpenAPI document is captured from
  `q_backend`, so the history and latest endpoints enter it by recapture after
  the backend task builds them. This task defines only the payload schemas those
  endpoints return.
- **No authentication for the stream.** It binds to loopback, like the API.
- **No compression or batching of frames.** Whether it is needed is a measurement
  for the endpoint task.
- **No consumer pin updates.** Each consumer advances `CONTRACTS_REV` in the task
  that first uses these schemas.

## Acceptance criteria

### Agent-verifiable

1. Every coalescing topic's entries carry the routing values named by its
   coalesce key, and validation fails when a topic declares a key that its
   entries' routing schema does not allow — verified by introducing such a
   mismatch, observing the failure, and reverting it.
2. `jobs.progress` and `jobs.terminal` name dedicated payload schemas, and no
   topic names the envelope as its payload schema.
3. The job terminal schema rejects any status other than completed, failed, or
   cancelled, and rejects a progress value outside zero to one.
4. The subscribe frame accepts an optional per-topic resume cursor, and a
   subscribe frame valid before this task still validates.
5. A rejection frame exists with a closed reason set covering unknown topic,
   unsupported schema major, and stream unavailable.
6. History page, history-expired, latest-value, and snapshot-watermark schemas
   exist, each with a validating example.
7. The WebSocket framing is documented, and an example binary frame is decoded by
   a test into an envelope equal to its logical JSON counterpart.
8. Topic policy is emitted as generated data for Python, TypeScript, and Rust,
   and the generated retention entry count for `quotes` equals `topics.yaml`'s.
9. Every example under `schema/stream/examples` that validated against the
   envelope before this task still does.
10. The full validation suite passes, including the generation drift check.

### Human-verifiable

1. The framing document is read by someone who has not seen this task, who
   confirms they could write a decoder from it alone.
   Command: `less schema/stream/README.md`
