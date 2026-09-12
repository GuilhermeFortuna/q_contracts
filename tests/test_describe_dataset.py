import json
import os
from pathlib import Path

import jsonschema
import pytest


def test_describe_dataset_skipped_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("Q_MARKET_DATA_ROOT", raising=False)
    # With Q_MARKET_DATA_ROOT unset, the lake test must skip
    if "Q_MARKET_DATA_ROOT" not in os.environ:
        pytest.skip("Q_MARKET_DATA_ROOT environment variable not set")


def test_describe_dataset_from_existing_lake() -> None:
    env_root = os.getenv("Q_MARKET_DATA_ROOT")
    if not env_root:
        pytest.skip("Q_MARKET_DATA_ROOT environment variable not set")

    root = Path(env_root)
    if not root.is_dir():
        pytest.skip(f"Q_MARKET_DATA_ROOT '{root}' is not a directory")

    from tools.describe_dataset import bars_datasets, manifest_from_directory

    datasets = bars_datasets(root)
    if not datasets:
        pytest.skip(f"No ohlcv/<symbol>/<timeframe> bar series under '{root}'")

    subject, rel_paths = datasets[0]

    manifest = manifest_from_directory(
        root=root,
        rel_paths=rel_paths,
        subject=subject,
    )

    # 1. Manifest must validate against dataset-manifest.schema.json
    schema_path = (
        Path(__file__).parent.parent
        / "schema"
        / "catalog"
        / "dataset-manifest.schema.json"
    )
    schema_doc = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema_doc)
    errors = list(validator.iter_errors(manifest))
    assert errors == [], f"Generated manifest failed validation: {errors}"

    # 2. Manifest contents must reflect the series it describes
    assert manifest["row_count"] > 0
    assert "start" in manifest["time_range"]
    assert "end" in manifest["time_range"]
    assert [entry["path"] for entry in manifest["files"]] == [
        rel_path.as_posix() for rel_path in rel_paths
    ]
    for entry, rel_path in zip(manifest["files"], rel_paths, strict=True):
        assert entry["size_bytes"] == (root / rel_path).stat().st_size
        assert len(entry["checksum"]) == 64  # sha256 hex digest length
    declared = [field["name"] for field in manifest["arrow_schema"]["fields"]]
    assert declared[0] == "time"
    assert {"open", "high", "low", "close"} <= set(declared)


def test_describe_dataset_unit_with_fixture() -> None:
    """Always-run unit test using local repository fixture to verify describe_dataset logic."""
    from tools.describe_dataset import manifest_from_directory

    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_rel = Path("bars_sample.parquet")
    assert (fixture_dir / fixture_rel).is_file()

    subject = {
        "kind": "bars",
        "symbol": "PETR4",
        "timeframe": "D1",
    }

    manifest = manifest_from_directory(
        root=fixture_dir,
        rel_paths=[fixture_rel],
        subject=subject,
    )

    schema_path = (
        Path(__file__).parent.parent
        / "schema"
        / "catalog"
        / "dataset-manifest.schema.json"
    )
    schema_doc = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema_doc)
    errors = list(validator.iter_errors(manifest))
    assert errors == [], f"Fixture manifest failed validation: {errors}"
    assert manifest["row_count"] == 2
    assert manifest["files"][0]["path"] == "bars_sample.parquet"
    assert manifest["arrow_schema"]["fields"][0]["name"] == "time"
    assert (
        manifest["arrow_schema"]["fields"][0]["tz"]
        == "naive-wallclock-America/Sao_Paulo"
    )


def _write_parquet(path: Path, columns: dict[str, list]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(columns), path)


def test_bars_datasets_selects_the_ohlcv_layout_and_ignores_other_parquet(
    tmp_path: Path,
) -> None:
    """A lake root holds more than bars; selection must not depend on sort order."""
    from tools.describe_dataset import bars_datasets

    # Sorts before "ohlcv/", and is the file a naive rglob would pick first.
    _write_parquet(
        tmp_path / "lake" / "strategy_search" / "abc" / "leaderboard.parquet",
        {"time": [1, 2], "equity": [1.0, 2.0]},
    )
    _write_parquet(
        tmp_path / "ohlcv" / "PETR4" / "D1" / "2024.parquet",
        {"time": [1, 2], "open": [1.0, 2.0]},
    )

    datasets = bars_datasets(tmp_path)

    assert len(datasets) == 1
    subject, rel_paths = datasets[0]
    assert subject == {"kind": "bars", "symbol": "PETR4", "timeframe": "D1"}
    assert rel_paths == [Path("ohlcv/PETR4/D1/2024.parquet")]


def test_bars_datasets_groups_every_file_of_one_series(tmp_path: Path) -> None:
    from tools.describe_dataset import bars_datasets

    for year in (2023, 2024):
        _write_parquet(
            tmp_path / "ohlcv" / "PETR4" / "D1" / f"{year}.parquet",
            {"time": [1], "open": [1.0]},
        )

    datasets = bars_datasets(tmp_path)

    assert len(datasets) == 1
    _, rel_paths = datasets[0]
    assert rel_paths == [
        Path("ohlcv/PETR4/D1/2023.parquet"),
        Path("ohlcv/PETR4/D1/2024.parquet"),
    ]


def test_bars_datasets_is_empty_for_a_lake_without_an_ohlcv_tree(
    tmp_path: Path,
) -> None:
    from tools.describe_dataset import bars_datasets

    _write_parquet(tmp_path / "lake" / "x.parquet", {"a": [1]})

    assert bars_datasets(tmp_path) == []
