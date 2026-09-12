# Q-006 implementation plan: Contract code generation and consumer vendoring

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-006-contract-codegen-and-vendoring-spec.md`](../specs/Q-006-contract-codegen-and-vendoring-spec.md)  
**Depends on:** Q-002, Q-003, Q-004, Q-005

## Current-system context

After Q-002 through Q-005, `q_contracts/schema/` holds four populated subtrees:
`stream/` (the envelope, five control frames, `topics.yaml`), `api/`
(`openapi.yaml` captured from the running backend, `error.schema.json`, and the
Arrow declarations `arrow/bars.schema.json` and `arrow/ticks.schema.json`),
`edge/` (`data-gateway.yaml` at schema major 1, `execution.yaml`, and the
per-operation schemas), and `catalog/` (`dataset-manifest.schema.json`,
`lifecycle.yaml`). `tools/validate.py` walks the tree and runs four cross-document
consistency checks; `generated/` contains only `.gitkeep`; `make check` is the
single validation command. Three dialects are present: JSON Schema 2020-12,
OpenAPI 3.1, and hand-shaped YAML policy files.

On the consumer side nothing has changed. `q_frontend/src/types/` still holds
twelve hand-written mirrors — `api.ts`, `backtesting.ts`, `execution.ts`,
`optimization.ts`, `storage.ts`, `strategies.ts` and the rest — consumed through
`src/api/client.ts` and `src/api/queries/`, with `src/api/schemas/` beside them.
`q_backend`'s Pydantic models in `src/q_backend/api/schemas/` remain the runtime
source of the captured OpenAPI document, which makes the generation direction for
Python subtler than for the other languages. Neither repository has a `Makefile`
or any notion of a contracts pin; `q_frontend`'s scripts are `pnpm` tasks in
`package.json` and `q_backend`'s are `mise` tasks plus `uv run`. The gap this task
closes is that nothing in either repository reads `q_contracts` at all.

## Interfaces produced

```
// q_contracts/
tools/generate.py            the generation command; one entry point, three emitters
tools/emitters/python.py
tools/emitters/typescript.py
tools/emitters/rust.py
generated/python/q_contracts/    importable package
generated/typescript/            .ts modules, one per schema group
generated/rust/                  a crate source tree, no Cargo.toml of its own
COMPAT.md                        known-good pins across every repository
```

```python
# q_contracts/tools/generate.py
LANGUAGES: tuple[str, ...]            # ("python", "typescript", "rust")
HEADER: str                           # the generated-file marker template

class GenerationError(Exception):
    """Raised with the schema path and the target language named."""

def plan_units(schema_root: Path) -> list[GenerationUnit]:
    """Group schema files into the units each emitter produces one file from."""

def generate(schema_root: Path, out_root: Path, languages: Sequence[str]) -> list[Path]:
    """Emit every unit for every language. Returns the written paths, sorted."""

def main(argv: Sequence[str] | None = None) -> int: ...
```

```
// consumer side, identical shape in every consumer repository
contracts/            the vendored generated code for that repository's language
CONTRACTS_REV         a single line: the q_contracts commit hash
Makefile              `make contracts`   regenerate from CONTRACTS_REV
                      `make contracts-check`  regenerate into a temp dir and diff
```

## Implementation decisions

- **One generator process with three emitters, rather than three off-the-shelf
  tools wired together.** Three tools means three version pins, three sets of
  configuration, and three different ideas of how to name a field — and the
  determinism requirement then depends on all three being deterministic, which
  none of them promises. A single emitter per language, written against the small
  set of shapes this repository actually contains, is more code to own and is the
  only way the byte-identical requirement is achievable.

- **Determinism is achieved by sorting every collection and writing no
  timestamps, no hostnames, and no tool versions into the output.** The standard
  failure is a generator that stamps the generation time into a header; the output
  then differs on every run, the drift check becomes noise, and within a month
  somebody disables it. The header names the source schema and nothing that
  varies.

- **The generated-file marker is the first line of every file and includes the
  source schema's repository-relative path.** A reader who opens a generated type
  to fix a field name needs to be told, in the place they are looking, which file
  to fix instead. A marker at the bottom, or a marker naming only "the generator",
  fails that reader.

- **Python types are generated even though `q_backend`'s Pydantic models are what
  produced the OpenAPI document.** The circularity is real and is resolved by
  scope: the generated Python covers the payloads `q_backend` does *not* already
  own — the stream envelope and control frames, the edge contracts, and the dataset
  manifest — while the control API models stay hand-written in `q_backend` and
  remain the captured document's source. Generating API models back into
  `q_backend` would create a loop in which the models generate the document and the
  document generates the models, and the first divergence would be unresolvable.
  This split is recorded in `COMPAT.md` because it is the least obvious rule here.

- **C++ is not generated, narrowing §7 of the architecture.** §5 confines C++ to
  custom scene-graph render nodes, which move buffers and never decode a payload;
  the terminal's typed access is Rust over `cxx-qt`. Generating an unused C++
  surface would produce headers nothing compiles, and a generated artifact nothing
  compiles is wrong without anyone learning. This removes C++ from the *emitter*
  list only — `q_terminal` still contains hand-written C++ under `cpp/` (Q-008),
  and no repository is added or removed by this decision. The reason is recorded
  in `COMPAT.md` and the decision is revisited if C++ acquires a payload role.

- **The Rust output is a source tree without its own `Cargo.toml`.** `q_core` will
  include it as a module inside an existing crate (Q-007), and a vendored crate
  with its own manifest would have to be added as a path dependency, which puts a
  sibling path into `q_core`'s manifest — exactly the cross-repo path coupling §7.1
  removes. A source tree is included; a crate is depended on.

- **`CONTRACTS_REV` holds a commit hash and nothing else — no tag, no branch, no
  version.** A branch name is not a pin; a tag can be moved. The file being a
  single line with a single hash also makes the update diff unambiguous in review,
  which is the whole reason the pin is a file rather than a lockfile entry.

- **`make contracts` fetches the pinned commit into a temporary checkout rather
  than reading a sibling directory.** Reading `../../q_contracts` would make a
  consumer's build depend on the developer's directory layout and would silently
  regenerate from whatever is checked out there — including uncommitted edits. The
  temporary checkout means the pin is what is generated from, always.

- **`make contracts-check` regenerates into a temporary directory and diffs,
  rather than regenerating in place and checking `git status`.** Regenerating in
  place in CI leaves the working tree dirty and, worse, leaves it dirty on a
  developer's machine when they run the check locally, which then looks like an
  unrelated change. Temp-dir-and-diff is read-only.

- **The adopted payload is `q_frontend`'s job progress shape, replacing the
  corresponding hand-written type.** It is the smallest mirror, it is covered by
  existing tests, and it is the payload the stream work in the next batch touches
  first, so the adoption is immediately load-bearing rather than ceremonial. A
  larger mirror would make the runtime-behavior-unchanged claim harder to verify.

- **Adoption deletes the mirror rather than re-exporting the generated type from
  it.** A re-export leaves the old path working, which means nothing forces the
  next author to use the generated type, and the mirror survives indefinitely as a
  file that looks authoritative.

- **`COMPAT.md` records what the combination was verified by, not that it works.**
  "Verified by: `q_backend` `uv run pytest` green, `q_frontend` `pnpm test:run`
  and `pnpm typecheck` green, at these hashes" is checkable a year later; "known
  good" is not.

## Ordered implementation

1. Create the branch `Q-006-contract-codegen-and-vendoring-spec` in `q_contracts`.
2. Write failing unit tests for `plan_units`: over the real `schema/` tree it
   returns a stable, sorted list; the same tree yields an identical list on a
   second call; a schema in an unrecognized dialect raises `GenerationError` whose
   message contains both the file path and the language. Confirm they fail,
   implement `plan_units`, confirm they pass. Commit.
3. Write failing tests for the Python emitter: the stream envelope emits a class
   with the nine envelope fields, `seq` typed as an integer and `epoch` as a
   string; the file's first line matches `HEADER` and contains
   `schema/stream/envelope.schema.json`; emitting twice yields identical bytes.
   Confirm they fail, implement `emitters/python.py`, confirm they pass. Commit.
4. Repeat step 3 for the TypeScript emitter, asserting the envelope emits an
   exported interface with the same nine fields and that optional fields are
   emitted with `?` rather than `| undefined`. Commit.
5. Repeat step 3 for the Rust emitter, asserting the envelope emits a struct with
   `serde` derives, that the three submit outcomes from Q-004 emit as an enum with
   exactly three variants, and that the four lookup outcomes emit as an enum with
   exactly four. Commit.
6. Write `tools/generate.py`'s `generate` and `main`, and a failing test that
   generating into a temporary directory twice produces byte-identical trees, and
   that generating into `generated/` after the committed generation produces no
   diff. Confirm they fail, implement, confirm they pass. Commit the generated
   tree.
7. Add a `generate-check` step to `make check` that regenerates into a temp dir and
   diffs against `generated/`, failing on any difference. Confirm `make check`
   passes. Commit.
8. Merge to `main` and record the resulting commit hash; this is the first pin.
9. In `q_frontend`: add `CONTRACTS_REV` holding that hash, a `Makefile` with
   `contracts` and `contracts-check` targets that clone `q_contracts` at the pinned
   hash into a temp directory and copy `generated/typescript/` into `contracts/`,
   and a `pnpm` script wrapping `contracts-check`. Run `make contracts`, commit the
   vendored tree. Confirm `pnpm typecheck` and `pnpm test:run` pass. Commit.
10. In `q_frontend`, replace the hand-written job progress type with the generated
    one: update the importing modules under `src/api/queries/` and delete the
    mirror. Confirm `pnpm typecheck`, `pnpm lint`, and `pnpm test:run` all pass
    unchanged — no test is modified in this step. Commit.
11. Add `contracts-check` to `q_frontend`'s CI. Verify criterion 8 by hand: edit a
    line in `contracts/`, run `make contracts-check`, confirm a non-zero exit
    naming the file, revert. Commit the CI change only.
12. In `q_backend`: add `CONTRACTS_REV` with the same hash, a `Makefile` with the
    same two targets copying `generated/python/q_contracts/` into
    `contracts/`, and a `mise` task wrapping `contracts-check`. Run `make
    contracts`, commit the vendored tree, and confirm `uv run pytest` passes.
    Add `contracts-check` to `q_backend`'s CI. Commit.
13. Write `COMPAT.md` in `q_contracts`: a row per repository with its commit hash,
    the Python-generation split rule, the C++ non-generation decision with its
    reason, and a "verified by" line naming the exact commands run in steps 10 and
    12 and their outcomes. Commit.
14. Human step, matching human-verifiable criterion 1: read one generated type per
    language and confirm it is usable without an adapter.
15. Human step, matching human-verifiable criterion 2: make a trivial additive
    schema change in `q_contracts`, commit it, advance `q_frontend`'s
    `CONTRACTS_REV` to the new hash, run `make contracts`, and review the diff.
    Revert the trial change and the pin afterwards, or keep both and update
    `COMPAT.md` — but not neither.
16. Human step, matching human-verifiable criterion 3: run `q_frontend` and confirm
    the surface that adopted the generated type behaves as before.
17. Run every validation suite — `make check` in `q_contracts`, `pnpm typecheck &&
    pnpm lint && pnpm test:run` in `q_frontend`, `uv run pytest` in `q_backend` —
    and commit. Report the handoff.

## Validation

- **Unit:** `plan_units` stability and its unsupported-dialect failure; per-emitter
  field, type, optionality, and enum-arity assertions; header content.
- **Integration:** double-generation byte identity; `make check`'s embedded
  generate-check; each consumer's `make contracts` producing no diff at its pin.
- **Regression:** `q_frontend`'s existing test suite passes unchanged across the
  type adoption in step 10, with no test file modified. That is the evidence that
  adoption changed where types come from and not what the code does.
- **Manual:** steps 14, 15, and 16.
- **Measurement:** report the wall-clock time of a full `generate` run and of one
  consumer's `make contracts`, since `make contracts` runs a clone and will be run
  often enough that a slow one gets skipped.

```bash
# contracts
cd /home/gui/projects/q/q_contracts && make check
uv run python tools/generate.py --out /tmp/gen-a && uv run python tools/generate.py --out /tmp/gen-b
diff -r /tmp/gen-a /tmp/gen-b && echo "deterministic"
diff -r /tmp/gen-a generated && echo "committed output matches"

# consumers
cd /home/gui/projects/q/q_frontend && make contracts-check && pnpm typecheck && pnpm lint && pnpm test:run
cd /home/gui/projects/q/q_backend  && make contracts-check && uv run pytest
```

## Handoff

Report the contracts commit hash recorded in both consumers' `CONTRACTS_REV`, and
confirm they are the same hash. Report the file count and total line count of
generated output per language, and the name of the one hand-written mirror deleted
in step 10 together with the list of modules updated to import the generated type
instead. State explicitly that no test file was modified in step 10, and give the
before and after results of `pnpm test:run` to show the suite passed unchanged.
Report the two determinism diffs from the command block as empty, quoting the
commands. Report the wall-clock time of a full generation and of one consumer's
`make contracts`. Report the exact failure output from the hand-edit check in step
11. Finally, report the `COMPAT.md` "verified by" line as written, since every
later cross-repo change is measured against it.
