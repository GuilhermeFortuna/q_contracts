# Q-001 implementation plan: `q_contracts` repository skeleton

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-001-q-contracts-repository-skeleton-spec.md`](../specs/Q-001-q-contracts-repository-skeleton-spec.md)  
**Depends on:** None

## Current-system context

There is no `q_contracts` repository. `/home/gui/projects/q` is a plain directory
holding two independent git repositories, `q_backend` and `q_frontend`, plus
`docs/`. `q_backend` is Python 3.12 managed with `uv` (`pyproject.toml`
`[project] requires-python = ">=3.12"`, `[tool.uv.sources]` for the MT5 stub),
formatted with `black`, linted with a deliberately minimal `ruff` selection
(`BLE001`, `S110` only), tested with `uv run pytest`, and task-run through
`mise.toml`. `q_frontend` is TypeScript with `pnpm`, `eslint`, `prettier`, and
`vitest`. The two conventions differ and neither is automatically right for a
schema repository.

What already exists and is unused for this purpose: `q_backend/gateway/mt5_gateway.py`
carries the only written wire contract in the system, in its module docstring at
lines 16–58, complete with `SCHEMA_VERSION = "1.0"` (line 94) and the
`/v1/` path table; `q_backend/src/q_backend/api/schemas/` holds fourteen Pydantic
modules that already describe most of the control surface; `q_frontend/src/types/`
holds twelve hand-written mirrors of those. None of these can be read by a repository
that does not exist. The gap this task closes is the absence of a place to put
them — the directory layout, the validity rules, and the one command that enforces
both.

## Interfaces produced

This task adds no runtime surface. It adds a repository layout and one executable
check. The layout is the interface, so it is specified here.

```
// q_contracts/  (new repository, sibling of q_backend and q_frontend)
schema/                  hand-authored, the source of truth; no consumer reads this
  api/README.md          the control API boundary        (populated by Q-003)
  stream/README.md       the event stream boundary       (populated by Q-002)
  edge/README.md         the Wine edge boundary          (populated by Q-004)
  catalog/README.md      the dataset catalog boundary    (populated by Q-005)
generated/               generated output; empty in this task (populated by Q-006)
  .gitkeep
tools/
  validate.py            the whole check; walks schema/ and exits non-zero on any failure
tests/
  test_validate.py       unit tests for the check's own rules
VERSIONING.md            additive-by-default, schema-major, commit-hash pinning
README.md                what this repository is, and how to add a schema
pyproject.toml           toolchain declaration
.python-version          exact interpreter pin
Makefile                 `make check` — the one command
.github/workflows/ci.yml runs `make check`
```

```python
# tools/validate.py

BOUNDARIES: tuple[str, ...]  # ("api", "stream", "edge", "catalog")
SUPPORTED_DIALECTS: frozenset[str]  # JSON Schema 2020-12 only, for now

class SchemaProblem(NamedTuple):
    path: Path      # repo-relative path of the offending file
    reason: str     # single-line explanation, names the file's actual defect

def discover(schema_root: Path) -> list[Path]:
    """Every *.schema.json and *.yaml under schema/, sorted; no registry consulted."""

def check_file(path: Path, schema_root: Path) -> list[SchemaProblem]:
    """Parse, dialect check, and boundary-placement check for one file."""

def check_tree(schema_root: Path) -> list[SchemaProblem]:
    """discover() then check_file() over everything. Empty tree yields no problems."""

def main(argv: Sequence[str] | None = None) -> int:
    """Prints one line per problem, returns 0 when there are none."""
```

## Implementation decisions

- **The repository is Python with `uv`, matching `q_backend` rather than
  `q_frontend`.** The generator in Q-006 must emit three languages, and a
  generator written in one of the three target languages acquires an opinion
  about that language's output. Python is also the toolchain the developer
  already runs for the backend, so there is no fourth package manager to keep
  alive. The cost is that `q_frontend` developers touch a Python repository to
  change a schema; that is accepted because they change schemas rarely and
  regenerate rather than hand-edit.

- **Discovery walks the tree; there is no manifest of schema files.** A manifest
  is a second place the truth lives, and the failure it produces is the worst
  kind: a schema that exists, is wrong, and is never checked because someone
  forgot a line. Walking means the only way to escape the check is to delete the
  file.

- **A schema's identifier is derived from its path, not read from inside it.**
  If `$id` were authoritative, two files could claim one identifier and the
  conflict would surface as a confusing generation error in Q-006 rather than as
  a placement error here. `check_file` therefore verifies that any declared `$id`
  agrees with the path and reports a problem when it does not.

- **`schema/` is hand-authored and `generated/` is generated, and the separation
  is by top-level directory rather than by filename suffix.** Consumers in Q-006
  copy a whole directory; a suffix convention would require them to filter, and a
  filter is a rule that can be got wrong at the far end of a vendoring script.

- **Only JSON Schema 2020-12 is accepted as a dialect in this task, even though
  the tree will later hold an OpenAPI document and a YAML topic policy.** Those
  two files are validated by their own rules in Q-003 and Q-002 respectively;
  admitting their dialects now would mean writing validation for documents that
  do not exist. `SUPPORTED_DIALECTS` is the extension point, and an unsupported
  dialect fails loudly with the dialect named so the next author knows exactly
  which set to extend.

- **The check passes on an empty tree.** The alternative — requiring at least one
  schema — would force Q-001 to ship a schema, which is exactly what the spec
  rules out. An empty repository that validates is the correct initial state.

- **Boundary directories carry a `README.md` rather than a dotfile.** The
  directory must survive a git commit while empty, and the thing that makes it
  survive should also be the thing that tells the next author what goes in it.
  `.gitkeep` would satisfy git and teach nobody.

- **`make check` runs format, lint, and the schema check in that order.** Order
  matters for the author's feedback loop: formatting failures are mechanical and
  fixing them first avoids re-reading lint output that formatting would have
  changed anyway.

- **The interpreter is pinned by `.python-version` to the same 3.12 series
  `q_backend` requires.** Q-006 will generate Python types that `q_backend`
  imports; generating them under a different interpreter than the consumer runs
  invites a syntax feature the consumer cannot parse.

- **CI is a single job running `make check` and nothing else.** A CI file that
  runs a different sequence than the developer is a CI file that goes green on a
  machine nobody has.

## Ordered implementation

1. Create the branch `Q-001-q-contracts-repository-skeleton-spec` in a newly
   initialized `q_contracts` repository at `/home/gui/projects/q/q_contracts`
   (`git init`, initial empty commit on `main`, then branch).
2. Add `pyproject.toml`, `.python-version`, `.gitignore`, and a `uv.lock`
   produced by `uv sync`. Declare `black`, `ruff`, `pytest`, and a JSON Schema
   validator as dev dependencies; declare no runtime dependencies. Confirm
   `uv run python -c "print(1)"` succeeds. Commit.
3. Create `schema/{api,stream,edge,catalog}/README.md`, each stating what belongs
   in that directory and naming the task that populates it; create
   `generated/.gitkeep`. Commit.
4. Write failing unit tests in `tests/test_validate.py` for `discover`: over a
   temporary tree containing `schema/stream/a.schema.json`,
   `schema/edge/b.schema.json`, and `schema/api/README.md`, it returns exactly the
   two schema files in sorted order and does not return the README; over an empty
   `schema/` it returns an empty list. Run them and confirm they fail because
   `tools/validate.py` does not exist.
5. Implement `discover`. Confirm the tests pass. Commit.
6. Write failing unit tests for `check_file`: a file containing `{` yields one
   `SchemaProblem` whose `path` is that file and whose `reason` mentions parse
   failure; a file declaring `"$schema": "http://json-schema.org/draft-07/schema#"`
   yields one problem whose `reason` contains the string `draft-07`; a file
   declaring `"$id": "stream/other"` while living at `schema/stream/envelope.schema.json`
   yields one problem mentioning the mismatch; a valid 2020-12 file with a matching
   `$id` yields no problems. Run them and confirm they fail.
7. Implement `check_file` and `SUPPORTED_DIALECTS`. Confirm the tests pass. Commit.
8. Write a failing test for `check_tree` and `main`: `check_tree` over an empty
   `schema/` returns no problems, and `main` returns 0; `check_tree` over a tree
   with one malformed file returns exactly one problem and `main` returns 1 and
   prints a line containing the file's repo-relative path. Run them and confirm
   they fail. Implement. Confirm they pass. Commit.
9. Add the `Makefile` with a `check` target running `uv run black --check .`,
   `uv run ruff check .`, `uv run python tools/validate.py`, and `uv run pytest`.
   Run `make check` and confirm it exits zero. Commit.
10. Write `VERSIONING.md` stating the additive-by-default rule, what forces a
    schema-major bump, that both majors are served for one release cycle, and that
    consumers pin by commit hash with no registry and no semver. Write `README.md`
    covering what the repository is, the directory layout, how to add a schema, and
    the single validation command. Confirm `make check` still exits zero. Commit.
11. Add `.github/workflows/ci.yml` running `make check` on push and pull request,
    installing `uv` and syncing from the lockfile. Commit.
12. Verify criterion 4 by hand: create `schema/stream/broken.schema.json`
    containing `{`, run `make check`, confirm a non-zero exit and that the output
    names the file; delete it and confirm `make check` exits zero again. Do not
    commit the broken file.
13. Human step, matching human-verifiable criterion 1: push the branch, confirm the
    CI run is green, and confirm by reading the workflow that it invokes the same
    `make check` a developer runs and no other sequence.
14. Human step, matching human-verifiable criterion 2: give `README.md` to a reader
    who has not seen the repository and confirm they can place a new schema in the
    correct directory without asking a question; record any question they did ask
    and close it in the README.
15. Run the full validation suite (`make check`) and confirm a clean exit. Commit
    any residual formatting. Report the handoff.

## Validation

- **Unit:** `discover` over a mixed tree and an empty tree; `check_file` against a
  parse failure, an unsupported dialect, an `$id`/path mismatch, and a valid file;
  `check_tree` and `main` exit codes on an empty tree and on a tree with one
  malformed file.
- **Integration:** `make check` is the composed command and is what CI runs; the
  malformed-file round trip in step 12 exercises it end to end.
- **Regression:** none. Nothing exists yet to regress against; the baseline this
  task locks is the commit hash of `q_contracts` `main` after merge, which Q-006
  will record in `COMPAT.md`.
- **Manual:** the CI run is green on a pushed branch; the README is sufficient for
  a first-time author.

```bash
cd /home/gui/projects/q/q_contracts
uv sync
make check
# criterion 4, the malformed-file round trip
printf '{' > schema/stream/broken.schema.json
make check; echo "expected non-zero, got $?"
rm schema/stream/broken.schema.json
make check; echo "expected zero, got $?"
```

## Handoff

Report the absolute path of the new repository and the commit hash of its merged
`main`, since that hash is the first entry Q-006 records in `COMPAT.md`. Report
the exact pinned interpreter version and the pinned versions of `black`, `ruff`,
`pytest`, and the JSON Schema validator, because Q-006 generates under this
toolchain and a later mismatch is the likeliest source of non-deterministic
output. Report the wall-clock time of a `make check` run on the empty tree — the
spec requires it to be cheap enough to run on every save, and a number is the
only way to know whether it is. Report the exact stderr line produced by the
malformed-file round trip, confirming it names the repo-relative path. Confirm
that no file in the repository contains the strings `q_backend`, `q_frontend`, or
`..` as a path component, and state how that was checked.
