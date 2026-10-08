# Cross-repository compatibility pins

This is the only cross-repository pin record for Q. A consumer updates its
`CONTRACTS_REV` and regenerated vendored output in the same change, then this
table is updated with the consumer commit and verification evidence.

| Repository | Repository commit | Contracts commit | `q_core` tag pinned |
| --- | --- | --- | --- |
| `q_contracts` | `818b2823d830f90aaea0e84785e36095768f1fb8` | `818b2823d830f90aaea0e84785e36095768f1fb8` | — |
| `q_frontend` | `5774b580e8443598ce57a0460752f4ec83c898be` | `8a9c45299842184d73a82c9c4d6c9fb49dc16885` | — |
| `q_backend` | `f1ab2dee44cebf8d4d29563186f4503127333eb3` (research position context release) | `e06a3c9f7f79517b47bea826ecef8f3527655a73` | `v2026.10.08.2` |
| `q_core` | `7e189227a51e7b3df50762148df79abdda0bd21e` (`v2026.10.08.2`) | `998a50570905524bfb9af0465a725b170f2970df` | — |
| `q_terminal` | `e510f504259718b4a2f8acd517da3b99bbee8163` | `998a50570905524bfb9af0465a725b170f2970df` | `v2026.09.12` |

Every commit hash above resolves in its repository; verify with
`git -C <repo> cat-file -t <hash>` before editing a row. An earlier revision of
this table carried a `q_core` hash that resolved nowhere.

### Open drift

Three different contracts revisions are in use: `q_backend` at `e06a3c9`,
`q_core` and `q_terminal` at `998a5057`, and `q_frontend` at `8a9c452`. Each
repository's `make contracts-check` passes against the revision it pins, so no
repository is internally inconsistent, but no single revision is shared across
the workspace. Aligning revisions requires coordinated re-vendoring and
verification as a separate task.

The two `q_core` tags in use also differ: `q_terminal` still links
`v2026.09.12` while `q_backend` pins `v2026.10.08.2`.

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
