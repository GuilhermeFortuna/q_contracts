# Q-004: Wine edge wire contracts

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** Q-001  
**Implementation plan:** [`../plans/Q-004-wine-edge-wire-contracts-plan.md`](../plans/Q-004-wine-edge-wire-contracts-plan.md)

## Purpose

The boundary between Linux and the MetaTrader terminal is the one place in the
system where a contract violation loses money rather than a render frame, and it
is currently described in a module docstring inside the process that implements
it. The Linux-side client codes against prose, and the execution edge that will
carry orders does not exist yet. This task moves the existing data-gateway wire
contract into `q_contracts` without changing it, and specifies the execution edge
alongside it, so that the edge processes, the Linux client, and the execution
worker are all built against one description — and so that the at-most-one-
submission rule is a property of the contract rather than of whoever writes the
worker.

## Requirements

### Two contracts, not one

- The data gateway and the execution edge are described as separate contracts
  with separate schema majors, because they are separate processes with separate
  lifetimes and one may be replaced without the other.
- Both declare the same process-level obligations: a health endpoint reporting
  connectivity and terminal build, refusal of a mismatched schema major, and
  loopback-only binding for the execution edge.
- Both declare that the implementing process may depend only on the standard
  library plus the MetaTrader module and the array library, because the Wine
  interpreter has nothing else, and a contract that permits more will eventually
  be implemented with more.

### Data gateway: captured, not redesigned

- The data-gateway contract describes the endpoints the running gateway serves
  today, with the same paths, the same query parameters, the same response
  encodings, and the same schema version.
- The timestamp convention is stated explicitly as part of the contract: the
  wall-clock, timezone-naive interpretation the gateway applies, and the fact
  that the gateway performs no timezone conversion.
- The binary response encoding and its array names, dtypes, and length equality
  are part of the contract, not an implementation detail, because the Linux
  client reconstructs typed arrays from them.
- The error vocabulary is declared: which conditions produce which status and
  which machine-readable code, including the case where the terminal is
  unreachable but the process is healthy.
- Nothing in the captured contract changes the wire. A difference between the
  contract and the running gateway means the contract is wrong.

### Execution edge: new

- The execution edge exposes quote retrieval, order pre-check, order submission,
  intent lookup, open positions, and deal history.
- Every submission carries an intent identifier minted by the caller, and the
  contract states that the edge attempts at most one submission per identifier
  for the lifetime of its process, answering a repeat with a distinct duplicate
  outcome rather than submitting again.
- The intent identifier's placement in the broker-visible fields the terminal
  will echo back is part of the contract, because lookup depends on being able to
  find it afterwards.
- Lookup takes an intent identifier and a time window and returns exactly one of:
  filled with deal detail, rejected, not found, or unavailable. The contract
  states which of these close an intent and which leave it pending, because
  treating unavailable as not-found is the failure that produces a duplicate
  order.
- The contract states that the edge never retries, never resubmits, and never
  invents an outcome; ambiguity is reported as ambiguity.
- The edge is described as stateless across restarts and idempotent only within a
  process lifetime, so no caller may rely on its memory as the authoritative
  deduplication.

### Safety properties expressed in the contract

- A submission response distinguishes an accepted submission, a broker rejection,
  and an indeterminate outcome, and the indeterminate case is a first-class
  response rather than an error the caller must interpret.
- A transport timeout is documented as indistinguishable from an indeterminate
  outcome, and the contract states the caller's obligation in that case.
- Quote responses carry the age of the quote, so a caller can apply a freshness
  gate without trusting its own clock against the terminal's.

### Checkability

- Both contracts are validated by the repository's existing validation command.
- The data-gateway contract is checked against the running gateway implementation
  by a test, so that moving the contract out of the docstring does not begin a
  new drift.

## Constraints and non-goals

- **No change to `q_backend/gateway/mt5_gateway.py`.** The contract is extracted
  from it; the file itself is edited in a later task, when it is changed to
  reference the contract rather than restate it. The temptation is to delete the
  docstring now, which would leave the running process with no description until
  the consumer repositories vendor generated types.
- **No execution edge implementation.** Not a stub, not a fake, not a test
  double that lives in `q_contracts`. The edge is implemented in `q_backend`
  in a later batch.
- **No changes to the execution worker.** Intent identity, the ledger, leases,
  and reconciliation stay exactly as they are; this task describes the wire the
  worker will eventually speak, not the worker.
- **No tier B content.** The Expert Advisor supervision protocol — signed limit
  updates, heartbeats, the local kill flag — is a separate contract belonging to
  the conditional tier B phase, and specifying it now would be designing against
  a strategy that does not exist.
- **No transport security.** The shared-token scheme the gateway already uses is
  captured as-is; no certificate, signature, or key-rotation scheme is designed.
- **No broker abstraction.** The contract describes a MetaTrader edge. Making it
  generic over brokers would produce a lowest common denominator that fits one
  broker badly.

## Acceptance criteria

### Agent-verifiable

1. Two contracts exist under the edge boundary, each declaring its own schema
   major, and both pass the repository's validation command.
2. The data-gateway contract declares every endpoint the running gateway serves,
   verified by a test that reads the gateway's own route table and compares.
3. The data-gateway contract's schema version matches the version constant the
   running gateway declares, verified by a test.
4. The binary response array names and dtypes in the contract match those the
   running gateway produces, verified against a real artifact.
5. The timestamp convention is declared, and a test asserts the contract states a
   naive wall-clock interpretation with no conversion.
6. The execution edge contract declares all six operations, each with a request
   and response schema, and an example of each validates.
7. The submission response schema admits exactly three outcomes — accepted,
   rejected, indeterminate — and an example claiming any other outcome fails
   validation.
8. The lookup response schema admits exactly four outcomes, and the contract
   declares for each whether it closes the intent.
9. A submission example lacking an intent identifier fails validation.
10. The quote response schema requires a quote age field, and an example omitting
    it fails validation.
11. Both contracts declare the standard-library-only dependency obligation.
12. The full validation suite passes.

### Human-verifiable

1. The execution edge contract is read end to end against §6.2 and §6.3 of the
   architecture and confirmed to permit no path by which one intent identifier
   results in two submissions.
   Command: `$EDITOR q_contracts/schema/edge/execution.yaml`
2. The data-gateway contract is diffed against the docstring it was extracted
   from, and every behavioral statement in the docstring is confirmed present in
   the contract or explicitly recorded as intentionally dropped.
   Command: `sed -n '1,80p' q_backend/gateway/mt5_gateway.py`
