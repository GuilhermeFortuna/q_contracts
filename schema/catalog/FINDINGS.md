# Lake Storage and Catalog Findings

This document records the architectural invariants required by the dataset manifest and catalog schema (`Q-005`), discrepancies identified in the existing `q_backend` market data store (`local_store.py`), and the triage decision for each finding.

---

## Finding 1: In-Place Parquet Mutation in `write_ohlcv` Violates Dataset Immutability

- **Component / Location:** `src/q_backend/market_data/local_store.py:181-196, 282-315` (`_merge_year_frame`, `_write_year_parquet`, `write_ohlcv`).
- **Invariant / Expectation:** Datasets are immutable. A published dataset has an immutable `dataset_id` and its underlying files are never mutated in place. New or appended data produces a new dataset with a new identifier and points backward via `supersedes`.
- **Observed Lake Behavior / Conflict:** In `write_ohlcv`, when new bars are ingested for an existing year, `local_store` reads the existing `{year}.parquet` file, merges and deduplicates rows in memory, and rewrites the file in place at the same path. A concurrent reader (such as `q_terminal` reading directly from the lake) holding an open file descriptor will see the file replaced or truncated underneath it, corrupting active queries and invalidating cached checksums.
- **Triage Decision:** Resolved by Q-017. `q_backend` now implements content-addressed, immutable parquet partitions (`write_partition_immutable`) and catalog tracking (`LakeCatalog`), leaving superseded files intact under a configurable grace period (default 7 days) for active readers.

---

## Finding 2: Existing Catalog Key Carries No Version and Cannot Express `supersedes`

- **Component / Location:** `src/q_backend/market_data/local_store.py:110-120, 248-270` (`_catalog_entry_key`, `_upsert_catalog_entry`, `_catalog_path`).
- **Invariant / Expectation:** A dataset record carries a monotonic `version` integer within its subject, a stable opaque `dataset_id` (UUID form), and a `supersedes` backward pointer referencing the prior version it replaces. This enables point-in-time reproducibility, deterministic cache invalidation, and reader stability.
- **Observed Lake Behavior / Conflict:** The current catalog (`catalog.json`) keys entries by `(symbol, kind, timeframe)`. When new data is ingested, `_upsert_catalog_entry` replaces the existing entry with updated `first_time`, `last_time`, and `count`. There is no version number, no identity, no history of prior snapshots, and no representation of `supersedes`.
- **Triage Decision:** Resolved by Q-017. `q_backend` implemented the PostgreSQL/SQLite `lake_datasets` and `lake_dataset_files` catalog schema with immutable UUID `dataset_id`, monotonic `version`, and `supersedes` backward pointer.

---

## Finding 3: Absence of Cryptographic Content Checksums in Lake Files

- **Component / Location:** `src/q_backend/market_data/local_store.py:196-205` (`_write_year_parquet`, `_write_month_parquet`).
- **Invariant / Expectation:** Every file entry in a dataset manifest carries a cryptographic content checksum (`checksum`) under a declared algorithm (`checksum_algorithm`), along with `size_bytes`, allowing readers to verify file integrity and completeness before trusting data.
- **Observed Lake Behavior / Conflict:** Existing Parquet files are written without calculating or persisting digests. `catalog.json` records only row count and timestamps. A reader has no mechanism to detect partial writes, bit rot, or file truncation without scanning file footers or reading rows.
- **Triage Decision:** Resolved by Q-017. Lake partition writes in `q_backend` compute SHA-256 digests (`checksum`) and file byte sizes during atomic write and record them in the manifest files list.

---

## Finding 4: Source-Relative Lake Root Resolution (`_project_root`) Incompatible with External Readers

- **Component / Location:** `src/q_backend/market_data/local_store.py:54-70` (`_project_root`, `market_data_root`).
- **Invariant / Expectation:** Boundaries of ownership: file paths within a manifest are strictly relative to a lake root (`files[].path`). The lake root must be supplied to readers independently (via environment variable `Q_MARKET_DATA_ROOT` or application configuration), completely decoupled from `q_backend` source code location.
- **Observed Lake Behavior / Conflict:** `local_store.py` falls back to computing `_project_root() = Path(__file__).resolve().parents[3] / settings.market_data_root`. Independent external processes (such as `q_terminal`, CLI tools, or distributed workers) running in different containers, separate virtual environments, or different machines cannot reproduce paths based on `local_store.py`'s file location.
- **Triage Decision:** Accepted deviation / configuration policy. The manifest schema strictly enforces relative paths (`^(?![/\\])(?!.*(?:^|[/\\])\.\.(?:[/\\]|$)).+$`). Lake consumers (`q_terminal`, `q_backend`, `q_contracts`) must configure the root path via explicit configuration (`Q_MARKET_DATA_ROOT`), never relying on source tree traversal.

---

## Finding 5: `describe_dataset.py` Labels Naive Wall-Clock Bounds as UTC

- **Component / Location:** `tools/describe_dataset.py:33-40` (`_format_time_bound`).
- **Invariant / Expectation:** A dataset manifest's time range expresses UTC instants that correspond to the lake's naive Brasília wall-clock values (`America/Sao_Paulo`). A naive timestamp `09:00` represents Brasília wall clock and corresponds to `12:00 UTC` (RFC 3339 `...T12:00:00Z`).
- **Observed Lake Behavior / Conflict:** `_format_time_bound` formatted naive `datetime` instances by appending `Z` directly (`val.strftime("%Y-%m-%dT%H:%M:%SZ")`), treating naive local wall-clock values as UTC instants without offset adjustment. A 09:00 Brasília bar was labeled as `09:00:00Z` instead of `12:00:00Z`.
- **Triage Decision:** Bug / alignment task. Tools constructing manifests from naive lake files must interpret naive timestamps in `America/Sao_Paulo` before converting to UTC RFC 3339 strings, matching `q_backend`'s catalog implementation in Q-017.

---

## Finding 6: Nullable Arrow Type Representation for Unpopulated Lake Columns

- **Component / Location:** `schema/catalog/dataset-manifest.schema.json` and lake partition parquet files.
- **Invariant / Expectation:** The manifest's inline `arrow_schema` reflects the physical columns and types in the lake partition files.
- **Observed Lake Behavior / Conflict:** In existing bar files where optional columns such as `spread` or `real_volume` contain only nulls (e.g. historical daily bars ingested without volume or spread), PyArrow infers column type as `null` rather than `int64`. In `q_backend`, `lake_arrow_schema` normalizes Arrow types to canonical physical forms (`int64`, `float64`, `int32`, `timestamp[us]`) while preserving `tz="naive-wallclock-America/Sao_Paulo"` for the time column to ensure readers have explicit type information even on empty or sparse partitions.
- **Triage Decision:** Documented schema invariant. Readers should accept `type: "null"` or canonical physical types for sparse/all-null optional columns in existing lake partitions.

---

## Reader Walkthrough (Human-Verifiable Criterion 2)

Opening a dataset given only the manifest and an externally supplied root path:

1. **Which files belong to this dataset?**
   - The reader inspects `manifest["files"]`. Each file is explicitly listed with its relative path.
2. **In what order should files be processed?**
   - Files are enumerated in `manifest["files"]`. For sequential time series, the reader or publisher can order them by time; each file's exact identity and relative path are known upfront.
3. **With what columns and types?**
   - The reader inspects `manifest["arrow_schema"]["fields"]`. Column names, physical Arrow types, nullability, and timezones (`tz`) are fully known before opening any file.
4. **Verified how?**
   - For each file in `manifest["files"]`:
     1. The reader checks that `file["size_bytes"] == stat(root / file["path"]).st_size`.
     2. The reader computes the digest of `root / file["path"]` under `manifest["checksum_algorithm"]` (e.g. SHA-256) and asserts equality with `file["checksum"]`.
5. **Covering what range and row count?**
   - `manifest["time_range"]["start"]` and `manifest["time_range"]["end"]` provide inclusive temporal boundaries; `manifest["row_count"]` provides total row count.
6. **Are any directory listings or external queries required?**
   - No. The reader accesses only `root / file["path"]` directly. No `glob`, no `os.listdir`, and no database queries are required to read, verify, or interpret the dataset.
