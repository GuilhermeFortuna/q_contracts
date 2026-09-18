# Q-039: Execution event payloads and command idempotency

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** [`q_contracts/docs/system-architecture.md` §4.1, §4.2, §4.5, §6.2, §9 invariant 2, §10 Phase 4](https://github.com/GuilhermeFortuna/q_contracts/blob/f2273a88e52c5b9a8ad5ac9d7eb27f8069cf643d/docs/system-architecture.md#10-roadmap)  
**Depends on:** Q-009  
**Implementation plan:** [`../plans/Q-039-execution-event-payloads-and-command-idempotency-plan.md`](../plans/Q-039-execution-event-payloads-and-command-idempotency-plan.md)

## Purpose

Phase 4 moves live trading into `q_terminal`, which may learn execution state
only from the stream and the control API. The six durable execution topics —
`decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments` — are declared
in the topic policy, but each still names the envelope itself as its payload,
so nothing states what an execution event carries. A terminal cannot apply a
delta whose shape is unknown, and the backend cannot write one without making
it up. The snapshot half of §4.2 has the same gap for execution: there is a
job snapshot shape but no execution one. Two further gaps sit on the paths
phase 4 makes live. Commands must carry a client idempotency key (§4.5), and
no contract says how. The edge contract requires the intent identifier in the
broker-visible `magic` and `comment` fields, but it names a Python function
instead of stating the derivation. The edge and the worker live on opposite
sides of Wine and must derive the same values. Finally, the live activation
gates check the trading account's login and whether trading is allowed, and
the edge contract has no operation that reports either, so a worker that no
longer imports `MetaTrader5` could not apply them.

This task closes those gaps additively, so that the batch-07 backend, edge and
terminal tasks build against the contract rather than against each other.

## Requirements

### Execution event payloads

- Each of the six durable execution topics has a payload schema of its own, and
  the topic policy points at it instead of at the envelope.
- Every execution event carries the **full current state of one entity** after
  the change it records: a deployment, a decision, an order, a fill, a risk
  event, a ledger entry, or the global control state. A consumer applies an event
  by replacing that entity, never by computing a difference. Replaying an event
  twice therefore leaves the same state.
- Every payload names the entity kind and its identifier, and carries the
  identifiers a consumer needs to place it: deployment, account and, where they
  apply, decision and order.
- A fill event also carries the deployment's net position after that fill, so a
  consumer can show positions without its own position arithmetic.
- A ledger event also carries the account's cash balance and realized profit and
  loss after that entry.
- Kill-switch changes are events on `risk`, with the actor and the time of the
  change.
- Order events carry the order status and the reconciliation state from one
  closed vocabulary each, taken from today's backend enums. The intent
  identifier is a field of its own.
- Monetary and quantity values are exact decimal strings, not binary floats, as
  they are in today's control API responses.
- Every execution topic carries its deployment identifier as a routing key
  value (account-level events carry the account identifier). No consumer logic
  may depend on these keys, because the topics do not coalesce.

### Execution snapshot

- A response schema describes the execution snapshot: the current deployments,
  accounts, open net positions, open and recent orders, and the global control
  state, with a watermark covering all six execution topics.
- Every entity in the snapshot has the same shape as that entity in its event
  payload. A consumer therefore handles one shape per entity.
- The snapshot declares how many recent decisions, fills, orders and risk events
  it includes, and that older ones come from history.

### Command idempotency

- The control API contract declares one request header that carries a
  client-generated idempotency key on mutating execution commands. It states
  the key's format, and that the server stores each key's result for 24 hours
  and returns that stored result on retry.
- Reusing a key for a different request is a declared error with its own
  machine-readable code, distinct from a validation error. A retry that arrives
  while the first request with that key is still executing is a separate,
  retryable error.
- The contract lists which commands require the key and which accept it
  optionally, and states that a command sent without a required key is refused.

### Intent field derivation

- The execution edge contract states the derivation of `magic` and `comment`
  from an intent identifier as a formula, and publishes test vectors: at least
  five identifiers with their expected `magic` and `comment`. The formula and
  vectors match what the backend derives today.
- The contract states that the edge derives both fields itself, and refuses a
  submission whose caller-supplied `magic` or `comment` disagree with the
  derivation.

### Account operation

- The execution edge contract gains a read-only account operation. It returns
  the account login, server, currency, whether trading is allowed for the
  account and for the terminal, balance, equity, and free margin. It answers
  unavailable, not an empty account, when the terminal is disconnected.
- The addition is additive within schema major 1.

### Generation and checks

- Every new schema is generated for Python, TypeScript and Rust by the existing
  generator, and the generated output is committed.
- The repository's validation fails if an execution topic points at the envelope
  again, if a snapshot entity diverges from its event payload shape, or if the
  derivation vectors disagree with the formula.

## Constraints and non-goals

- **No backend, edge or terminal implementation.** Emission is Q-043, the edge
  is Q-040, and the terminal store is Q-046.
- **No OpenAPI recapture of backend routes.** The control API document is
  captured from a running backend. The idempotency header and the execution
  snapshot route are described in this repository's API README and error
  vocabulary. They enter `openapi.yaml` when Q-043 and Q-044 recapture it.
- **No change to the envelope, framing, control frames or retention.** All
  changes are additive, and the schema major stays at 1.
- **No Arrow payloads for execution topics.** Execution events are small,
  infrequent and exact-decimal. They are JSON control payloads, like job events.
- **No change to the data-gateway contract.**

## Acceptance criteria

### Agent-verifiable

1. Each of the six execution topics in `topics.yaml` points at its own payload
   schema, and validation fails if any points at the envelope.
2. For each topic, one example per entity kind validates. An example missing its
   entity identifier or its deployment identifier fails.
3. A fill example without the post-fill net position fails validation. So does a
   ledger example without the post-entry balance, and an order example with a
   status outside the declared vocabulary.
4. A decimal field given as a JSON number fails validation.
5. The execution snapshot schema validates an example with every entity kind and
   a six-topic watermark. A test asserts that each snapshot entity shape equals
   the event payload shape for that entity.
6. The idempotency header, its 24-hour replay rule, the key-reuse error code and
   the list of covered commands are declared, and a test reads them.
7. The edge contract states the `magic` and `comment` derivation. A test checks
   at least five vectors against the formula, and the same vectors against
   `q_backend`'s `intent_magic` and `intent_comment` at a pinned backend commit.
8. The account operation has request and response schemas, and examples for
   a connected and a disconnected terminal validate. An account example without
   `login` or `trade_allowed` fails.
9. Generated Python, TypeScript and Rust contain every new type, and
   `make generate-check` is clean.
10. `make check` passes.

### Human-verifiable

1. The six payload schemas are read against the backend's execution tables and
   confirmed to carry every field the frontend execution workspace shows today,
   so that the terminal can reach parity from the stream and the snapshot alone.
   Command: `$EDITOR q_contracts/schema/stream/payloads/execution-*.schema.json`
2. The derivation section of the edge contract is read against §6.2 and
   confirmed to leave no way for the edge and the worker to derive different
   values for one intent.
   Command: `$EDITOR q_contracts/schema/edge/execution.yaml`
