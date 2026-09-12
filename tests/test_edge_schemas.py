import json
from pathlib import Path

import jsonschema
import pytest


def test_edge_health_schema_validates_and_rejects_missing_mt5_connected():
    schema_path = Path("schema/edge/common/health.schema.json")
    assert schema_path.is_file(), "schema/edge/common/health.schema.json must exist"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    valid_example = {
        "status": "ok",
        "schema_version": "1.0",
        "mt5_connected": True,
        "terminal_build": 4150,
    }
    validator.validate(valid_example)

    # terminal_build can also be null
    valid_example_null_build = {
        "status": "ok",
        "schema_version": "1.0",
        "mt5_connected": False,
        "terminal_build": None,
    }
    validator.validate(valid_example_null_build)

    invalid_example = {
        "status": "ok",
        "schema_version": "1.0",
        "terminal_build": 4150,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError) as excinfo:
        validator.validate(invalid_example)
    assert "mt5_connected" in str(excinfo.value)


def test_edge_error_schema_validates_vocabulary():
    schema_path = Path("schema/edge/common/error.schema.json")
    assert schema_path.is_file(), "schema/edge/common/error.schema.json must exist"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    valid_example = {
        "error": "MetaTrader 5 terminal is not initialized.",
        "code": "mt5_unavailable",
    }
    validator.validate(valid_example)

    invalid_example = {
        "error": "Something went wrong",
        "code": "unknown_unregistered_code_xyz",
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(invalid_example)
