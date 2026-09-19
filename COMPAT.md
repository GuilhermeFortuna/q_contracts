# Cross-repository compatibility pins

This is the only cross-repository pin record for Q. A consumer updates its
`CONTRACTS_REV` and regenerated vendored output in the same change, then this
table is updated with the consumer commit and verification evidence.

| Repository | Repository commit | Contracts commit | `q_core` tag pinned |
| --- | --- | --- | --- |
| `q_contracts` | `818b2823d830f90aaea0e84785e36095768f1fb8` | `818b2823d830f90aaea0e84785e36095768f1fb8` | — |
| `q_frontend` | `5774b580e8443598ce57a0460752f4ec83c898be` | `8a9c45299842184d73a82c9c4d6c9fb49dc16885` | — |
| `q_backend` | `25a1a84d7225743fbbeda809342f3e6f1d4a6d65` (Q-044) | `4e874974e64eef48f375acb3aae10c56380ea6e0` | `v2026.09.15.2` |
| `q_core` | `415aa59a419bf9a9c7d6bef67d157ddafd09bc40` (`v2026.09.15.2`) | `998a50570905524bfb9af0465a725b170f2970df` | — |
| `q_terminal` | `e510f504259718b4a2f8acd517da3b99bbee8163` | `998a50570905524bfb9af0465a725b170f2970df` | `v2026.09.12` |

Every commit hash above resolves in its repository; verify with
`git -C <repo> cat-file -t <hash>` before editing a row. An earlier revision of
this table carried a `q_core` hash that resolved nowhere.

### Open drift

Three different contracts revisions are in use: `q_backend` at `4e87497`,
`q_core` and `q_terminal` at `998a5057`, and `q_frontend` at `8a9c452`. Each
repository's `make contracts-check` passes against the revision it pins, so no
repository is internally inconsistent, but no single revision is shared across
the workspace. Closing this means re-vendoring `q_core`, `q_terminal` and
`q_frontend` at `09400d7` and re-verifying each — a change large enough to
belong to its own board task, not a pin-record edit.

The two `q_core` tags in use also differ: `q_terminal` still links
`v2026.09.12` while `q_backend` pins `v2026.09.15.2`.

## Reference fixture pins

Cross-repository reference fixture pins used for numerical parity gating and test provenance. Unlike contract vendoring, these pins represent test oracle provenance rather than a code dependency (`q_core` consumes fixtures exported from `q_backend`).

| Consumer | Reference repository | Reference commit (`BACKEND_REV`) | Purpose |
| --- | --- | --- | --- |
| `q_core` | `q_backend` | `067e29cdf8db67d8b8c237599fced0b8eabb921f` | Technical indicator reference fixtures & parity gate (Q-021) |

## Generation scope decisions

Python generation covers the stream envelope and control frames, edge
payloads, and the dataset manifest. `q_backend` keeps its control API models
hand-written because those Pydantic models are the source of the captured
OpenAPI document; generating them back into the backend would create a
source-generation loop. The generated Python API module is therefore not
vendored into `q_backend`.

C++ is not a generation target. `q_terminal` uses C++ only for custom Qt
scene-graph buffer movement and the generated side of the `cxx-qt` bridge; it
does not decode wire payloads. This decision is revisited if C++ acquires a
payload-handling role.

## Verified by

Every row above was re-verified together on 2026-09-16, each repository at the
commit its row names:

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
