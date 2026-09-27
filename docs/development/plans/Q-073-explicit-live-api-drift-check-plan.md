# Explicit Live API Drift Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep normal contracts CI independent of a running backend while preserving an explicit live route comparison.

**Architecture:** Exclude the live drift test from the default pytest selection and run it only through `make check-live`. The explicit target requires a caller-provided URL and fails when that target is unavailable.

**Tech Stack:** Make, Python, pytest.

**Spec:** [`../specs/Q-073-explicit-live-api-drift-check-spec.md`](../specs/Q-073-explicit-live-api-drift-check-spec.md)

## Global constraints

- Normal `make check` must never contact a backend.
- `make check-live` is read only and requires an explicit URL.
- Schema and generated contract content remain unchanged.

## Review focus

- An ambient `Q_API_BASE_URL` must not enable the check in normal CI; cover in Task 1.
- A listening local backend must not alter normal CI results; cover in Task 1.
- Missing or unreachable live URL must fail rather than skip; cover in Task 1.
- A route mismatch must remain a useful failure; cover in Task 1.
- The opt-in command must issue only the OpenAPI GET; cover in Task 1.

---

### Task 1: Separate repository validation from live route comparison

**Files:** `Makefile`, `tests/test_api_drift.py`, `tests/test_capture_api.py`, `README.md`

**Interface:** `make check` runs offline checks; `make check-live Q_API_BASE_URL=<url>` runs the existing route comparison against the given backend.

- [ ] Add focused tests that make a normal check fail if `fetch_openapi` is called, even with `Q_API_BASE_URL` set; check that the explicit command rejects a missing/unreachable URL and still reports a route mismatch.
- [ ] Run the focused tests and confirm failures against current behavior.
- [ ] Mark and exclude the live test from normal pytest selection, require `Q_API_BASE_URL` for the explicit target, and make connection errors fail with the target URL. Keep the request as `GET /openapi.json`.
- [ ] Document the offline/default and explicit/live commands in `README.md`.
- [ ] Run focused tests and `git diff --check`; commit the task changes.

## Handoff

Use the task branch created by `./work start Q-073 --agent <agent>` after the plan is approved.
