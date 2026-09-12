# Q-005: Dataset manifest and catalog schema

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** Q-001  
**Implementation plan:** [`../plans/Q-005-dataset-manifest-and-catalog-schema-plan.md`](../plans/Q-005-dataset-manifest-and-catalog-schema-plan.md)

## Purpose

Data in the lake is found today by constructing a path from a symbol and a
timeframe and listing a directory, and it is updated by rewriting the file in
place. Both properties are incompatible with a second process reading the same
files: a reader holding an open file can see it replaced underneath, and a reader
that guesses a path has no way to know whether what it found is complete. The
architecture makes datasets immutable and catalog-addressed; this task writes the
schema that makes that enforceable — what a dataset identity is, what a manifest
must contain for a reader to verify what it opened, and what publication and
tombstoning mean. It is the prerequisite for `q_terminal` reading Parquet
directly, which is the whole point of the direct-read path.

## Requirements

### Dataset identity

- A dataset has an identifier that is immutable and is not derived from a path,
  so that moving or reorganizing files cannot change what a dataset is.
- The identifier is assigned at publication and never reused, including after
  tombstoning, because a reused identifier makes a stale cached manifest
  indistinguishable from a current one.
- New data produces a new dataset with a new identifier rather than modifying an
  existing one; the schema provides no representation of a mutated dataset.
- A dataset records what it is a version of, so that a caller asking for the
  latest data on a subject can be answered without scanning.

### Manifest content

- A manifest lists every file belonging to the dataset, each with its size and a
  content checksum, so a reader can verify before trusting.
- The manifest carries the Arrow schema of the dataset's contents, so a reader
  knows the columns without opening a file.
- The manifest carries the row count, the time range covered, and the publication
  instant.
- The manifest is sufficient on its own: a reader given only the manifest can
  open, verify, and interpret the dataset without consulting any other source and
  without listing any directory.
- The manifest states which checksum algorithm was used, rather than fixing one
  forever by convention.

### Lifecycle states

- The states a dataset can be in are declared, and the legal transitions between
  them are declared, so that an implementation cannot invent a state.
- Publication is described as atomic from a reader's perspective: a dataset is
  either absent or complete, never partially visible.
- Tombstoning marks a dataset as no longer offered to new readers while its files
  remain readable for a grace period, and the grace period is part of the record
  rather than a global constant, so an open reader never loses a file mid-read.
- The schema expresses that a tombstoned dataset's files are eventually deleted,
  and records when that becomes permissible.

### Boundaries of ownership

- The manifest describes files; it does not describe where the lake root is, what
  the retention policy is, or how paths are constructed. Those belong to the
  process that owns dataset lifecycle.
- File references in the manifest are relative to a root the reader is told
  separately, so a manifest is valid regardless of where the lake is mounted.
- The schema carries no notion of a catalog implementation, a database table, or
  a query interface; it describes the record, not the store.

### Compatibility with what exists

- The manifest can describe the data the lake holds today without that data being
  rewritten, so that adopting the catalog is a cataloguing exercise rather than a
  migration.
- Where today's lake layout cannot satisfy an invariant the schema requires, that
  is recorded as a finding naming the invariant and the conflict, rather than the
  invariant being weakened to fit.

## Constraints and non-goals

- **No catalog implementation.** No database schema, no migration, no repository
  functions, no endpoint. The catalog lives in `q_backend` and is a later task.
- **No changes to the lake layout.** Directory structure, partitioning, file
  naming, and the existing catalog file stay exactly as they are. This task
  describes; the migration is separate and will need this description first.
- **No changes to `q_backend`.** The local store is read as evidence, not edited.
- **No reader implementation.** Checksum verification, manifest-driven opening,
  and the HTTP fallback belong to `q_core` and `q_terminal` in later tasks.
- **No retention policy values.** How long a dataset is kept, how large the lake
  may grow, and when tombstoning is triggered are operational decisions. The
  schema carries the grace period as a recorded value because a reader needs it;
  it does not choose the value.
- **No compression, encoding, or file-format decisions.** The manifest records
  what a file is; it does not prescribe how it was written.

## Acceptance criteria

### Agent-verifiable

1. The manifest schema exists under the catalog boundary and passes the
   repository's validation command.
2. A manifest example describing a multi-file dataset validates, and examples
   missing the file list, the checksum on any file, the Arrow schema, the row
   count, the time range, or the publication instant each fail with the missing
   element named.
3. A manifest whose file reference is an absolute path, or contains a parent
   directory component, fails validation.
4. The identifier field rejects a value that encodes a path, verified by an
   example carrying a path-like identifier failing validation.
5. The lifecycle states and their legal transitions are declared, and an example
   asserting an illegal transition fails a consistency check that names both
   states.
6. A tombstoned dataset record without a grace period fails validation.
7. The Arrow schema carried in a manifest resolves to the same declaration form
   used by the columnar payload schemas, verified by a test that a manifest
   carrying the bar schema validates against it.
8. A manifest is generated from a real artifact in the existing lake and
   validates, demonstrating that today's data is describable without being
   rewritten.
9. Findings are recorded for every invariant today's layout cannot satisfy, each
   naming the invariant and the conflict.
10. The full validation suite passes.

### Human-verifiable

1. The findings are reviewed and each is triaged as a migration task, an accepted
   deviation, or a schema correction, with the decision recorded beside it.
   Command: `$EDITOR q_contracts/schema/catalog/FINDINGS.md`
2. The manifest is confirmed sufficient by walking through opening a dataset using
   only the manifest and a root path, listing every question the reader must ask
   and confirming the manifest answers each.
   Command: `$EDITOR q_contracts/schema/catalog/dataset-manifest.schema.json`
