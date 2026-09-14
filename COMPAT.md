# Cross-repository compatibility pins

This is the only cross-repository pin record for Q. A consumer updates its
`CONTRACTS_REV` and regenerated vendored output in the same change, then this
table is updated with the consumer commit and verification evidence.

| Repository | Repository commit | Contracts commit |
| --- | --- | --- |
| `q_contracts` | `09400d7fc16a4b95cae225300ff7834a20f3d1b0` | `09400d7fc16a4b95cae225300ff7834a20f3d1b0` |
| `q_frontend` | `aea7bfe70ec7fae81b6c28d24bd3bb10cdeff7c3` | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_backend` | `8367451d26744fc1e513c3cf5b103eb4aa559220` | `8a9c45299842184d73a82c9c4d6c9fb49dc16885` |
| `q_core` | `84bdeb084920fc41f6e1e69a038bf9087532eb51` (`v2026.09.12`) | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_terminal` | `88aa2730a30b5cecea17ebfc9aafdc3fe3aa6196` | `998a50570905524bfb9af0465a725b170f2970df` |

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

Verified by: `q_contracts` at `09400d7` `make check` — clean generated-output
drift check, Black, Ruff, schema validation, and `131 passed, 7 skipped`; `q_frontend` `make
contracts-check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean,
`pnpm typecheck` — passed, `pnpm lint` — 0 errors and 45 warnings, and `TZ=America/Sao_Paulo
pnpm test:run` — 188 files and 886 tests passed, both before and after the
generated-type adoption with no frontend test file modified; `q_backend` at `development`
`8a1174b8eebf8ea3676683ec7dc8c1c0f7d071f8` (pin commit `1a8d0bc`) `scripts/ci.sh`
— `make contracts-check` against the published repository clean, migrations
applied, Ruff and Black clean, and pytest 1,722 passed, 14 skipped; `q_core` `make check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean rustfmt, clippy, workspace tests, release wheel build, virtualenv wheel integration test, Qt staticlib C++ harness assertions, and contracts-check; `q_terminal` `env -u WAYLAND_DISPLAY -u DISPLAY make check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean rustfmt, clippy, build, qmllint (-W 0), test_bridge, test_headless_report, clean contracts-check, and headless-report reporting app version 0.1.0, core version 2026.9.12, contracts rev 998a50570905524bfb9af0465a725b170f2970df, and headless render backend.

