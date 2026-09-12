# Control API Boundary

This directory holds schemas describing the control and configuration API surface, including REST endpoints, job payloads, and columnar query payloads exchanged with the control service.

## What Belongs Here

- OpenAPI documents describing the control REST surface and job submission/status contracts.
- Apache Arrow schema definitions for columnar API responses and query payloads.
- Control-plane request and response contracts.

## What Does Not Belong Here

- Event stream message payloads or topic policies (belong in `schema/stream/`).
- Edge gateway protocol contracts or bridge payloads (belong in `schema/edge/`).
- Lake dataset catalog manifests (belong in `schema/catalog/`).
- Generated client code, server stubs, or language-specific bindings (belong in `generated/`).

## Populating Task

This boundary is populated by task **Q-003** (`Control API and Columnar Schemas`).
