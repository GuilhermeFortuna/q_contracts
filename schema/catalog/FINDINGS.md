# Lake Storage and Catalog Findings

This document records the architectural invariants required by the dataset manifest and catalog schema (`Q-005`), discrepancies identified in the existing `q_backend` market data store (`local_store.py`), and the triage decision for each finding.

---

## Finding 1: In-Place Parquet Mutation in `write_ohlcv` Violates Dataset Immutability

- **Component / Location:** `src/q_backend/market_data/local_store.py:181-196, 282-315` (`_merge_year_frame`, `_write_year_parquet`, `write_ohlcv`).
- **Invariant / Expectation:** Datasets are immutable. A published dataset has an immutable `dataset_id` and its underlying files are never mutated in place. New or appended data produces a new dataset with a new identifier and points backward via `supersedes`.
- **Observed Lake Behavior / Conflict:** In `write_ohlcv`, when new bars are ingested for an existing year, `local_store` reads the existing `{year}.parquet` file, merges and deduplicates rows in memory, and rewrites the file in place at the same path. A concurrent reader (such as `q_terminal` reading directly from the lake) holding an open file descriptor will see the file replaced or truncated underneath it, corrupting active queries and invalidating cached checksums.
- **Triage Decision:** Migration task. The storage ingest engine in `q_backend` must be migrated from in-place file mutation to writing versioned, immutable partition files accompanied by atomic manifest publication.

---

## Finding 2: Existing Catalog Key Carries No Version and Cannot Express `supersedes`

- **Component / Location:** `src/q_backend/market_data/local_store.py:110-120, 248-270` (`_catalog_entry_key`, `_upsert_catalog_entry`, `_catalog_path`).
- **Invariant / Expectation:** A dataset record carries a monotonic `version` integer within its subject, a stable opaque `dataset_id` (UUID form), and a `supersedes` backward pointer referencing the prior version it replaces. This enables point-in-time reproducibility, deterministic cache invalidation, and reader stability.
- **Observed Lake Behavior / Conflict:** The current catalog (`catalog.json`) keys entries by `(symbol, kind, timeframe)`. When new data is ingested, `_upsert_catalog_entry` replaces the existing entry with updated `first_time`, `last_time`, and `count`. There is no version number, no identity, no history of prior snapshots, and no representation of `supersedes`.
- **Triage Decision:** Migration task. The catalog repository in `q_backend` must transition to a versioned catalog model that stores immutable manifests with `dataset_id`, `version`, and `supersedes` backward pointers.

---

## Finding 3: Absence of Cryptographic Content Checksums in Lake Files

- **Component / Location:** `src/q_backend/market_data/local_store.py:196-205` (`_write_year_parquet`, `_write_month_parquet`).
- **Invariant / Expectation:** Every file entry in a dataset manifest carries a cryptographic content checksum (`checksum`) under a declared algorithm (`checksum_algorithm`), along with `size_bytes`, allowing readers to verify file integrity and completeness before trusting data.
- **Observed Lake Behavior / Conflict:** Existing Parquet files are written without calculating or persisting digests. `catalog.json` records only row count and timestamps. A reader has no mechanism to detect partial writes, bit rot, or file truncation without scanning file footers or reading rows.
- **Triage Decision:** Migration task. The dataset publisher must compute digests (standardizing on SHA-256) at publication time and record them in the manifest `files` list.

---

## Finding 4: Source-Relative Lake Root Resolution (`_project_root`) Incompatible with External Readers

- **Component / Location:** `src/q_backend/market_data/local_store.py:54-70` (`_project_root`, `market_data_root`).
- **Invariant / Expectation:** Boundaries of ownership: file paths within a manifest are strictly relative to a lake root (`files[].path`). The lake root must be supplied to readers independently (via environment variable `Q_MARKET_DATA_ROOT` or application configuration), completely decoupled from `q_backend` source code location.
- **Observed Lake Behavior / Conflict:** `local_store.py` falls back to computing `_project_root() = Path(__file__).resolve().parents[3] / settings.market_data_root`. Independent external processes (such as `q_terminal`, CLI tools, or distributed workers) running in different containers, separate virtual environments, or different machines cannot reproduce paths based on `local_store.py`'s file location.
- **Triage Decision:** Accepted deviation / configuration policy. The manifest schema strictly enforces relative paths (`^(?![/\\])(?!.*(?:^|[/\\])\.\.(?:[/\\]|$)).+$`). Lake consumers (`q_terminal`, `q_backend`, `q_contracts`) must configure the root path via explicit configuration (`Q_MARKET_DATA_ROOT`), never relying on source tree traversal.

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
