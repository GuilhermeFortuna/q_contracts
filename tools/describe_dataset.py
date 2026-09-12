"""Tool to describe existing lake artifacts as dataset manifests."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq


def _normalize_arrow_type(type_str: str) -> str:
    """Normalize PyArrow type string to schema declaration representation."""
    type_str = type_str.lower()
    if type_str in ("double", "float64", "f8"):
        return "float64"
    if type_str in ("int64", "i8"):
        return "int64"
    if type_str in ("int32", "i4"):
        return "int32"
    if type_str in ("uint32", "u4"):
        return "uint32"
    if type_str in ("float32", "float", "f4"):
        return "float32"
    if type_str.startswith("timestamp"):
        return type_str
    return type_str


def _format_time_bound(val: Any) -> str:
    """Format a timestamp value to RFC 3339 UTC representation."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.strftime("%Y-%m-%dT%H:%M:%SZ")
        return val.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(val)


def bars_datasets(root: Path) -> list[tuple[dict[str, Any], list[Path]]]:
    """Every OHLCV bar series the lake holds, as (subject, files-relative-to-root).

    The lake keeps bars under ``ohlcv/<symbol>/<timeframe>/``; other parquet
    lives elsewhere under the same root, so a series is identified by that
    layout rather than by scanning for parquet and hoping.
    """
    series_root = root / "ohlcv"
    if not series_root.is_dir():
        return []

    datasets: list[tuple[dict[str, Any], list[Path]]] = []
    for timeframe_dir in sorted(series_root.glob("*/*")):
        if not timeframe_dir.is_dir():
            continue
        rel_paths = [
            path.relative_to(root)
            for path in sorted(timeframe_dir.glob("*.parquet"))
            if path.is_file()
        ]
        if not rel_paths:
            continue
        datasets.append(
            (
                {
                    "kind": "bars",
                    "symbol": timeframe_dir.parent.name,
                    "timeframe": timeframe_dir.name,
                },
                rel_paths,
            )
        )
    return datasets


def manifest_from_directory(
    root: Path,
    rel_paths: Sequence[Path],
    subject: dict[str, Any],
    checksum_algorithm: str = "sha256",
    placeholder_dataset_id: str = "00000000-0000-0000-0000-000000000000",
) -> dict[str, Any]:
    """Build a manifest for existing files. Reads Arrow schema, row count and time
    range from the files themselves; assigns no identity and writes nothing."""
    files_entry: list[dict[str, Any]] = []
    total_row_count = 0
    min_time: datetime | None = None
    max_time: datetime | None = None
    arrow_fields: list[dict[str, Any]] = []

    for rel_path in rel_paths:
        rel_p = Path(rel_path)
        abs_p = root / rel_p
        if not abs_p.is_file():
            raise FileNotFoundError(f"Dataset file not found: {abs_p}")

        data_bytes = abs_p.read_bytes()
        size_bytes = len(data_bytes)

        if checksum_algorithm == "sha256":
            checksum = hashlib.sha256(data_bytes).hexdigest()
        elif checksum_algorithm == "md5":
            checksum = hashlib.md5(data_bytes).hexdigest()
        else:
            h = hashlib.new(checksum_algorithm)
            h.update(data_bytes)
            checksum = h.hexdigest()

        files_entry.append(
            {
                "path": rel_p.as_posix(),
                "size_bytes": size_bytes,
                "checksum": checksum,
            }
        )

        table = pq.read_table(abs_p)
        total_row_count += table.num_rows

        if not arrow_fields:
            for field in table.schema:
                norm_type = _normalize_arrow_type(str(field.type))
                field_decl: dict[str, Any] = {
                    "name": field.name,
                    "type": norm_type,
                    "nullable": field.nullable,
                }
                if norm_type.startswith("timestamp"):
                    field_tz = getattr(field.type, "tz", None)
                    field_decl["tz"] = (
                        str(field_tz)
                        if field_tz
                        else "naive-wallclock-America/Sao_Paulo"
                    )
                arrow_fields.append(field_decl)

        # Time range computation
        time_col = None
        for cand in ("time", "time_msc"):
            if cand in table.column_names:
                time_col = cand
                break
        if time_col is None:
            for col_name in table.column_names:
                if str(table[col_name].type).startswith("timestamp"):
                    time_col = col_name
                    break

        if time_col is not None and table.num_rows > 0:
            file_min = pc.min(table[time_col]).as_py()
            file_max = pc.max(table[time_col]).as_py()
            if min_time is None or file_min < min_time:
                min_time = file_min
            if max_time is None or file_max > max_time:
                max_time = file_max

    now_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_range = {
        "start": _format_time_bound(min_time) if min_time is not None else now_utc,
        "end": _format_time_bound(max_time) if max_time is not None else now_utc,
    }

    arrow_schema = {
        "name": subject.get("kind", "bars"),
        "fields": arrow_fields,
    }

    manifest = {
        "dataset_id": placeholder_dataset_id,
        "subject": subject,
        "version": 1,
        "supersedes": None,
        "state": "published",
        "published_at": now_utc,
        "checksum_algorithm": checksum_algorithm,
        "files": files_entry,
        "arrow_schema": arrow_schema,
        "row_count": total_row_count,
        "time_range": time_range,
        "tombstone": None,
    }

    return manifest
