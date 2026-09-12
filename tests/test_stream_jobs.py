import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_DIR = Path(__file__).parent.parent / "schema" / "stream" / "jobs"
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "stream" / "examples"


def load_job_schema(name: str) -> dict:
    path = SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_job_progress_valid_example():
    schema = load_job_schema("progress")
    example = json.loads(
        (EXAMPLES_DIR / "job-progress.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert example["status"] == "running"
    assert 0.0 <= example["progress"] <= 1.0


@pytest.mark.parametrize("missing_field", ["job_id", "status", "progress"])
def test_job_progress_missing_required_field_fails(missing_field: str):
    schema = load_job_schema("progress")
    example = json.loads(
        (EXAMPLES_DIR / "job-progress.json").read_text(encoding="utf-8")
    )
    del example[missing_field]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_job_progress_invalid_status_fails():
    schema = load_job_schema("progress")
    example = json.loads(
        (EXAMPLES_DIR / "job-progress.json").read_text(encoding="utf-8")
    )
    example["status"] = "unknown_status"
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1


def test_job_progress_out_of_range_progress_fails():
    schema = load_job_schema("progress")
    example = json.loads(
        (EXAMPLES_DIR / "job-progress.json").read_text(encoding="utf-8")
    )
    example["progress"] = 1.5
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1


def test_job_terminal_valid_example():
    schema = load_job_schema("terminal")
    example = json.loads(
        (EXAMPLES_DIR / "job-terminal.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert example["status"] == "completed"


@pytest.mark.parametrize("missing_field", ["job_id", "status"])
def test_job_terminal_missing_required_field_fails(missing_field: str):
    schema = load_job_schema("terminal")
    example = json.loads(
        (EXAMPLES_DIR / "job-terminal.json").read_text(encoding="utf-8")
    )
    del example[missing_field]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_job_terminal_invalid_status_fails():
    schema = load_job_schema("terminal")
    example = json.loads(
        (EXAMPLES_DIR / "job-terminal.json").read_text(encoding="utf-8")
    )
    example["status"] = "running"  # running is not terminal!
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
