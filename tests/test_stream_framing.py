import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "stream" / "framing.schema.json"
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "stream" / "examples"


@pytest.fixture
def framing_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_framing_valid_example(framing_schema: dict):
    example = json.loads(
        (EXAMPLES_DIR / "websocket-binary-header.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(framing_schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert example["payload_length"] == 8192
    assert example["payload_kind"] == "arrow_ipc"
    assert example["routing_key"] == "WIN$N:M1"


@pytest.mark.parametrize(
    "missing_field",
    [
        "topic",
        "schema_major",
        "seq",
        "epoch",
        "producer_id",
        "origin_ts",
        "payload_kind",
        "payload_schema",
        "payload_length",
    ],
)
def test_framing_missing_required_field_fails(framing_schema: dict, missing_field: str):
    example = json.loads(
        (EXAMPLES_DIR / "websocket-binary-header.json").read_text(encoding="utf-8")
    )
    del example[missing_field]
    validator = jsonschema.Draft202012Validator(framing_schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_framing_negative_payload_length_fails(framing_schema: dict):
    example = json.loads(
        (EXAMPLES_DIR / "websocket-binary-header.json").read_text(encoding="utf-8")
    )
    example["payload_length"] = -1
    validator = jsonschema.Draft202012Validator(framing_schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1


def test_framing_invalid_payload_kind_fails(framing_schema: dict):
    example = json.loads(
        (EXAMPLES_DIR / "websocket-binary-header.json").read_text(encoding="utf-8")
    )
    example["payload_kind"] = "raw_bytes"  # only arrow_ipc or control allowed
    validator = jsonschema.Draft202012Validator(framing_schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
