# Cross-repository compatibility pins

This is the only cross-repository pin record for Q. A consumer updates its
`CONTRACTS_REV` and regenerated vendored output in the same change, then this
table is updated with the consumer commit and verification evidence.

| Repository | Repository commit | Contracts commit | `q_core` tag pinned |
| --- | --- | --- | --- |
| `q_contracts` | `bf602c9c7bad907680d3ce98327439efe0f4c5bf` (backtest entry reasons) | `bf602c9c7bad907680d3ce98327439efe0f4c5bf` | — |
| `q_frontend` | `91d1f10` (Q-129 entry reasons, unpushed) | `bf602c9c7bad907680d3ce98327439efe0f4c5bf` | — |
| `q_backend` | `60f5bb3` (Q-129 entry reasons, unpushed) | `bf602c9c7bad907680d3ce98327439efe0f4c5bf` | `v2026.10.20` |
| `q_core` | `d72df0f1e9b97d4d800b4935b224380ff12fe909` (`v2026.10.20`) | `998a50570905524bfb9af0465a725b170f2970df` | — |
| `q_terminal` | `e510f504259718b4a2f8acd517da3b99bbee8163` | `998a50570905524bfb9af0465a725b170f2970df` | `v2026.09.12` |

Every commit hash above resolves in its repository; verify with
`git -C <repo> cat-file -t <hash>` before editing a row. An earlier revision of
this table carried a `q_core` hash that resolved nowhere.

### Open drift

`q_backend` and `q_frontend` pin `bf602c9` (Q-129 entry reasons), while
`q_core` pins `998a5057`. The touched consumers' contract checks pass against
their own pins. Aligning the `q_core` contracts revision remains a separate task.

`q_backend` now adopts `q_core` `v2026.10.20`; `q_terminal` retains its independently
managed core pin and is not changed by this release.

## Reference fixture pins

Cross-repository reference fixture pins used for numerical parity gating and test provenance. Unlike contract vendoring, these pins represent test oracle provenance rather than a code dependency (`q_core` consumes fixtures exported from `q_backend`).

| Consumer | Reference repository | Reference commit (`BACKEND_REV`) | Purpose |
| --- | --- | --- | --- |
| `q_core` | `q_backend` | `067e29cdf8db67d8b8c237599fced0b8eabb921f` | Technical indicator reference fixtures & parity gate (Q-021) |

## Generation scope decisions

Python generation covers the stream envelope and control frames, edge
payloads, the lake dataset manifest, and the ML entry-filter dataset/model
manifest (`schema/catalog/ml-entry-filter-manifest.schema.json`). `q_backend`
keeps its control API models hand-written because those Pydantic models are the
source of the captured OpenAPI document; generating them back into the backend
would create a source-generation loop. The generated Python API module is
therefore not vendored into `q_backend`.

C++ is not a generation target. `q_terminal` uses C++ only for custom Qt
scene-graph buffer movement and the generated side of the `cxx-qt` bridge; it
does not decode wire payloads. This decision is revisited if C++ acquires a
payload-handling role.

## Verified by

The September baseline was verified together on 2026-09-16 at the commits
listed below. Later consumer adoptions are recorded in the dated sections:

- `q_contracts` at `818b282` — `make check`: clean generated-output drift check,
  Black, Ruff, schema validation, `131 passed, 7 skipped`.
- `q_backend` at `281b739` — `scripts/ci.sh`: `make contracts-check` against the
  published repository clean, migrations applied, Ruff and Black clean, pytest
  `1930 passed, 14 skipped` plus `55 passed` serial integration tests.
- `q_frontend` at `5774b58` — `TZ=America/Sao_Paulo scripts/ci.sh`:
  `make contracts-check` clean, cross-repo path check, `pnpm typecheck`, `pnpm
  lint`, `pnpm format:check`, `pnpm test:run` 200 files and 944 tests passed,
  `vite build` passed, and the Tauri shell stage clean (`cargo clippy
  -D warnings`, `cargo test` including the process-ownership guard).
- `q_core` at `415aa59` (`v2026.09.15.2`) — `make check`: clean rustfmt, clippy,
  workspace tests, fixture staleness check, parity isolation, release wheel
  build (`q_core-2026.9.15`, contracts rev `998a5057`), virtualenv wheel
  integration tests for bar frames, candle engine and tick engine, Qt staticlib
  C++ harness, and contracts-check.
- `q_terminal` at `e510f50` — `env -u WAYLAND_DISPLAY -u DISPLAY make check
  CONTRACTS_REPO=/home/gui/projects/q/q_contracts`: clean rustfmt, clippy,
  build, qmllint (-W 0), `test_bridge`, `test_headless_report`, clean
  contracts-check, and headless-report reporting app version 0.1.0, core
  version 2026.9.12, contracts rev `998a5057`, headless render backend.

## Q-079 trade contracts handoff

Q-079 adds the UTC trade Arrow schema, ordered `trades` stream policy, separate
latest source status, and immutable session snapshot/history interfaces. The
implementation branch is not a consumer pin. Q-080/Q-081 consumers must update
`CONTRACTS_REV` to the merged `q_contracts` commit and regenerate their vendored
bindings as part of their own reviewed changes; do not pin this unpublished
branch revision.

## Q-092 bar completeness handoff

Q-092 adds bar completeness metadata (`truncated`, `max_bars`) and continuation
rules to `/v1/ohlcv` in the descriptive data gateway contract. The change is
additive and YAML-only with no generated output changes. Q-093 updates
`q_backend`'s `CONTRACTS_REV` to the merged `q_contracts` commit; no consumer
regeneration is needed. Do not pin this unpublished branch revision.

## Q-097 imported backtest runs handoff

Q-097 adds `POST /api/v1/backtests/import`, `BacktestProvenance`, and `origin`
(`stack` or `script`) on backtest run list and detail responses plus an optional
`origin` filter on `GET /api/v1/backtests`. The change is additive; TypeScript
and Rust API bindings are regenerated. Q-099 and Q-101 must pin the merged
`q_contracts` commit pushed to the remote and regenerate vendored bindings as
part of their own reviewed changes. Do not pin this unpublished branch revision.

## 2026-10-08 review fixes

Generated Python and Rust object fields now preserve declared scalar defaults.
In particular, omitting a run's `origin` yields `stack`; explicit values remain
unchanged. Rust keeps the existing optional field types and uses Serde defaults
for omitted fields. TypeScript interfaces remain optional and callers interpret
an absent origin as `stack`. Regenerate consumer output when adopting this
revision; no wire fields or enum values changed.

The gateway bar contract also documents that an unfinished bounded history scan
returns the existing HTTP 500 `internal_error` shape rather than incomplete
success. No new error code or generated payload is required for that correction.

## 2026-10-08 research position context release

- `q_core` tag `v2026.10.08.2` resolves to
  `7e189227a51e7b3df50762148df79abdda0bd21e`. `make check` passed: formatting,
  workspace Clippy and tests, reference fixture verification, parity isolation,
  Python wheel integration tests, Qt C++ harness, and vendored contract verification.
  The normal pre-push CI also passed before publishing the commit and tag.
- `q_backend` at `f1ab2dee44cebf8d4d29563186f4503127333eb3` pins this published
  tag and exact core commit in `pyproject.toml` and `uv.lock`. `uv sync` installed
  the release; inspection confirmed the candle `strategy_callback` API and the
  public `ResearchPosition` export. The research suite and focused engine, bridge,
  signal, and registry baseline tests passed (`229 passed`, two existing Pydantic
  deprecation warnings) against the published dependency.
  Publication then passed the normal full pre-push CI: vendored contracts,
  migrations, Ruff, Black, `2499 passed, 15 skipped` unit tests, and
  `56 passed` integration tests against disposable PostgreSQL and Redis services.
- This adoption adds optional actual-position context to research strategy hooks.
  It changes no wire contracts, generated schemas, or fixture provenance pins.
  The package version is `2026.10.8`; the release tag distinguishes this second
  release of the day from `v2026.10.08`.
- The compatibility record passed `q_contracts`' canonical `make check`:
  generated-output verification, Black, Ruff, schema validation, and
  `245 passed, 7 skipped, 1 deselected`.

## Q-104 intermediate core release (2026-10-08)

`q_core` `v2026.10.08.3` resolves to
`095c2ce507278dcb814b620db1087fa5b77393a9`. It adds lazy custom screen/tick exit
callbacks and runtime entry-level transport, preserving legacy callbacks.
Fresh `make check` passed, covering Rust tests, fixtures, parity isolation,
Python wheel integration, the Qt harness and contracts drift. Publication's
pre-push CI also passed. Backend adoption and its verification are still in
progress under Q-104; update the backend row when its consumer commit is verified.

## Q-104 backend adoption (2026-10-08)

- `q_backend` at `7d8212dcda9db1d039a3bbe3f8c021f306bb55eb` pins `q-core` to the
  published tag `v2026.10.08.3`, which resolves to
  `095c2ce507278dcb814b620db1087fa5b77393a9`. `uv.lock` records the same commit.
  The package version is `2026.10.8` and the contracts revision is `998a5057`.
- The adoption adds entry stop and take-profit levels, confirmed from a
  `TickStore`, and phase-aware exit screening and tick replay to research
  backtests. It changes no wire contracts, generated schemas, or fixture pins.
  Job and publish payloads are unchanged because the new trade fields are not
  serialised.
- Verification on the consumer commit: the research, backtesting and execution
  suites passed (`1058 passed, 11 skipped`); the API payload and backtest tests
  passed (`93 passed`); ruff and black passed on changed paths. Seven integration
  tests that need Postgres and Redis were not run in this environment. The
  pre-push CI that runs them has not been run for this commit.
- Known limitation, a follow-up in `q_core`: a wrong-side entry is reported in
  `rejected_entries` even when the position cap would also skip it.

## q_core v2026.10.12 release and q_backend adoption (2026-10-12)

- `q_core` tag `v2026.10.12` resolves to
  `9872b41645ee32125190fb959104ff31b98494e5`. It is the second release after
  `v2026.10.10` and carries the intrabar breakeven emergency stops
  (`engine.BREAKEVEN_INTRABAR`). `make check` passed on the release commit with
  zero failing checks: formatting, workspace Clippy and tests, fixtures, parity
  isolation, Python wheel tests, Qt harness, and contracts drift. The build logs
  still show environment-only warnings (hardlink fallback on the cache volume and
  a gold-linker deprecation notice for the `q-qt` test binary); no code warnings.
  Contracts revision `998a5057` is unchanged.
- `q_backend` at `b97f83af2e47e1c17629c85e6989411457c86b52` pins `q-core` to
  `v2026.10.12` in `pyproject.toml` and `uv.lock`, resolving to
  `9872b41645ee32125190fb959104ff31b98494e5`. `uv sync` installed
  `q-core==2026.10.12`, and `engine.BREAKEVEN_INTRABAR` is present. Focused
  verification: `tests/backtesting`, `tests/execution/test_evaluator_q_core.py`
  and `tests/test_no_cross_repo_paths.py` passed (`727 passed, 11 skipped`).
  The full pre-push CI for this commit has not been run.
- The `q_core` commit and tag are pushed to origin. The `q_backend` pin commit
  is local only, and `q_backend` `development` also carries the unpushed
  `0b402df` breakeven change, which needs this pin.

## q_core v2026.10.12.3 release and q_backend adoption (2026-10-12)

- `q_core` tag `v2026.10.12.3` resolves to
  `70df284e46f6a827ab4522d6874c3c7d7ac7d3e4`. It is the third release of the day
  and follows `v2026.10.12.2` (the Q-111 research indicator kernels, resolving to
  `5f4c9b8739181d123e642ac862972eec8e377970`). It corrects `quote_spread_bars`,
  which counted a quote for time before its bar's open, and rejects an
  exponentially weighted half-life above `5e8`, whose readiness count used to
  wrap. `make check` passed on the release commit. Contracts revision `998a5057`
  is unchanged.
- `q_backend` at `490786a` pins `q-core` to `v2026.10.12.3` in `pyproject.toml`
  and `uv.lock`, resolving to the commit above. Focused verification on the
  released wheel: `tests/market_data/test_indicator_catalog.py`,
  `tests/market_data/test_quote_spread.py`, `tests/api/test_market_indicators.py`,
  `tests/features` and `tests/backtesting/test_q111_wrappers.py` passed
  (`268 passed`). The full pre-push CI for this commit has not been run.
- The `q_core` commit and tag are pushed to origin. The `q_backend` pin and the
  series and quote-feature corrections that need it are merged into `development`
  locally (`b840b8a`) and are not pushed.

## Volume-at-price review release and adoption (2026-10-16)

- `q_core` tag `v2026.10.16` resolves to
  `66d2acb157fe7a10950d7a765b2df66488ccf1ea`. It includes the Q-116 review
  fixes for source-order volume sums, full-range value area at a share of one,
  representable tick indices, overflow-safe POC ties, and checkpoint suffix
  causality. Package version: `2026.10.16`; contracts revision: `998a5057`.
- The full canonical `make check` passed: 403 Rust tests, reference-exporter
  tests and fixture regeneration, parity isolation, Python wheel projection and
  engine checks, Qt harness, formatting, Clippy, and contracts drift checks.
  The normal pre-push CI also passed. The release commit and annotated tag are
  published to origin.
- `q_backend` at `c40dbb5ced2b4d66e94d0171d325108410936c40` pins the published
  tag in `pyproject.toml` and `uv.lock`, resolving to the release commit above.
  `uv sync --frozen` installed `q-core==2026.10.16`. Focused tests in
  `tests/research/test_volume_at_price.py`, `tests/api/test_market_volume_profile.py`,
  `tests/api/test_market_indicators.py`, and `tests/market_data/test_indicator_catalog.py`
  passed (`106 passed`). Ruff and Black passed in the normal commit hook.
- `q_frontend` at `9c8a9147aea16552b5334c161cfca2bfc8d836af` includes the
  Q-117 request-boundary, session-placement, and hover fixes. The merged tree
  passed 39 focused chart, saved-profile, and market utility tests. Chromium
  verified profile hover and desktop/narrow rendering before integration.
- Backend and frontend `make contracts-check` passed against their pinned
  `25bae5a` revision using the documented local contracts checkout option.
  Their `development` changes are committed locally and have not been pushed.

## Tick-backed backtest review release and adoption (2026-10-20)

- `q_core` tag `v2026.10.20` resolves to
  `d72df0f1e9b97d4d800b4935b224380ff12fe909`. It preserves every observed price
  during a screened scan across a protective exit and subsequent resting entry,
  and rejects stop/target amendments without an intrabar source and OHLC inputs.
  Package version: `2026.10.20`; contracts revision: `998a5057`.
- The full canonical `make check` and normal pre-push CI passed, including
  reference fixtures, workspace tests, Python wheel checks, the Qt harness,
  formatting, Clippy, and contracts checks. The release tag is published to origin.
- `q_backend` at `3fb55723ca7df8a584e30d6e78e11ff11885c46d` pins the published
  tag in `pyproject.toml` and `uv.lock`, resolving to the core commit above.
  It attributes original trade levels to accepted entry decisions, preserves
  forming-candle observations while flat without invoking user exit hooks,
  and transports native tick-data failures across session workers with global
  bar indices. No wire contract changed.
- `uv sync --frozen` installed the release from its Git tag. Canonical backend
  CI and the normal pre-push hook passed: contracts checks, migrations against
  disposable Postgres/Redis, Ruff, Black, `3267 passed, 15 skipped` unit tests and `56 passed` serial
  integration tests. The native engine regression suite passed all 176 tests.
- The push hook clears repository-local Git context before launching CI, so
  foreign contracts checkouts work from linked worktrees as well as primary
  checkouts. Two focused Git fixtures cover those cases. The core release and
  backend adoption are published on their respective `development` branches.

## Backtest entry reasons (Q-129, 2026-10-25)

- `q_contracts` at `bf602c9c7bad907680d3ce98327439efe0f4c5bf` renames
  `ExitReasonStats` to `ReasonStats` and adds the required `entry_reasons`
  array to `BacktestPerformance`. The rename breaks the Q-123 performance
  schema for any consumer still on an older revision, so each consumer moves to
  this revision in the same change. `make check` passed: `309 passed, 7 skipped`.
- `q_backend` at `60f5bb3` pins `bf602c9` and passes `make contracts-check`
  against that revision from a local clone, because the commit is unpushed.
  Focused research, backtesting, analytics, performance and payload-guard tests
  pass, and Ruff and Black are clean. Six optimization and API tests need the
  dev Postgres on `localhost:5434`, which is not running in this workspace.
- `q_frontend` at `91d1f10` pins `bf602c9` and passes `make contracts-check`
  from a local clone, `pnpm typecheck`, and `pnpm lint` with no errors. The full
  Vitest suite passed under `TZ=America/Sao_Paulo`: `271` files and `1406` tests.
- Both consumer commits are local. Nothing has been pushed.


## Strategy files (Q-134, 2026-10-29)

- `q_contracts` at `2e9f5201a667fe7cbc72a4f67e0d57b751192ab6` adds the
  strategy file list and strategy version routes, the `bool` and `time`
  parameter types, and the `strategy_file`, `strategy_version_id` and bundle
  hash fields on backtest requests and runs. The change is additive; generated
  TypeScript and Rust outputs are regenerated. `make check` passed:
  `310 passed, 7 skipped`.
- `q_backend` at `87c5639` pins `2e9f520` and passes `make contracts-check`
  from a local clone, because the commit is unpushed. The API and worker tests
  for strategy files, the backtest, import, storage and research suites pass
  (`1722 passed, 11 skipped`). Seven optimization and stream tests need the dev
  Postgres on `localhost:5434`, which is not running in this workspace.
- `q_frontend` at `307f394` pins `2e9f520` and passes `make contracts-check`
  from a local clone, `pnpm typecheck`, and `pnpm lint` with no errors. The full
  Vitest suite passed under `TZ=America/Sao_Paulo`: `275` files and `1436` tests.
- Both consumer commits are local. Nothing has been pushed.

## MT5 demo-account gate (Q-135, 2026-10-29)

- `q_contracts` at `379fb21` adds the required `trade_mode` (`demo`, `contest`
  or `real`) to the execution-edge account response, and `cb651e0` adds
  `mt5_orders` (capability, reason and account) to the execution health
  response. `fce35bb` aligns the OpenAPI account reference with the backend
  schema. The execution-edge contract moves to version `1.1`; its schema major
  stays `1`. The data gateway contract is unchanged at `1.0`.
- `q_backend` at `74b2825` pins `fce35bb` and passes `make contracts-check`
  against the local clone, because the commits are unpushed. The gateway,
  execution, and execution API suites pass (`275 passed, 1 skipped`), and Ruff
  and Black are clean for the changed files.
- `q_contracts` `make check` passed at `fce35bb`: `310 passed, 7 skipped`. Run
  with `Q_BACKEND_PATH` set to the `q_backend` worktree, the gateway capture
  tests pass (`6 passed`).
- Both repositories' task commits are local. Nothing has been pushed.

## Deploy research strategy versions (Q-136, 2026-10-29)

- `q_contracts` adds `order_kinds` to the backtest run detail and list schemas,
  the `strategy_version` source kind and its provenance (`strategy_version_id`,
  `strategy_bundle_hash`) to deployment summary and detail schemas, and the
  `day_trade_session` to deployment detail and backtest run schemas.


## Stop, limit and protective orders on MT5 (Q-137, 2026-10-29)

- The execution-edge contract moves to version `1.2` (schema major `1`), an
  additive minor change. `submit-request` gains an `action` (`deal` by default,
  `pending`, `sltp`, `remove`) with per-action required fields, and `order` gains
  `expiration`. `deal` gains `position_id` and `reason`. `GET /v1/orders` lists
  working pending orders (`working-order`). `lookup-request` gains `kind`
  (`deal` by default); `kind: pending` answers `pending-lookup-outcome`, which
  adds `placed`, `cancelled` and `expired` to the existing filled, rejected,
  not-found and unavailable outcomes. `lookup-outcome` keeps its four members.
- The stream `execution-common` enums gain order types `stop` and `limit`, and
  statuses `working` and `expired`.
- The backend refuses pending and protective intents when the edge advertises
  a `schema_version` below `1.2`.
- Generated Python, Rust and TypeScript output is regenerated. The Rust emitter
  writes `pub` on enum struct-variant fields and boolean `const` values as
  `String`; this already applies to the existing outcome enums and is recorded
  as a follow-up, not changed here.
