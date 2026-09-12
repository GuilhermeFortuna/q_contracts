# Q-002 implementation plan: Stream envelope and topic policy

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-002-stream-envelope-and-topic-policy-spec.md`](../specs/Q-002-stream-envelope-and-topic-policy-spec.md)  
**Depends on:** Q-001

## Current-system context

After Q-001, `q_contracts` holds `schema/stream/` with a README and nothing else,
`tools/validate.py` with `discover`, `check_file`, `check_tree` and `main`, and
`SUPPORTED_DIALECTS` accepting JSON Schema 2020-12 only. `make check` runs
`black`, `ruff`, `validate.py` and `pytest`.

There is no streaming in the running system. `q_backend` publishes job progress
into Redis as opaque values through
`src/q_backend/storage/redis/progress.py` (`set_job_progress`, `get_job_progress`,
`delete_job_progress`), consumed in `src/q_backend/api/backtest_jobs.py` via
`_persist_progress(run_id, status, error)` at line 83, which writes the bare
status strings `"running"`, `"completed"` and `"failed"` under a
`PROGRESS_NAMESPACE`. That is the closest thing to an event today and it has no
sequence, no epoch, and no ordering guarantee — a client that reads it twice can
observe the values out of order and has no way to tell. `q_frontend` compensates
by polling on React Query timers. The gap this task closes is that there is no
written definition of what a stream entry is, so the outbox relay, the WebSocket
endpoint, and every client gap-detection path in later batches have nothing to
code against.

## Interfaces produced

```
// q_contracts/schema/stream/
envelope.schema.json          the logical stream entry
topics.yaml                   the topic policy, one entry per topic
control/subscribe.schema.json
control/subscribed.schema.json
control/cursor-expired.schema.json
control/lagging.schema.json
control/epoch-changed.schema.json
examples/                     fixtures the validity tests load; not a contract
```

```jsonc
// schema/stream/envelope.schema.json  — field meanings, types elided to their JSON types
{
  "topic":         "string, must be a declared topic in topics.yaml",
  "schema_major":  "integer >= 1; a consumer that does not implement it rejects the entry",
  "seq":           "integer >= 0; monotonic per (topic, epoch); NOT globally ordered",
  "epoch":         "string; outbox epoch for durable topics, publisher epoch for ephemeral",
  "producer_id":   "string; identifies the process instance that wrote the entry",
  "origin_ts":     "RFC 3339 UTC instant from the producer's clock; NOT an ordering key",
  "payload_kind":  "enum: arrow_ipc | control",
  "payload_schema":"string; the schema identifier the payload conforms to",
  "payload":       "arrow_ipc: base64 IPC batch; control: an inline object"
}
```

```yaml
# schema/stream/topics.yaml  — shape of one declaration
topics:
  <name>:
    class: durable | ephemeral
    retention:
      duration: <ISO 8601 duration>   # the smaller of the two bounds wins
      entries: <integer>
    backpressure:
      coalesce: false                 # durable topics: must be false
      coalesce_key: [<field>, ...]    # present only when coalesce is true
      on_overflow: lag | coalesce
    payload_schema: <identifier resolving to a file in this repository>
    replay: unbounded | retention_only
    notes: <free text; why a value deviates from the architecture>
```

```python
# q_contracts/tools/validate.py  (extended)

def check_stream_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Cross-document rules between topics.yaml and envelope.schema.json.

    Rules enforced, each producing a problem naming the offending topic:
      - every topics.yaml key is an accepted value of the envelope's `topic` enum
      - every envelope topic enum value is declared in topics.yaml
      - class == durable implies backpressure.coalesce is false
      - class == ephemeral implies replay == retention_only
      - payload_schema resolves to an existing file under schema/
      - coalesce_key is present iff coalesce is true
    """
```

## Implementation decisions

- **The envelope carries `epoch` on every entry rather than only on transitions.**
  A consumer that connects mid-stream has no transition to observe; if the epoch
  arrived only when it changed, such a consumer would validate its sequence
  against an epoch it inferred, and would accept a stale sequence as fresh
  after a Redis restart. Per-entry epoch costs a small field and removes the
  entire class.

- **`seq` is documented as per-topic and not globally ordered, in the schema's own
  description text.** The failure this avoids is a client author building a
  single merged timeline across topics and concluding that a `fills` entry
  preceded the `orders` entry that caused it. The description is where a
  generated-type reader will actually see it, which is why the prose lives in
  the schema and not only in the architecture document.

- **The Redis stream identifier is deliberately absent from the envelope.** It is
  assigned by the transport, differs between a live read and a replay of the same
  logical entry, and is exactly the value a client would otherwise be tempted to
  deduplicate on. Deduplicating on a transport-assigned id silently fails after a
  relay restart republishes the same outbox row. Keeping it out of the envelope
  makes the correct key — `(topic, epoch, seq)` — the only key available.

- **`origin_ts` is explicitly labelled as unsuitable for ordering.** Two producers'
  clocks are not comparable and a single producer's clock can move backwards.
  Labelling it in the schema rather than trusting convention is the difference
  between a client author sorting by timestamp and a client author asking why not.

- **`payload_kind` and `payload_schema` are separate fields.** `payload_kind`
  decides the decoder, `payload_schema` decides the interpretation. Folding them
  into one string would mean a consumer has to parse an identifier to learn
  whether to run an Arrow reader, and identifier parsing is where such things
  break when a new schema name is introduced.

- **Arrow payloads are carried base64-encoded inside a JSON envelope rather than
  as a binary frame with a JSON header.** The envelope is defined logically here
  and its transport framing is Q-006's and the backend's concern; a base64 form
  gives the schema a single self-contained representation that examples and tests
  can exercise today. The binary framing that avoids the 33% expansion is a
  transport optimization applied where the transport is implemented, and the
  logical envelope is unchanged by it.

- **The topic policy is YAML, not JSON.** It is the one file in the repository a
  human reads and edits by hand to tune retention, and it needs comments to
  record why a value deviates from the architecture's starting value. JSON cannot
  carry the comment, and a `notes` field alone does not survive contact with a
  developer changing a number in a hurry. The dialect extension to
  `SUPPORTED_DIALECTS` is made here because this is the task that introduces it.

- **Retention carries both a duration and an entry count, with the smaller
  winning.** A duration alone lets a burst blow the memory budget; a count alone
  lets a quiet topic retain week-old entries that a consumer will treat as
  current. The architecture's starting values are transcribed: roughly 24 hours
  or 200k entries for durable topics, roughly one hour for `quotes` and
  `bars.forming`, roughly 24 hours for `bars.completed` and `jobs.progress`.

- **Class invariants are enforced by the validator, not by documentation.** The
  specific failure avoided is a future author adding `coalesce: true` to `fills`
  to fix a backpressure incident, which would lose a fill and be discovered only
  in a reconciliation. A rule that the file cannot express is a rule that cannot
  be broken in a hurry at 2am.

- **`jobs.terminal` is a separate durable topic from the ephemeral
  `jobs.progress`, and the policy file records the pairing in `notes`.** Progress
  may be coalesced to the latest value for a job; a completion may not be dropped.
  One topic cannot have both policies, so the split is structural rather than
  conventional, and writing the pairing down is what stops a later author from
  "simplifying" them back together.

- **Control frames get individual schema files rather than a single oneOf
  document.** Q-006 generates a named type per file, and a single document would
  generate one union type that every consumer has to narrow by hand. Five files
  produce five types with the names the protocol already uses.

- **`check_stream_consistency` is added to `check_tree` rather than exposed as a
  second command.** The spec requires one validation command; a second command is
  one a developer will not run and CI will.

## Ordered implementation

1. Create the branch `Q-002-stream-envelope-and-topic-policy-spec`.
2. Extend `SUPPORTED_DIALECTS` and `check_file` to accept YAML policy files under
   `schema/stream/`. Write the failing unit test first: a well-formed
   `topics.yaml` yields no problems, and a `topics.yaml` that is not a mapping at
   its root yields one problem naming the file. Confirm they fail, implement,
   confirm they pass. Commit.
3. Write `schema/stream/envelope.schema.json` with the nine fields above, each
   carrying a `description` that states its unit, its ordering role, and — for
   `seq`, `origin_ts`, and the absent stream id — what it must not be used for.
   Add `examples/envelope-arrow.json` and `examples/envelope-control.json`.
   Confirm `make check` passes. Commit.
4. Write failing tests asserting that the envelope validates both examples, and
   that three mutated copies — one with `seq` removed, one with `epoch` removed,
   one with `topic` removed — each fail with the missing field named in the error.
   Confirm they fail, then adjust the schema's `required` list until they pass.
   Commit.
5. Write the five control frame schemas. Write failing tests asserting that a
   `subscribed` example carrying `{cursor, epoch, last_seq}` per topic validates,
   that a copy with `epoch` removed from one topic's entry fails, that a copy with
   `last_seq` removed fails, and that a `lagging` example without `from_seq`
   fails. Confirm they fail, implement, confirm they pass. Commit.
6. Write `schema/stream/topics.yaml` declaring the twelve topics: durable
   `decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments`,
   `jobs.terminal`; ephemeral `quotes`, `bars.forming`, `bars.completed`,
   `jobs.progress`. Transcribe the retention and backpressure values from the
   architecture, with `quotes` coalescing on `[symbol]`, `bars.forming` on
   `[symbol, timeframe]`, `jobs.progress` on `[job_id]`, and every durable topic
   and `bars.completed` non-coalescing with `on_overflow: lag`. Add the envelope's
   `topic` enum listing the same names. Commit.
7. Write failing tests for `check_stream_consistency`, one per rule, each over a
   temporary tree: a durable topic with `coalesce: true` yields one problem whose
   text contains that topic's name; an ephemeral topic with `replay: unbounded`
   yields one problem naming it; a topic in `topics.yaml` absent from the envelope
   enum yields one problem naming it; the reverse case likewise; a
   `payload_schema` pointing at a nonexistent file yields one problem naming both
   the topic and the path; `coalesce_key` present with `coalesce: false` yields
   one problem. Run them and confirm they fail.
8. Implement `check_stream_consistency` and call it from `check_tree`. Confirm the
   tests pass and that `make check` exits zero over the real tree. Commit.
9. Add a test asserting the delivered `topics.yaml` yields no consistency
   problems, so a later edit that breaks an invariant fails a named test rather
   than only the tree walk. Commit.
10. Human step, matching human-verifiable criterion 1: read `topics.yaml` end to
    end against §4.3 and §4.4 of the architecture and confirm every retention and
    backpressure value matches, recording any deviation in that topic's `notes`.
11. Human step, matching human-verifiable criterion 2: read the `description`
    text of `seq`, `epoch`, and `origin_ts` in `envelope.schema.json` and confirm
    it states the cursor-versus-watermark distinction in prose a client author
    will act on.
12. Run the full validation suite and commit. Report the handoff.

## Validation

- **Unit:** each `check_stream_consistency` rule against a temporary tree that
  violates exactly that rule; envelope validation of both example payload kinds
  and of the three field-removal mutants; control frame validation including the
  two `subscribed` mutants and the `lagging` mutant.
- **Integration:** `make check` over the real tree, which runs discovery, per-file
  checks, and cross-document consistency in one pass.
- **Regression:** `make check` must still exit zero on the Q-001 tree shape — the
  YAML dialect extension must not cause any existing JSON Schema file to be
  evaluated by the YAML rules. Assert this with a test that a JSON schema file
  placed under `schema/stream/` is still checked as JSON Schema.
- **Manual:** steps 10 and 11.

```bash
cd /home/gui/projects/q/q_contracts
make check
uv run pytest tests/test_validate.py -k stream -v
# confirm the delivered tree is consistent, and that breaking it is caught
uv run python - <<'PY'
import subprocess, pathlib, shutil
p = pathlib.Path("schema/stream/topics.yaml")
orig = p.read_text()
p.write_text(orig.replace("coalesce: false", "coalesce: true", 1))
print("exit:", subprocess.run(["uv","run","python","tools/validate.py"]).returncode)
p.write_text(orig)
PY
```

## Handoff

Report the twelve topic names as delivered, each with its class, its two
retention bounds, and its coalescing key or the fact that it has none — this
table is what the backend's relay and the two clients will implement against, and
it is the thing most likely to be misremembered. Report any value that deviates
from §4.3 or §4.4 of the architecture together with the reason recorded in its
`notes` field, or state explicitly that there are none. Report the exact error
text produced for each of the six consistency rules, since those messages are the
only diagnosis a future author gets. Confirm that `check_stream_consistency` runs
inside `make check` and not as a separate command, and confirm that the Redis
stream identifier appears nowhere in the envelope schema.
