import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).parent.parent / "schema" / "stream" / "envelope.schema.json"
)
EXAMPLES_DIR = Path(__file__).parent.parent / "schema" / "stream" / "examples"


@pytest.fixture
def envelope_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_envelope_validates_arrow_example(envelope_schema: dict) -> None:
    data = json.loads(
        (EXAMPLES_DIR / "envelope-arrow.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(envelope_schema)
    errors = list(validator.iter_errors(data))
    assert errors == []


def test_envelope_validates_control_example(envelope_schema: dict) -> None:
    data = json.loads(
        (EXAMPLES_DIR / "envelope-control.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(envelope_schema)
    errors = list(validator.iter_errors(data))
    assert errors == []


@pytest.mark.parametrize("missing_field", ["seq", "epoch", "topic"])
def test_envelope_mutants_fail_with_field_named(
    envelope_schema: dict, missing_field: str
) -> None:
    data = json.loads(
        (EXAMPLES_DIR / "envelope-arrow.json").read_text(encoding="utf-8")
    )
    del data[missing_field]
    validator = jsonschema.Draft202012Validator(envelope_schema)
    errors = list(validator.iter_errors(data))
    assert len(errors) >= 1
    # Ensure failure explicitly names the missing field
    assert any(missing_field in err.message for err in errors)
