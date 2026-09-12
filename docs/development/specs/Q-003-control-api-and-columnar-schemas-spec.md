# Q-003: Control API and columnar payload schemas

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** Q-001  
**Implementation plan:** [`../plans/Q-003-control-api-and-columnar-schemas-plan.md`](../plans/Q-003-control-api-and-columnar-schemas-plan.md)

## Purpose

The control surface between `q_backend` and its clients is defined twice — as
Pydantic models in the backend and as hand-written TypeScript interfaces in the
frontend — with nothing checking that the two agree. A field renamed on one side
is discovered at runtime, in the workspace that happens to read it. This task
captures the surface that exists today as a single machine-readable description,
and adds Arrow schemas for the columnar payloads that the stream and the
visualization path will carry, so that Q-006 has something to generate from and
so that the third and fourth consumers — `q_terminal` and the execution edge —
never need a hand-written mirror at all. Capturing what exists, rather than
designing what should exist, is deliberate: the value is in removing the second
copy, not in redesigning the API while doing it.

## Requirements

### Faithfulness to the running system

- The description matches the endpoints the backend serves today, including paths,
  methods, status codes, request bodies, response bodies, and query parameters.
- Where the running API and the description disagree, the description is wrong
  and is corrected; this task does not change the API to match a nicer
  description.
- Discrepancies found while capturing — a response field that is optional in
  practice but required in the model, an endpoint the frontend calls that does
  not exist, a field the frontend reads that the backend never sends — are
  recorded as findings rather than silently reconciled, because each is a latent
  bug and some are more than a schema problem.
- The description is checked against the running application by a test, not by
  reading, so that it cannot drift without something failing.

### Coverage

- Every router the backend mounts is represented.
- The job lifecycle payloads are represented: submission, the identifier
  returned, the status a client polls, progress while running, and the terminal
  result or error.
- Command idempotency is expressed: the commands that carry a client-generated
  idempotency key declare it, and the description states that a repeated key
  returns the stored result rather than acting twice.
- Error responses have a declared shape, and it is one shape across the surface
  rather than one per router.

### Columnar payloads

- Every payload that travels as a columnar batch has a declared Arrow schema:
  field names, types, nullability, and units.
- The columnar schemas cover the market-data shapes the system already moves —
  bars and ticks — with field names and types matching what the existing store
  and gateway produce, so that adopting the schema does not silently reinterpret
  stored data.
- Timestamp fields declare their unit and their timezone convention explicitly,
  including the cases where the existing system uses a naive wall-clock value,
  because that convention is load-bearing and undocumented today.
- Each columnar schema is referenceable by the identifier that the stream
  envelope's payload reference uses, so a topic can name its payload and a
  consumer can resolve it.

### Relationship to the stream

- A columnar schema is defined once and referenced by both the REST description
  and the topic policy; the same bars that arrive over the stream are the bars a
  REST history call returns.
- The description declares which REST endpoints serve the history and snapshot
  roles the stream protocol depends on, so the subscribe-then-snapshot sequence
  can be implemented from the contract alone.

## Constraints and non-goals

- **No API redesign.** Not a renamed field, not a collapsed endpoint, not a
  corrected pluralization. The surface is captured as it is. Every improvement
  this task makes obvious becomes a recorded finding and, where warranted, a
  later task.
- **No new endpoints.** The outbox history endpoints and the `latest` endpoints
  that the stream protocol needs are described only to the extent they already
  exist; where they do not, that is recorded as a finding and specified in the
  batch that builds them.
- **No changes to `q_backend`.** The backend is read and exercised, not edited.
  The test that checks the description against the running application lives in
  `q_contracts`.
- **No generated clients.** Q-006 generates types. This task produces the
  description and the columnar schemas only.
- **No Parquet layout decisions.** How bars are stored on disk, partitioned, or
  named is Q-005's and the backend's concern. This task describes the wire shape.
- **No authentication scheme.** The API is loopback-local today; describing a
  scheme that does not exist would be fiction.

## Acceptance criteria

### Agent-verifiable

1. The API description exists under the API boundary, is a valid document in its
   declared dialect, and passes the repository's validation command.
2. Every router mounted by the backend today appears in the description, verified
   by comparing the description's paths against the application's own route table
   rather than against a list written by hand.
3. A test loads the description and the application's route table and fails when
   either contains a path or method the other does not.
4. The job lifecycle payloads are described, and an example of each validates
   against its schema.
5. A single error shape is declared and is referenced by every operation that can
   fail.
6. Operations carrying an idempotency key declare it, and the description states
   the stored-result-on-retry behavior.
7. Arrow schemas exist for the bar and tick payloads, with every field carrying a
   type and a unit, and timestamp fields carrying a timezone convention.
8. The bar and tick schemas' field names and types match what the existing local
   store and the existing gateway produce, verified by a test that reads a real
   stored artifact and compares its columns against the schema.
9. Every columnar schema is resolvable by the identifier form used in the stream
   topic policy's payload reference.
10. Findings are recorded in a document in the repository, each naming the
    endpoint or field, what was expected, and what the running system does.
11. The full validation suite passes.

### Human-verifiable

1. The findings document is reviewed and each finding is triaged as either a
   later task or an accepted deviation, with the decision recorded beside it.
   Command: `$EDITOR q_contracts/schema/api/FINDINGS.md`
2. The described surface is exercised against a running backend and the responses
   are confirmed to validate, for at least one operation per router.
   Command: `cd q_backend && uv run uvicorn q_backend.api.main:app --port 8000` then
   `cd q_contracts && make check-live`
