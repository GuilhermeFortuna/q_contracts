# Q-005 implementation plan: Dataset manifest and catalog schema

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Specification:** [`../specs/Q-005-dataset-manifest-and-catalog-schema-spec.md`](../specs/Q-005-dataset-manifest-and-catalog-schema-spec.md)  
**Depends on:** Q-001

## Current-system context

The lake is `src/q_backend/market_data/local_store.py`. Its root comes from
`market_data_root()` at line 58, which reads `Q_MARKET_DATA_ROOT` or falls back to
`settings.market_data_root`, itself relative to `_project_root()` at line 54 —
`Path(__file__).resolve().parents[3]`, a path computed from the source file's own
location. Paths are constructed, not looked up: `_slug_symbol` at line 73,
`_ohlcv_series_dir(symbol, timeframe)` at line 81, `_year_parquet_path(symbol,
timeframe, year)` at line 90, `_ticks_series_dir` at line 94, and
`_month_parquet_path(symbol, month_key)` at line 98. There is already a catalog of
a kind — `_catalog_path()` at line 77, `_read_catalog` at 124, `_write_catalog` at
140, `_upsert_catalog_entry` at 248, `_remove_catalog_entry` at 264, keyed by
`_catalog_entry_key` at line 110 as `(symbol, kind, timeframe)` — but it is a
file of summaries derived by `_summarize_series` at line 209, not an identity.

The property that matters most here is in `write_ohlcv` at line 282: it merges
through `_merge_year_frame` at line 181 and rewrites the year's Parquet file via
`_write_year_parquet` at line 196. Data is mutated in place, the catalog key is
derived from the data's subject rather than from a version, and there is no
checksum anywhere. A second process — which is exactly what `q_terminal` will be —
can open a file and have it replaced beneath it, and cannot tell whether what it
read was complete. Also unused for this purpose: `pyarrow>=24.0.0` is already a
declared dependency, so Arrow schemas can be read from real files without adding
anything. The gap this task closes is that there is no written definition of a
dataset identity, so nothing can be addressed, verified, or held stable while it
is read.

## Interfaces produced

```
// q_contracts/schema/catalog/
dataset-manifest.schema.json   the record a reader is handed
lifecycle.yaml                 states and legal transitions
FINDINGS.md                    invariants today's lake cannot satisfy
examples/                      fixtures the validity tests load
```

```jsonc
// schema/catalog/dataset-manifest.schema.json
{
  "dataset_id":     "opaque string, UUID form; rejects '/', '\\', '.' segments",
  "subject":        "what this is data about, e.g. {kind, symbol, timeframe}",
  "version":        "integer >= 1; monotonic within a subject",
  "supersedes":     "dataset_id | null; the version this one replaces",
  "state":          "enum from lifecycle.yaml",
  "published_at":   "RFC 3339 UTC instant",
  "checksum_algorithm": "enum; the algorithm every file entry used",
  "files": [
    {"path": "relative, no leading separator, no '..' segment",
     "size_bytes": "integer >= 0",
     "checksum": "hex digest under checksum_algorithm"}
  ],
  "arrow_schema":   "the same field-declaration form used by schema/api/arrow/*",
  "row_count":      "integer >= 0",
  "time_range":     "{start, end} — inclusive bounds over the dataset's time column",
  "tombstone":      "null, or {tombstoned_at, deletable_after}"
}
```

```yaml
# schema/catalog/lifecycle.yaml
states: [publishing, published, tombstoned, deleted]
transitions:
  publishing:  [published]          # a failed publish leaves no record at all
  published:   [tombstoned]
  tombstoned:  [deleted]
  deleted:     []
invariants:
  - state == tombstoned implies tombstone is not null
  - state == published  implies tombstone is null
  - files is non-empty for every state except deleted
```

```python
# q_contracts/tools/validate.py  (extended)
def check_catalog_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Every state named in an example exists in lifecycle.yaml; every lifecycle
    invariant holds for every committed example; the manifest's arrow_schema
    field uses the same declaration form as schema/api/arrow/*."""

# q_contracts/tools/describe_dataset.py
def manifest_from_directory(root: Path, rel_paths: Sequence[Path], subject: dict) -> dict:
    """Build a manifest for existing files. Reads Arrow schema, row count and time
    range from the files themselves; assigns no identity and writes nothing."""
```

## Implementation decisions

- **`dataset_id` is opaque and explicitly rejects path-like values.** The obvious
  and wrong choice is a readable identifier such as `WINFUT-M15-2024`, because it
  is nice in a log. It is also a path, and the moment it is a path somebody
  constructs a filename from it, which reintroduces exactly the directory-guessing
  the catalog exists to remove. The schema's rejection of separators and `.`
  segments is what makes that impossible rather than merely discouraged.

- **Identity is separate from subject, and both are recorded.** Identity must be
  stable and meaningless; the question a caller actually asks — "the latest M15
  bars for this symbol" — is about the subject. Keeping `subject`, `version` and
  `supersedes` in the manifest lets the second question be answered without
  scanning files and without overloading the identifier with meaning.

- **`supersedes` points backwards, not forwards.** A forward pointer would have to
  be written into an already-published manifest when its successor appears, which
  would mutate an immutable record — the one thing this schema exists to prevent.
  Backward pointers are written once, at publication, by the only process that
  knows both values.

- **There is no `publishing` record visible to readers, and the state exists only
  so a writer can name the interval.** `publishing` appears in `lifecycle.yaml`
  with exactly one outgoing transition and no legal way to be observed in a
  published manifest, because the atomicity requirement means a failed publish
  leaves nothing behind at all. Modelling it as a state a reader might see would
  invite a reader to handle partial datasets, and a reader that handles partial
  datasets will eventually chart one.

- **`checksum_algorithm` is a field rather than a fixed convention.** Fixing an
  algorithm in prose means the day it is changed, every old manifest becomes
  ambiguous and the ambiguity is silent — a verification that compares a new digest
  against an old one simply fails and looks like corruption. Naming it per manifest
  costs a string and makes the change a non-event.

- **File paths are relative, with absolute paths and `..` segments rejected by the
  schema rather than by the reader.** A reader that rejects them is one reader;
  there will be at least three (`q_backend`, `q_core`, `q_terminal`), and the one
  that forgets is the one running with the widest filesystem access. Rejecting at
  the schema puts it in every generated type's validation path.

- **`tombstone` carries `deletable_after` as a recorded instant rather than the
  grace period as a duration.** A duration would have to be combined with a global
  policy value at read time, and the two processes doing that combination could
  hold different policy values. An instant is a fact; every reader computes the
  same answer from it.

- **The manifest carries the Arrow schema inline rather than referencing one from
  `schema/api/arrow/`.** A reference would mean a manifest's meaning depends on the
  contracts commit the reader has vendored, so the same manifest could be read two
  ways by two consumers on different pins. Inline makes the manifest
  self-sufficient, which is the spec's requirement, at the cost of repetition —
  and the consistency check still enforces that the inline form is the same
  declaration form Q-003 defined, so the two cannot diverge structurally.

- **`describe_dataset.py` assigns no identity and writes nothing.** Its only job is
  to prove, in step 8, that today's files are describable. If it could assign an
  identity it would be a catalog implementation, which the spec rules out, and it
  would be the second place identities are minted.

- **Conflicts with today's layout become findings, not schema relaxations.** The
  known conflict is `write_ohlcv`'s in-place merge: a year file rewritten on every
  ingest cannot be an immutable dataset, and no manifest field makes it one. The
  correct output of this task is a schema that says so and a finding that names
  it, because weakening the immutability rule to accommodate the current writer
  would remove the reason the schema exists.

## Ordered implementation

1. Create the branch `Q-005-dataset-manifest-and-catalog-schema-spec`.
2. Write `schema/catalog/lifecycle.yaml` with the four states, the transition map,
   and the three invariants. Write failing tests: the transition map is total over
   the state list, `deleted` has no outgoing transitions, and `publishing` has
   exactly one. Confirm they fail, implement, confirm they pass. Commit.
3. Write `schema/catalog/dataset-manifest.schema.json` with the fields above.
   Write `examples/manifest-bars-two-files.json` describing a two-file dataset.
   Confirm `make check` passes. Commit.
4. Write failing validity tests: the two-file example validates; six mutants — one
   each with `files`, a file's `checksum`, `arrow_schema`, `row_count`,
   `time_range`, and `published_at` removed — each fail with the missing element
   named in the error. Confirm they fail, adjust the schema's `required` lists
   until they pass. Commit.
5. Write failing tests for the path and identity rules: a file entry with path
   `/abs/x.parquet` fails; one with `a/../b.parquet` fails; one with
   `bars/2024.parquet` validates; a `dataset_id` of `WINFUT/M15/2024` fails; a
   UUID-form `dataset_id` validates. Confirm they fail, implement the schema
   constraints, confirm they pass. Commit.
6. Write failing tests for the lifecycle invariants: a manifest with
   `state: tombstoned` and `tombstone: null` fails; one with `state: published`
   and a non-null `tombstone` fails; one with `state: tombstoned` whose tombstone
   lacks `deletable_after` fails; an example asserting a `published -> publishing`
   transition fails a consistency check naming both states. Confirm they fail,
   implement `check_catalog_consistency`, wire it into `check_tree`, confirm they
   pass. Commit.
7. Write a failing test that a manifest carrying the bar Arrow declaration from
   Q-003's `schema/api/arrow/bars.schema.json` validates against the manifest's
   `arrow_schema` subschema, proving the two forms agree. Confirm it fails,
   reconcile the form, confirm it passes. Commit.
8. Write `tools/describe_dataset.py` and a test that, given a real Parquet file
   from the existing lake (path supplied by `Q_MARKET_DATA_ROOT`, the test skipping
   when unset so `make check` stays green offline), builds a manifest whose
   `arrow_schema`, `row_count` and `time_range` are read from the file and which
   validates against the schema. Confirm it fails, implement, confirm it passes.
   Commit.
9. Write `schema/catalog/FINDINGS.md`. Record at minimum: `write_ohlcv`'s in-place
   merge and rewrite versus the immutability invariant; `_catalog_entry_key`'s
   `(symbol, kind, timeframe)` subject key carrying no version, so today's catalog
   cannot express `supersedes`; the absence of any checksum in the existing lake;
   `_project_root()` deriving the lake root from a source file's location, which no
   external reader can reproduce. Commit.
10. Human step, matching human-verifiable criterion 1: triage each finding as a
    migration task, an accepted deviation, or a schema correction, recording the
    decision beside it.
11. Human step, matching human-verifiable criterion 2: walk through opening a
    dataset given only a manifest and a root path; list every question the reader
    must answer — which files, in what order, with what columns, verified how,
    covering what range — and confirm the manifest answers each without a directory
    listing.
12. Run the full validation suite and commit. Report the handoff.

## Validation

- **Unit:** lifecycle map totality and the three per-state rules; the six
  required-field mutants; the five path and identity cases; the three lifecycle
  invariant violations; the Arrow declaration-form agreement.
- **Integration:** `make check` over the whole tree, running this task's
  consistency check alongside Q-002's, Q-003's and Q-004's.
- **Regression:** step 8 is the standing check that today's lake data remains
  describable. Its fixture is a real Parquet file; if a later change to the schema
  makes existing data undescribable, this test fails rather than the discovery
  happening during a migration.
- **Manual:** steps 10 and 11.

```bash
cd /home/gui/projects/q/q_contracts
make check
uv run pytest tests/ -k catalog -v
# step 8 against the real lake
Q_MARKET_DATA_ROOT=/home/gui/projects/q/q_backend/data uv run pytest tests/test_describe_dataset.py -v
```

## Handoff

Report the manifest generated in step 8 in full — the file list with sizes and
checksums, the Arrow schema read from the file, the row count, and the time range
— because that manifest is the evidence that today's data is describable, and a
summary of it is not evidence. Report every entry in `FINDINGS.md` with its
triage decision, and state plainly which invariants today's lake violates; the
in-place rewrite in `write_ohlcv` is expected to be one and should be reported as
a migration task rather than as an accepted deviation, or the reason for the
opposite decision should be given. Report the checksum algorithm chosen for the
example and the digest of at least one real file, so the cost of checksumming the
existing lake can be estimated from a real number. Confirm that `make check`
passes with `Q_MARKET_DATA_ROOT` unset and that the lake-dependent test skips
rather than fails in that case.
