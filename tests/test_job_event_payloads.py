import json
from pathlib import Path

import jsonschema

PAYLOADS_DIR = Path(__file__).parent.parent / "schema" / "stream" / "payloads"
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "stream" / "examples"


def load_payload_schema(name: str) -> dict:
    path = PAYLOADS_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_job_terminal_status_error_rejected():
    schema = load_payload_schema("job-terminal")
    payload = {
        "kind": "backtest",
        "job_id": "job-123",
        "status": "error",
        "finished_at": "2026-09-12T10:00:00Z",
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert len(errors) >= 1
    assert any("status" in str(err.path) or "status" in err.message for err in errors)


def test_job_progress_out_of_bounds_rejected():
    schema = load_payload_schema("job-progress")
    payload = {
        "kind": "backtest",
        "job_id": "job-123",
        "status": "running",
        "progress": 1.5,
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert len(errors) >= 1
    assert any(
        "progress" in str(err.path) or "progress" in err.message for err in errors
    )


def test_job_progress_null_with_message_accepted():
    schema = load_payload_schema("job-progress")
    payload = {
        "kind": "neural_training",
        "job_id": "job-456",
        "status": "running",
        "progress": None,
        "message": "Epoch 3/10",
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_job_kind_job_rejected_and_optimization_accepted():
    terminal_schema = load_payload_schema("job-terminal")
    progress_schema = load_payload_schema("job-progress")

    for schema in (terminal_schema, progress_schema):
        bad_payload = {
            "kind": "job",
            "job_id": "job-789",
            "status": "completed" if schema == terminal_schema else "running",
            "finished_at": "2026-09-12T10:00:00Z",
            "progress": 0.5,
        }
        if schema == terminal_schema:
            bad_payload.pop("progress")
        else:
            bad_payload.pop("finished_at")

        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(bad_payload))
        assert (
            len(errors) >= 1
        ), f"Expected kind: 'job' to be rejected for {schema['$id']}"

        good_payload = dict(bad_payload)
        good_payload["kind"] = "optimization"
        errors = list(validator.iter_errors(good_payload))
        assert (
            errors == []
        ), f"Expected kind: 'optimization' to be accepted for {schema['$id']}"


def test_job_progress_status_completed_rejected():
    schema = load_payload_schema("job-progress")
    payload = {
        "kind": "backtest",
        "job_id": "job-123",
        "status": "completed",
        "progress": 1.0,
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert len(errors) >= 1
    assert any("status" in str(err.path) or "status" in err.message for err in errors)


def test_job_examples_validate():
    progress_schema = load_payload_schema("job-progress")
    terminal_schema = load_payload_schema("job-terminal")

    progress_example = json.loads(
        (EXAMPLES_DIR / "job-progress.json").read_text(encoding="utf-8")
    )
    terminal_example = json.loads(
        (EXAMPLES_DIR / "job-terminal.json").read_text(encoding="utf-8")
    )

    validator_prog = jsonschema.Draft202012Validator(progress_schema)
    assert list(validator_prog.iter_errors(progress_example)) == []

    validator_term = jsonschema.Draft202012Validator(terminal_schema)
    assert list(validator_term.iter_errors(terminal_example)) == []
