# Wine Edge Boundary

This directory holds schemas describing the wire contracts for edge processes running under Wine/Windows environments.

## What Belongs Here

- Data-gateway wire contracts and IPC/network formats connecting edge platform terminals.
- Order execution edge contracts with intent-at-most-once semantics.
- Gateway command, request, and telemetry schemas for edge bridges.

## What Does Not Belong Here

- General control API or web client payloads (belong in `schema/api/`).
- Central event stream envelopes or topic policies (belong in `schema/stream/`).
- Lake dataset manifests (belong in `schema/catalog/`).
- Generated bridge code or platform binaries (belong in `generated/`).

## Populating Task

This boundary is populated by task **Q-004** (`Wine Edge Wire Contracts`).
