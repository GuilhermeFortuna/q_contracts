import copy
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).parent.parent / "schema" / "catalog" / "dataset-manifest.schema.json"
)
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "catalog" / "examples"


@pytest.fixture
def manifest_schema() -> dict:
    assert (
        SCHEMA_PATH.is_file()
    ), f"dataset-manifest.schema.json must exist at {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def two_file_manifest() -> dict:
    example_path = EXAMPLES_DIR / "manifest-bars-two-files.json"
    assert (
        example_path.is_file()
    ), f"manifest-bars-two-files.json must exist at {example_path}"
    return json.loads(example_path.read_text(encoding="utf-8"))


def test_two_file_manifest_validates(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(two_file_manifest))
    assert errors == [], f"Validation errors: {[e.message for e in errors]}"


@pytest.mark.parametrize(
    "missing_top_field",
    ["files", "arrow_schema", "row_count", "time_range", "published_at"],
)
def test_manifest_missing_top_level_required_field_fails_with_field_named(
    manifest_schema: dict, two_file_manifest: dict, missing_top_field: str
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    del mutant[missing_top_field]
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert len(errors) >= 1
    assert any(
        missing_top_field in err.message for err in errors
    ), f"Missing '{missing_top_field}' error not found in: {[e.message for e in errors]}"


def test_manifest_missing_file_checksum_fails_with_checksum_named(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    del mutant["files"][0]["checksum"]
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert len(errors) >= 1
    assert any(
        "checksum" in err.message for err in errors
    ), f"Missing 'checksum' error not found in: {[e.message for e in errors]}"


def test_file_entry_absolute_path_fails(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    mutant["files"][0]["path"] = "/abs/x.parquet"
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert len(errors) >= 1


def test_file_entry_parent_dir_segment_fails(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    mutant["files"][0]["path"] = "a/../b.parquet"
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert len(errors) >= 1


def test_file_entry_valid_relative_path_passes(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    mutant["files"][0]["path"] = "bars/2024.parquet"
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert errors == []


def test_dataset_id_path_like_fails(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    mutant["dataset_id"] = "WINFUT/M15/2024"
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert len(errors) >= 1


def test_dataset_id_uuid_form_passes(
    manifest_schema: dict, two_file_manifest: dict
) -> None:
    mutant = copy.deepcopy(two_file_manifest)
    mutant["dataset_id"] = "123e4567-e89b-12d3-a456-426614174000"
    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(mutant))
    assert errors == []
