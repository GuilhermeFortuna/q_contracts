# Q-002: Stream envelope and topic policy

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** Q-001  
**Implementation plan:** [`../plans/Q-002-stream-envelope-and-topic-policy-plan.md`](../plans/Q-002-stream-envelope-and-topic-policy-plan.md)

## Purpose

The architecture replaces REST polling with an event stream whose correctness
rests entirely on three fields travelling with every entry — a per-topic
sequence, an epoch, and a topic name — and on each topic having a declared
durability class, retention bound, and backpressure policy. Today none of this
is written down anywhere a program can read: the frontend's eleven polling
queries encode no ordering assumptions at all, and the snapshot-then-delta
protocol has no schema to validate against. This task writes the envelope schema
and the topic policy file so that every producer and every consumer, in four
languages, agrees on what an entry is and what its topic promises. It is the
prerequisite for the outbox relay, the WebSocket endpoint, and every client-side
gap-detection path in later batches.

## Requirements

### Envelope shape

- Every stream entry carries its topic, a sequence number, an epoch, a producer
  identity, and a producer-clock origin timestamp, alongside its payload.
- The sequence number is monotonic within a topic and within an epoch, and the
  envelope makes clear that it is not globally ordered across topics.
- The epoch is the value whose change invalidates every sequence a consumer has
  seen for that topic, and the envelope carries it on every entry rather than
  only on epoch transitions, so a consumer that joins mid-stream can detect
  staleness from the first entry it reads.
- The origin timestamp is a producer-clock UTC instant and is documented as
  unsuitable for ordering, because ordering is the sequence number's job and two
  producers' clocks are not comparable.
- The payload is either a binary columnar batch or a structured control frame,
  and the envelope declares which, so a consumer never guesses at the decoding.
- The envelope carries a schema major, and a consumer that reads an entry whose
  major it does not implement is required to reject the entry rather than
  attempt a best-effort decode.
- The Redis stream identifier is not part of the envelope, because it is a
  replay cursor owned by the transport, and conflating it with the ordering
  watermark is the specific mistake this schema exists to prevent.

### Topic declaration

- Every topic in the system is declared in one machine-readable file, and a
  topic that is not declared there does not exist.
- Each declaration states the topic's durability class — durable or ephemeral —
  and that class determines who assigns its sequence and what replay it offers.
- Each declaration states its retention bound, expressed both as a duration and
  as an entry count, with the smaller bound winning.
- Each declaration states its backpressure policy: whether entries may be
  coalesced, and if so the key they are coalesced on, or that they may never be
  coalesced and overflow instead marks the consumer as lagging.
- Each declaration names the payload it carries, by reference to a schema, so
  that a topic's entries can be validated without the reader knowing which
  producer wrote them.
- The declarations cover exactly the topics the architecture defines, and adding
  a topic is a change to this file and nothing else.

### Class invariants

- Durable topics may never be coalesced and never dropped; the file cannot
  express a coalescing policy for a durable topic, and an attempt to do so is a
  validation failure rather than a comment someone might ignore.
- Ephemeral topics may not claim unbounded replay, because their source of truth
  is a live publisher that forgets.
- The terminal states of a job are carried by a durable topic even though job
  progress is ephemeral, and the file records this pairing explicitly so that no
  consumer treats a completion as droppable.

### Control frames

- The frames of the subscribe-then-snapshot protocol — subscription, subscription
  acknowledgement, cursor expiry, lag notification, and epoch change — have
  declared shapes, because they are cross-process payloads like any other.
- The acknowledgement frame carries, per subscribed topic, the cursor from which
  forwarding begins together with that topic's current epoch and last sequence,
  since a consumer cannot reconcile a snapshot against a stream without all
  three.
- A lag notification names both the topic and the sequence from which the
  consumer's view is incomplete, so recovery is a bounded fetch rather than a
  full re-snapshot where a full re-snapshot is not required.

### Consistency between envelope and policy

- The two documents are checked against each other: every topic named in a
  declaration is a legal topic value in the envelope, every payload reference
  resolves, and every class invariant holds.
- The check is part of the repository's existing validation command and adds no
  second command.

## Constraints and non-goals

- **No implementation of the stream.** No Redis client, no `XADD`, no relay, no
  WebSocket endpoint, no subscriber. Those are `q_backend` tasks in a later
  batch. The temptation is to write a reference publisher to "prove" the schema;
  a reference publisher is an implementation that will be maintained forever and
  will disagree with the real one.
- **No generated types.** Q-006 generates from these files; this task produces
  only the hand-authored sources.
- **No retention tuning.** The numbers written here are the architecture's
  starting values, recorded so they can be changed by measurement later. This
  task does not measure anything and does not claim the values are right.
- **No Arrow schemas for the columnar payloads.** The envelope declares that a
  payload is a columnar batch and which schema it conforms to; the schemas
  themselves belong to Q-003.
- **No transport framing.** How an envelope is written onto a WebSocket frame or
  a Redis entry — field encoding, compression, chunking — is not decided here.
  This task defines the logical entry only.
- **No authentication or authorization fields.** The stream is loopback-local in
  the current topology; adding a principal to the envelope now would be
  speculative and would have to be designed again when it is real.

## Acceptance criteria

### Agent-verifiable

1. The envelope schema exists under the stream boundary, declares every required
   field, and validates a hand-written example entry of each payload kind.
2. An example entry missing its sequence, its epoch, or its topic fails
   validation, and the failure names the missing field.
3. The topic policy file declares every topic named in the architecture, each
   with a class, a retention duration, a retention entry count, a backpressure
   policy, and a payload reference.
4. Every payload reference in the policy file resolves to a schema that exists in
   the repository.
5. A durable topic given a coalescing policy fails the consistency check, and the
   failure names the topic.
6. An ephemeral topic claiming unbounded replay fails the consistency check, and
   the failure names the topic.
7. A topic declared in the policy file but not accepted by the envelope's topic
   field fails the consistency check, and the failure names the topic.
8. Each control frame has a schema, and an acknowledgement example lacking the
   epoch or last-sequence for a subscribed topic fails validation.
9. The consistency check runs as part of the repository's single validation
   command, not as a separate command.
10. The full validation suite passes.

### Human-verifiable

1. The policy file is read end to end and each retention value is confirmed to
   match the architecture's stated starting value, with any deviation recorded
   in the file with its reason.
   Command: `$EDITOR q_contracts/schema/stream/topics.yaml`
2. The envelope's field documentation is confirmed to state, in prose a client
   author will read, that the Redis stream identifier is the replay cursor and
   the sequence is the ordering watermark, and that the two are different things.
   Command: `$EDITOR q_contracts/schema/stream/envelope.schema.json`
