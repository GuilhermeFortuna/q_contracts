import json
from pathlib import Path

import jsonschema
import pytest


def test_error_schema_validates_example_and_rejects_missing_message():
    schema_path = Path("schema/api/error.schema.json")
    assert schema_path.is_file(), "schema/api/error.schema.json must exist"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    valid_example = {
        "message": "Resource not found",
        "code": "NOT_FOUND",
        "details": {"resource_id": "123"},
    }
    validator.validate(valid_example)

    invalid_example = {
        "code": "NOT_FOUND",
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(invalid_example)
