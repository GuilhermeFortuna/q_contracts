import json
from pathlib import Path

import jsonschema
import pytest
import referencing

SCHEMA_DIR = Path(__file__).parent.parent / "schema" / "stream" / "replay"
STREAM_DIR = Path(__file__).parent.parent / "schema" / "stream"
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "stream" / "examples"


def load_replay_schema(name: str) -> dict:
    path = SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def history_validator() -> jsonschema.Draft202012Validator:
    schema = load_replay_schema("history")
    envelope_schema = json.loads(
        (STREAM_DIR / "envelope.schema.json").read_text(encoding="utf-8")
    )
    resource = referencing.Resource.from_contents(
        envelope_schema, default_specification=referencing.jsonschema.DRAFT202012
    )
    registry = referencing.Registry().with_resource(resource.id(), resource)
    return jsonschema.Draft202012Validator(schema, registry=registry)


def test_replay_history_valid_example(
    history_validator: jsonschema.Draft202012Validator,
):
    example = json.loads(
        (EXAMPLES_DIR / "replay-history.json").read_text(encoding="utf-8")
    )
    errors = list(history_validator.iter_errors(example))
    assert errors == []
    assert len(example["entries"]) == 2
    assert example["from_seq"] <= example["to_seq"]


@pytest.mark.parametrize(
    "missing_field", ["topic", "epoch", "from_seq", "to_seq", "entries"]
)
def test_replay_history_missing_required_field_fails(
    history_validator: jsonschema.Draft202012Validator, missing_field: str
):
    example = json.loads(
        (EXAMPLES_DIR / "replay-history.json").read_text(encoding="utf-8")
    )
    del example[missing_field]
    errors = list(history_validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_replay_latest_valid_example():
    schema = load_replay_schema("latest")
    example = json.loads(
        (EXAMPLES_DIR / "replay-latest.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert example["topic"] == "quotes"
    assert example["seq"] == 4501


@pytest.mark.parametrize("missing_field", ["topic", "epoch", "seq", "payload"])
def test_replay_latest_missing_required_field_fails(missing_field: str):
    schema = load_replay_schema("latest")
    example = json.loads(
        (EXAMPLES_DIR / "replay-latest.json").read_text(encoding="utf-8")
    )
    del example[missing_field]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_replay_watermark_valid_example():
    schema = load_replay_schema("watermark")
    example = json.loads(
        (EXAMPLES_DIR / "replay-watermark.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert "watermarks" in example
    assert example["watermarks"]["orders"] == 1205


def test_replay_watermark_missing_watermarks_fails():
    schema = load_replay_schema("watermark")
    example = {"epoch": "outbox-epoch-42"}
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("watermarks" in err.message for err in errors)


def test_replay_watermark_negative_seq_fails():
    schema = load_replay_schema("watermark")
    example = {
        "watermarks": {
            "orders": -5,
        }
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
