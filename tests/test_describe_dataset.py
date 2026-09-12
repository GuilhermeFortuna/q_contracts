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

    parquet_files = sorted(root.rglob("*.parquet"))
    if not parquet_files:
        pytest.skip(f"No parquet files found in Q_MARKET_DATA_ROOT '{root}'")

    from tools.describe_dataset import manifest_from_directory

    sample_file = parquet_files[0]
    rel_path = sample_file.relative_to(root)

    subject = {
        "kind": "bars",
        "symbol": "PETR4",
        "timeframe": "D1",
    }

    manifest = manifest_from_directory(
        root=root,
        rel_paths=[rel_path],
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

    # 2. Manifest contents must reflect the file
    assert manifest["row_count"] > 0
    assert "start" in manifest["time_range"]
    assert "end" in manifest["time_range"]
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["path"] == rel_path.as_posix()
    assert manifest["files"][0]["size_bytes"] == sample_file.stat().st_size
    assert len(manifest["files"][0]["checksum"]) == 64  # sha256 hex digest length
    assert "fields" in manifest["arrow_schema"]
    assert len(manifest["arrow_schema"]["fields"]) >= 5


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
