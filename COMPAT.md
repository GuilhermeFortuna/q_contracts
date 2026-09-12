# Cross-repository compatibility pins

This is the only cross-repository pin record for Q. A consumer updates its
`CONTRACTS_REV` and regenerated vendored output in the same change, then this
table is updated with the consumer commit and verification evidence.

| Repository | Repository commit | Contracts commit |
| --- | --- | --- |
| `q_contracts` | `998a50570905524bfb9af0465a725b170f2970df` | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_frontend` | `aea7bfe70ec7fae81b6c28d24bd3bb10cdeff7c3` | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_backend` | `2841245d5ce67f134cddcc9d18c67cf3ce69d0ad` | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_core` | `84bdeb084920fc41f6e1e69a038bf9087532eb51` (`v2026.09.12`) | `998a50570905524bfb9af0465a725b170f2970df` |
| `q_terminal` | `88aa2730a30b5cecea17ebfc9aafdc3fe3aa6196` (`v2026.09.12`) | `998a50570905524bfb9af0465a725b170f2970df` |

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

Verified by: `q_contracts` `UV_CACHE_DIR=/tmp/q-uv-cache make check` — Black,
Ruff, schema validation, and `93 passed, 7 skipped`; `q_frontend` `make
contracts-check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean,
`pnpm typecheck` — passed, `pnpm lint` — 0 errors and 45 warnings, and `TZ=America/Sao_Paulo
pnpm test:run` — 188 files and 886 tests passed, both before and after the
generated-type adoption with no frontend test file modified; `q_backend` `make
contracts-check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean, and
`UV_CACHE_DIR=/tmp/q-uv-cache uv run pytest` — 1,580 passed, 1 failed, 14
skipped. The one backend failure is the pre-existing
`test_factory_gemini_missing_api_key` configuration assertion; `q_core` `make check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean rustfmt, clippy, workspace tests, release wheel build, virtualenv wheel integration test, Qt staticlib C++ harness assertions, and contracts-check; `q_terminal` `env -u WAYLAND_DISPLAY -u DISPLAY make check CONTRACTS_REPO=/home/gui/projects/q/q_contracts` — clean rustfmt, clippy, build, qmllint (-W 0), test_bridge, test_headless_report, clean contracts-check, and headless-report reporting app version 0.1.0, core version 2026.9.12, contracts rev 998a50570905524bfb9af0465a725b170f2970df, and headless render backend.

