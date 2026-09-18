# Wine Edge Boundary

This directory holds schemas describing the wire contracts for edge processes running under Wine/Windows environments.

## What Belongs Here

- Data-gateway wire contracts and IPC/network formats connecting edge platform terminals.
- Order execution edge contracts with intent-at-most-once semantics.
- Gateway command, request, and telemetry schemas for edge bridges.
- Canonical intent derivation formula (`magic` and `comment`) mapping order UUIDs deterministically with refusal rules (`intent_field_mismatch`).
- Terminal account operation (`/v1/account`) querying live broker status, trading permissions, and float balances.

## What Does Not Belong Here

- General control API or web client payloads (belong in `schema/api/`).
- Central event stream envelopes or topic policies (belong in `schema/stream/`).
- Lake dataset manifests (belong in `schema/catalog/`).
- Generated bridge code or platform binaries (belong in `generated/`).

## Populating Tasks

- **Q-004** (`Wine Edge Wire Contracts`): Data gateway and execution edge baseline contracts and process obligations.
- **Q-039** (`Execution event payloads and command idempotency`): Deterministic intent derivation formula and test vectors, refusal rule for disagreeing caller fields, and read-only `/v1/account` operation.
