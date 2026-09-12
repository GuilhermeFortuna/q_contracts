# Edge Process Obligations

This document specifies the process-level obligations and runtime constraints imposed on all edge services running within the Wine / Windows environment (both the **Data Gateway** and the **Execution Edge**). Both edge wire contracts reference this document as authoritative.

---

## 1. Minimal Dependencies (Stdlib + MetaTrader + Array Library Only)

- **Allowed dependencies:** Python standard library + `MetaTrader5` + `numpy` (the array library) **only**.
- **Forbidden dependencies:** Edge services must **never import `q_backend`** or any package from `src/`, nor any additional third-party dependencies.
- **Rationale:** Edge processes execute inside a Wine prefix or isolated Windows environment where only the minimal Python runtime, the MetaTrader 5 terminal Python wheel, and its prerequisite `numpy` package are installed. Introducing additional dependencies causes silent execution failures inside the Wine prefix that pass local Linux developer checks.

---

## 2. Health & Connectivity Telemetry

- Every edge process must expose a `/v1/health` endpoint answering HTTP 200.
- The health response payload must conform to [`schema/edge/common/health.schema.json`](common/health.schema.json) and include:
  - `status`: String indicator of service status (e.g. `"ok"`).
  - `schema_version`: The wire schema version served by the process.
  - `mt5_connected`: Boolean indicating whether the IPC link to the MetaTrader 5 terminal is active and initialized.
  - `terminal_build`: The integer build number of the connected MetaTrader terminal (or `null` if MT5 is unavailable).
- **Resilience:** The health endpoint must never raise an unhandled exception or return a 5xx status code solely because the terminal is disconnected or uninitialized.

---

## 3. Schema Major Validation & Rejection

- Edge processes declare an explicit `schema_major` (currently `1`).
- Breaking changes require bumping `schema_major` and relocating endpoints (e.g. from `/v1/` to `/v2/`).
- The edge process must reject requests presenting an unsupported schema major with HTTP 400 and error code `schema_major_mismatch`.

---

## 4. Network Binding & Transport Security

- **Execution Edge:** The execution edge carries real order submissions and account state. It **must bind to loopback (`127.0.0.1`) only**. It must never listen on public or non-loopback network interfaces.
- **Data Gateway:** The read-only market data gateway may bind to non-localhost interfaces only when protected by shared-secret authentication. When `--token` / `MT5_GATEWAY_TOKEN` is configured, all requests must supply a matching `X-Gateway-Token` header or receive HTTP 401 `unauthorized`.

---

## 5. Execution Edge Safety & Lifecycle Invariants

- **At-Most-One Submission:** The execution edge must attempt at most one order submission per `intent_id` for the lifetime of its process. A duplicate submission request with an already-seen `intent_id` must be rejected with error `duplicate_intent` rather than submitted again.
- **Intent Identifier Placement:** Every order submitted to MetaTrader must encode the caller's `intent_id` in the broker-visible fields (`magic` and `comment`) using the system-standard derivation (`intent_magic` and `intent_comment`).
- **No Autonomous Retries:** The edge process must never retry, never resubmit, and never invent an outcome. Indeterminate or timed-out states must be reported directly as `indeterminate`.
- **Stateless Across Restarts:** The execution edge does not persist intent history across process restarts. Deduplication within the edge is scoped strictly to the process lifetime; authoritative persistence remains the responsibility of the Linux-side ledger and execution worker.
