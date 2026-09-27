# Q-073: Make live API drift check explicit

**Status:** plan pending approval on the Q project board  
**Implementation plan:** [`../plans/Q-073-explicit-live-api-drift-check-plan.md`](../plans/Q-073-explicit-live-api-drift-check-plan.md)

## Problem

`make check` runs all of `pytest`, including `tests/test_api_drift.py`. That test
silently connects to `http://127.0.0.1:8000/openapi.json` when a backend is
running and skips otherwise. The same CI command can therefore yield a
different result depending on an unrelated local service. The request is read
only, but it crosses the CI environment boundary.

## Requirements

1. Normal `make check` and GitHub Actions CI validate schemas and generators
   entirely from repository files and fixtures. They never contact a running
   backend, even when one is listening on port 8000 or `Q_API_BASE_URL` is set.
2. Retain an explicit `make check-live` command for comparing the committed
   routes with a selected backend. Require an explicit base URL; do not default
   to the development API or silently skip an unreachable target.
3. Keep the live check read only and document its opt-in purpose and invocation
   in the README. Do not change the schema or generated contract contents.

## Acceptance criteria

- A focused test or command mock proves normal `make check` cannot call
  `fetch_openapi`, regardless of `Q_API_BASE_URL` or a running local API.
- `make check-live Q_API_BASE_URL=<url>` fetches only `/openapi.json`, reports
  route drift, and fails clearly when the URL is absent or unreachable.
- `git diff --check` and focused validation of the Makefile/test behavior pass.
