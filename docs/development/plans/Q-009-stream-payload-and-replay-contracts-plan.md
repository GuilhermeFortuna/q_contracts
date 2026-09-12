# Q-009 implementation plan: Stream payload and replay contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-009-stream-payload-and-replay-contracts-spec.md`](../specs/Q-009-stream-payload-and-replay-contracts-spec.md)  
**Depends on:** Q-006

## Current-system context

`schema/stream/` holds `envelope.schema.json` (nine required fields,
`additionalProperties: false`, `schema_major` ≥ 1), `topics.yaml` declaring eleven
topics, and five control frames under `control/`. `tools/validate.py`'s
`check_stream_consistency` enforces the topic-enum agreement, the
durable-implies-no-coalesce and ephemeral-implies-retention-only rules, that
`payload_schema` resolves, and that `coalesce_key` is present iff `coalesce` is true.
It does not check what the coalesce key names. `quotes` declares
`coalesce_key: [symbol]` and `bars.forming` declares `[symbol, timeframe]`, but
`schema/api/arrow/ticks.schema.json` and `bars.schema.json` have no such columns and
the envelope has no field that could hold them. `jobs.progress` and `jobs.terminal`
both declare `payload_schema: schema/stream/envelope.schema.json`, so a job event
is currently specified as an envelope inside an envelope. `examples/envelope-arrow.json`
names the envelope as its payload schema, and `examples/envelope-control.json`
puts a `subscribed` frame on the `orders` topic, so neither example matches its
own topic.

`tools/generate.py`'s `plan_units` deliberately skips policy YAML ("they describe
retention, lifecycle, and endpoint obligations rather than payload shapes").
`schema/api/examples/jobs/` already holds six job lifecycle examples checked by
`tests/test_job_lifecycle_examples.py` against the captured OpenAPI. They show
what the REST job payloads look like today and are the source for the stream
vocabulary mapping. `schema/api/FINDINGS.md` Finding 4 names the missing
history and latest endpoints, and Finding 5 names the inconsistent job statuses.
Neither consumer imports the vendored `contracts/stream.py` yet. The gap this
task closes: payloads, routing, resume, replay shapes, framing, and policy data
that the backend and frontend stream tasks need before they can be built without
hand-written type mirrors.

## Interfaces produced

```
// schema/stream/  (additions and edits)
envelope.schema.json                     + optional "key": object of string values (routing)
topics.yaml                              jobs.* payload_schema → payloads/job-*.schema.json; jobs.progress coalesce_key [job_id] → [kind, job_id]
payloads/job-progress.schema.json        {kind, job_id, status, progress|null, message?}
payloads/job-terminal.schema.json        {kind, job_id, status: completed|failed|cancelled, error?, finished_at}
control/subscribe.schema.json            + optional "cursors": {topic → cursor}
control/rejected.schema.json             {reason: unknown_topic|unsupported_schema_major|stream_unavailable, topic?, detail?}
replay/history-page.schema.json          {topic, epoch, entries: [envelope], next_seq|null}
replay/history-expired.schema.json       {topic, requested_from_seq, oldest_available_seq|null}
replay/latest.schema.json                {topic, entries: {routing-key-string → envelope}}
replay/watermark.schema.json             {topic → {epoch, seq}}
framing.md                               WebSocket framing: text = JSON envelope/control; binary = header + IPC
examples/                                one example per new schema; existing two corrected
README.md                                links framing.md; lists payloads/ and replay/
```

```
// binary WebSocket frame layout (framing.md)
offset 0   u32 little-endian   header_len
offset 4   header_len bytes    UTF-8 JSON: envelope with "payload" omitted
offset 4+header_len            Arrow IPC stream bytes (the payload), to end of frame
```

```python
# tools/generate.py
def plan_policy_units(schema_root: Path) -> list[GenerationUnit]: ...
    # emits generated/{python/q_contracts/topics.py, typescript/topics.ts, rust/topics.rs}

# tools/validate.py
def check_stream_routing(schema_root: Path) -> list[SchemaProblem]: ...
    # every coalesce_key field is an allowed property of the envelope "key" object
    # every topic's payload_schema is not the envelope
```

```python
# generated/python/q_contracts/topics.py  (shape; generated)
@dataclass(frozen=True)
class TopicPolicy:
    name: str
    topic_class: Literal["durable", "ephemeral"]
    retention_duration: str          # ISO-8601 duration, as declared
    retention_entries: int
    coalesce_key: tuple[str, ...]    # empty when coalesce is false
    on_overflow: Literal["lag", "coalesce"]
    replay: Literal["unbounded", "retention_only"]
    payload_schema: str

TOPICS: Mapping[str, TopicPolicy]
```

## Implementation decisions

- **Routing values live in an optional envelope `key` object, not in the Arrow
  schemas and not in the payload.** Adding `symbol` to `ticks.schema.json` would
  change the schema that describes lake Parquet files, which the catalog and
  `q_core` readers depend on. Putting routing inside the payload would force the
  server to decode Arrow IPC for every quote just to coalesce it, which is the
  per-entry cost the stream exists to avoid. An optional envelope property is
  additive under `VERSIONING.md` §Additive by Default.

- **`key` values are strings, including timeframe.** The server compares keys for
  equality and never orders them. Allowing numbers would make `"M1"` against `1`
  a representable disagreement between producers, so it is ruled out.

- **Job events identify a job by `(kind, job_id)`, with `kind` a closed enum of
  the nine progress namespaces in use today.** The backend's
  `PROGRESS_NAMESPACE` values are `backtest`, `neural_training`,
  `storage_ingest`, `alpha_research`, `encoder_ablation`, `discovery_ab`,
  `strategy_search`, and `walkforward`, and the optimization manager uses the
  default `job`. Run ids and study ids come from different generators, and
  nothing guarantees they are disjoint. The enum spells the optimization kind
  `optimization`, and the backend maps it at the boundary, because `job` names
  nothing. For the same reason, `jobs.progress`'s `coalesce_key` changes from
  `[job_id]` to `[kind, job_id]`. Coalescing on `job_id` alone would let one
  kind's progress replace another's whenever their ids collide. No consumer reads
  the value yet, so changing it breaks nothing.

- **The terminal status enum is `completed | failed | cancelled`, and the
  progress status enum is `queued | running`.** The REST payloads use both
  `error` and `failed` for the same outcome (`discovery_ab_jobs.py` and
  `storage_jobs.py` both write `"error"`). Two spellings on the stream would
  force every client to carry the mapping, so the backend maps once at the
  boundary. Splitting the two enums means a progress event can never claim to be
  terminal, so "the last progress event says completed" cannot be mistaken for
  the durable terminal event.

- **`progress` is `number | null` with `minimum: 0, maximum: 1`.** Neural and
  encoder-ablation jobs report free text such as "Epoch 3/10". Coercing that to
  a fraction would put invented precision on a progress bar, so those jobs send
  `null` together with a `message`.

- **Subscribe gains optional `cursors` keyed by topic, rather than a new
  `resume` frame.** Resume is a subscribe with a starting point. A second frame
  type would duplicate the topic list and create a state where a client sends
  both. Topics without a cursor start live, which is today's behavior.

- **Rejection is a new control frame with a closed `reason` enum, not an HTTP
  status or a WebSocket close code.** Close codes carry no topic, and a
  subscription can be partly valid: one unknown topic must not tear down the
  others. The HTTP 503 at handshake stays the answer for "Redis is down before
  you connected". `stream_unavailable` is for losing Redis mid-connection.

- **History pages carry `next_seq`, not an offset or a page token.** `seq` is
  already the ordering watermark, and a client resumes from the last `seq` it
  applied. A separate cursor would be a second position to keep consistent with
  the first.

- **"Expired" is a distinct schema, not an empty page.** An empty page means
  "nothing after this `seq`", which a lagging client treats as caught up. If the
  rows were pruned, that conclusion silently loses events. The two answers must
  not share a shape.

- **Binary frames use a little-endian `u32` header length, a JSON header, and
  raw IPC bytes.** JSON keeps the header readable in browser devtools. The
  length prefix lets a decoder find the IPC bytes without scanning. Browsers and
  `arrow-rs` both decode an IPC stream from a byte slice without copying.
  Base64 in a text frame was rejected because of its 33% inflation and a second
  decode per quote.

- **Policy YAML is generated as data, reversing `plan_units`' exclusion for
  `topics.yaml` only.** That exclusion assumed policy was for humans. The relay
  needs `retention.entries` for `MAXLEN`, the endpoint needs `coalesce_key` and
  `on_overflow`, and the frontend needs the topic class, so three consumers would
  otherwise each hand-copy the values. That violates architecture invariant 2,
  and the copies would drift. `catalog/lifecycle.yaml` and the edge YAMLs stay
  excluded, because nothing consumes them as data yet.

- **`check_stream_routing` is a new function rather than new branches in
  `check_stream_consistency`.** That function already enforces six rules and is
  covered rule by rule in `tests/test_stream_consistency.py`. A separate
  function gets its own test module, and a new failure names a new rule instead
  of becoming a seventh case in an existing one.

## Ordered implementation

1. Create the branch `Q-009-stream-payload-and-replay-contracts-spec` in
   `q_contracts`.
2. Write failing tests in `tests/test_stream_routing.py`: a `topics.yaml` fixture
   where `quotes` declares `coalesce_key: [symbol]` but the envelope `key` allows
   only `timeframe` yields exactly one problem naming `quotes`; a fixture where
   `jobs.progress` names the envelope as its payload schema yields one problem
   naming `jobs.progress`; the real tree yields none. Confirm they fail.
   Implement `check_stream_routing`, wire it into `check_tree`, add `key` to the
   envelope, and point both job topics at placeholder payload files. Confirm the
   tests pass. Commit.
3. Write failing tests in `tests/test_job_event_payloads.py`: a terminal payload
   with `status: "error"` is rejected; `progress: 1.5` is rejected;
   `progress: null` with a `message` is accepted; `kind: "job"` is rejected and
   `kind: "optimization"` is accepted; a progress payload with
   `status: "completed"` is rejected. Confirm they fail. Write both payload
   schemas and their examples. Confirm they pass. Commit.
4. Write failing tests in `tests/test_control_schemas.py` (extend): the pre-task
   subscribe example still validates; a subscribe with
   `cursors: {"quotes": "1710000000000-0"}` validates; a rejected frame with
   `reason: "unknown_topic", topic: "nope"` validates; `reason: "other"` is
   rejected. Confirm they fail. Edit subscribe and add `rejected.schema.json`.
   Confirm they pass. Commit.
5. Write failing tests in `tests/test_replay_schemas.py`: a history page with two
   envelopes and `next_seq: null` validates; a history page whose entries lack
   `seq` is rejected; history-expired requires `requested_from_seq`; a latest
   response keyed `"WINZ25"` validates; a watermark `{"jobs.terminal": {"epoch":
   "e1", "seq": 42}}` validates. Confirm they fail. Write the four schemas and
   examples. Confirm they pass. Commit.
6. Write `schema/stream/framing.md`. Write a failing test in
   `tests/test_stream_framing.py` that builds a binary frame from
   `examples/frame-quotes.bin` (header length 4 bytes LE, JSON header, IPC bytes
   produced with `pyarrow` from a two-row ticks batch), decodes it, and asserts
   that the header plus base64 of the tail equals `examples/envelope-quotes.json`
   field for field. Confirm it fails. Add the example files and a decode helper
   under `tests/fixtures`. Confirm it passes. Commit.
7. Correct `examples/envelope-arrow.json` (topic `bars.completed`, payload schema
   `schema/api/arrow/bars.schema.json`, `key` with `symbol` and `timeframe`) and
   `examples/envelope-control.json` (a `jobs.terminal` entry carrying a
   job-terminal payload). Confirm that `tests/test_stream_envelope.py` still
   passes. Commit.
8. Write failing tests in `tests/test_generate.py` (extend): generation emits
   `topics.py`, `topics.ts`, and `topics.rs`; the Python module's
   `TOPICS["quotes"].retention_entries` equals `100000`; `TOPICS["bars.forming"].coalesce_key`
   equals `("symbol", "timeframe")`; `TOPICS["jobs.progress"].coalesce_key` equals
   `("kind", "job_id")`; generating twice produces byte-identical
   output. Confirm they fail. Implement `plan_policy_units`. Regenerate
   `generated/`. Confirm they pass. Commit.
9. Verify acceptance criterion 1 negatively: change `quotes`' coalesce key to
   `[venue]`, run `uv run python tools/validate.py`, confirm a non-zero exit
   naming `quotes`, and revert. Do not commit the change.
10. Update `schema/stream/README.md` to list `payloads/`, `replay/`, and
    `framing.md`. Add a Finding 4 note to `schema/api/FINDINGS.md` saying that
    the payload shapes are now defined and the endpoints remain a backend task.
    Commit.
11. Human step, matching human-verifiable criterion 1: a reader who has not seen
    this task reads `framing.md` and confirms it is sufficient to write a decoder.
12. Run `make check`. Record the resulting commit hash for the consumer tasks.
    Commit.

## Validation

- **Unit:** routing agreement, job payload enums and bounds, subscribe
  compatibility, rejection reasons, the four replay schemas, frame decode
  round-trip, and generated policy values.
- **Regression:** every pre-existing example still validates. `make
  generate-check` shows no drift after regeneration. The existing
  `test_stream_consistency.py` cases pass unchanged.
- **Manual:** step 11.

```bash
cd /home/gui/projects/q/q_contracts
UV_CACHE_DIR=/tmp/q-uv-cache make check
uv run pytest tests/test_stream_routing.py tests/test_job_event_payloads.py \
  tests/test_replay_schemas.py tests/test_stream_framing.py -v

# criterion 1, the deliberate mismatch
sed -i '0,/- symbol/s//- venue/' schema/stream/topics.yaml
uv run python tools/validate.py; echo "expected non-zero, got $?"
git checkout -- schema/stream/topics.yaml
```

## Handoff

Report the final `q_contracts` commit hash, which Q-010 and Q-016 pin. List every
schema added or edited, and confirm that no required set of an existing schema
grew. Report the exact problem text `validate.py` printed for the deliberate
coalesce-key mismatch. Report the byte size of the example binary quote frame
next to the base64 text form of the same envelope, so the framing choice is
justified by a number. Report the status mapping table the backend must apply
(every status literal found in `q_backend/src/q_backend/api/*_jobs.py` → stream
status), so Q-012 inherits it rather than re-deriving it.
