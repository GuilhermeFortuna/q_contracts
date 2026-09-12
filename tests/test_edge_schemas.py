import json
from pathlib import Path

import jsonschema
import pytest
import referencing

EXECUTION_SCHEMA_DIR = Path("schema/edge/execution")
EXAMPLES_DIR = Path("schema/edge/examples")


def load_execution_validator(schema_filename: str) -> jsonschema.Draft202012Validator:
    schema_path = EXECUTION_SCHEMA_DIR / schema_filename
    assert schema_path.is_file(), f"{schema_path} must exist"
    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))

    resources = []
    for file in EXECUTION_SCHEMA_DIR.glob("*.schema.json"):
        s = json.loads(file.read_text(encoding="utf-8"))
        res = referencing.Resource.from_contents(s)
        resources.append((file.name, res))
        if "$id" in s:
            resources.append((s["$id"], res))
            resources.append((f"{s['$id']}.schema.json", res))
    registry = referencing.Registry().with_resources(resources)
    return jsonschema.Draft202012Validator(schema_data, registry=registry)


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


def test_submit_request_validates_and_rejects_missing_intent_id():
    validator = load_execution_validator("submit-request.schema.json")
    valid_example = {
        "intent_id": "018f6c38-89ab-7000-8000-000000000001",
        "order": {
            "symbol": "PETR4",
            "volume": 100.0,
            "side": "buy",
        },
    }
    validator.validate(valid_example)

    invalid_example = {
        "order": {
            "symbol": "PETR4",
            "volume": 100.0,
            "side": "buy",
        }
    }
    with pytest.raises(jsonschema.exceptions.ValidationError) as excinfo:
        validator.validate(invalid_example)
    assert "intent_id" in str(excinfo.value)


def test_submit_outcome_three_legal_outcomes_validate():
    validator = load_execution_validator("submit-outcome.schema.json")

    accepted = {
        "outcome": "accepted",
        "order_ticket": 12345678,
        "retcode": 10009,
    }
    validator.validate(accepted)

    rejected = {
        "outcome": "rejected",
        "retcode": 10013,
        "reason": "Invalid volume",
    }
    validator.validate(rejected)

    indeterminate = {
        "outcome": "indeterminate",
        "reason": "Transport timeout waiting for MT5 response",
    }
    validator.validate(indeterminate)


def test_submit_outcome_rejects_duplicate_intent_or_other_outcome():
    validator = load_execution_validator("submit-outcome.schema.json")

    # duplicate_intent is an error response, not a submit outcome
    duplicate_intent = {
        "outcome": "duplicate_intent",
        "reason": "Order with intent already processed",
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(duplicate_intent)

    unknown_outcome = {
        "outcome": "executed",
        "order_ticket": 12345678,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(unknown_outcome)


def test_lookup_outcome_four_outcomes_and_closes_intent():
    validator = load_execution_validator("lookup-outcome.schema.json")

    filled = {
        "outcome": "filled",
        "deals": [
            {
                "ticket": 98765,
                "order_ticket": 12345678,
                "symbol": "PETR4",
                "volume": 100.0,
                "price": 41.50,
            }
        ],
        "closes_intent": True,
    }
    validator.validate(filled)

    rejected = {
        "outcome": "rejected",
        "retcode": 10013,
        "closes_intent": True,
    }
    validator.validate(rejected)

    not_found = {
        "outcome": "not_found",
        "closes_intent": True,
    }
    validator.validate(not_found)

    unavailable = {
        "outcome": "unavailable",
        "reason": "Terminal deal history buffer unavailable",
        "closes_intent": False,
    }
    validator.validate(unavailable)

    # Invalid: not_found claiming closes_intent=False
    invalid_not_found = {
        "outcome": "not_found",
        "closes_intent": False,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(invalid_not_found)

    # Invalid: unavailable claiming closes_intent=True
    invalid_unavailable = {
        "outcome": "unavailable",
        "reason": "Terminal deal history buffer unavailable",
        "closes_intent": True,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(invalid_unavailable)


def test_quote_response_requires_age_ms():
    validator = load_execution_validator("quote-response.schema.json")

    valid_example = {
        "symbol": "PETR4",
        "bid": 41.06,
        "ask": 41.08,
        "last": 41.07,
        "time_msc": 1710000000000,
        "age_ms": 15,
    }
    validator.validate(valid_example)

    missing_age = {
        "symbol": "PETR4",
        "bid": 41.06,
        "ask": 41.08,
        "last": 41.07,
        "time_msc": 1710000000000,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError) as excinfo:
        validator.validate(missing_age)
    assert "age_ms" in str(excinfo.value)


def test_all_six_operations_have_examples_that_validate():
    operation_schemas = [
        ("quote-request.json", "quote-request.schema.json"),
        ("quote-response.json", "quote-response.schema.json"),
        ("check-request.json", "check-request.schema.json"),
        ("check-response.json", "check-response.schema.json"),
        ("submit-request.json", "submit-request.schema.json"),
        ("submit-outcome-accepted.json", "submit-outcome.schema.json"),
        ("submit-outcome-rejected.json", "submit-outcome.schema.json"),
        ("submit-outcome-indeterminate.json", "submit-outcome.schema.json"),
        ("lookup-request.json", "lookup-request.schema.json"),
        ("lookup-outcome-filled.json", "lookup-outcome.schema.json"),
        ("lookup-outcome-rejected.json", "lookup-outcome.schema.json"),
        ("lookup-outcome-not-found.json", "lookup-outcome.schema.json"),
        ("lookup-outcome-unavailable.json", "lookup-outcome.schema.json"),
        ("positions-request.json", "positions-request.schema.json"),
        ("positions-response.json", "positions-response.schema.json"),
        ("deals-request.json", "deals-request.schema.json"),
        ("deals-response.json", "deals-response.schema.json"),
    ]
    for example_file, schema_file in operation_schemas:
        validator = load_execution_validator(schema_file)
        example_path = EXAMPLES_DIR / example_file
        assert example_path.is_file(), f"{example_path} must exist"
        data = json.loads(example_path.read_text(encoding="utf-8"))
        validator.validate(data)
