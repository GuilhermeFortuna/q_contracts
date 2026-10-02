# Q-079 implementation plan: Trade stream and session history contracts

> **For implementation agents:** Read the linked spec and repository instructions.
> Use superpowers:executing-plans when that skill is available. Start only through
> `./work start Q-079 --agent <agent> --worktree` after written-plan approval and
> completed dependencies. Implement this task natively; delegation requires separate authorization.

**Goal:** Define a complete, ordered tape data path with session history, replay and explicit coverage.
**Architecture:** q_contracts owns wire schemas and generated metadata; hosts own ingestion/storage and presentation.
**Spec:** [Specification](../specs/Q-079-trade-stream-and-session-history-contracts-spec.md)
**Status:** implementation complete on the local task branch; awaiting review.

## Global constraints

- The linked spec defines the interface, defaults and acceptance criteria; do not widen scope.
- Use the existing repository toolchain and canonical checks without resource-slice wrappers.
- Commit focused changes on the task branch. Never push, merge or change protected branches.
- Report unavailable prerequisites with the documented board workflow; do not substitute shortcuts.

## Ordered implementation

- [x] 1. Add schema tests and small fixtures for identical trade multiplicity, raw flags, UTC timestamps, immutable page metadata, 202/410/503 and non-coalescing policy.
- [x] 2. Author the separate Arrow trade schema and additive gateway /v1/trades request/response metadata. Document eligibility, raw volume fields and volume-unit selection; leave ticks schema untouched.
- [x] 3. Declare trades/trades.status policies, source context, snapshot/history endpoints and generated response headers. Define the watermark join, token expiry and changed-generation recovery example in schema/stream/README.md.
- [x] 4. Regenerated Python/TypeScript/Rust output and verified the trade field/context names and identical-record example against Q-079. Q-080/Q-082 interface documents are not present in this repository, so consumer-side interface comparison remains for those tasks.
- [x] 5. Generated-output drift, all-file Black checks one file at a time, full Ruff, schema validation, and full pytest (205 passed, 7 skipped, 1 deselected) all pass. The canonical `make check` completes generation drift but hangs at its multi-file Black invocation in this host environment. The compatibility handoff is documented; Q-080/Q-081 must pin the merged contract commit. The Q-080/Q-082 specs are not present here, so their consumer-interface comparison remains with those tasks. All three final-review findings were fixed and verified with regression checks; implementation and review-fix commits are local.

## Review focus

- Identical trades are distinct source occurrences; the fixture retains both rows.
- A quote row with carried-forward last is excluded; eligibility fixtures check raw flags.
- A 202/expired token cannot masquerade as empty complete history; response examples validate status and coverage.
- Snapshot and live volume units/generations must match; negative schema fixtures exercise mismatch handling.
- Existing tick timestamp semantics remain untouched; generator regression checks include old payload examples.

## Validation and handoff

Run `make check`; it includes generated-output drift and offline schema/example tests. No live backend or gateway is required.

Record acceptance results, exact dependency pins, any manual evidence and open follow-ups.
Commit the final changes, then run `./work board set Q-079 in-review -m "<changes; checks and results; follow-ups>"`
from the workspace root. The human owns integration and any required release.
