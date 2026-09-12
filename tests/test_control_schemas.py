import json
from pathlib import Path

import jsonschema
import pytest

CONTROL_SCHEMA_DIR = Path(__file__).parent.parent / "schema" / "stream" / "control"


def load_control_schema(name: str) -> dict:
    path = CONTROL_SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_subscribed_valid_example():
    schema = load_control_schema("subscribed")
    example = {
        "topics": {
            "orders": {
                "cursor": "1710000000000-0",
                "epoch": "outbox-epoch-42",
                "last_seq": 105,
            },
            "fills": {
                "cursor": "1710000001000-0",
                "epoch": "outbox-epoch-42",
                "last_seq": 88,
            },
        }
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []


def test_subscribed_missing_epoch_fails():
    schema = load_control_schema("subscribed")
    example = {
        "topics": {
            "orders": {
                "cursor": "1710000000000-0",
                # "epoch" missing
                "last_seq": 105,
            }
        }
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("epoch" in err.message for err in errors)


def test_subscribed_missing_last_seq_fails():
    schema = load_control_schema("subscribed")
    example = {
        "topics": {
            "orders": {
                "cursor": "1710000000000-0",
                "epoch": "outbox-epoch-42",
                # "last_seq" missing
            }
        }
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("last_seq" in err.message for err in errors)


def test_lagging_missing_from_seq_fails():
    schema = load_control_schema("lagging")
    example = {
        "topic": "bars.completed",
        # "from_seq" missing
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("from_seq" in err.message for err in errors)


def test_subscribe_with_cursors_valid():
    schema = load_control_schema("subscribe")
    example_path = (
        Path(__file__).parent.parent
        / "schema"
        / "stream"
        / "examples"
        / "subscribe-with-cursors.json"
    )
    example = json.loads(example_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []
    assert "cursors" in example
    assert example["cursors"]["orders"] == "1710000000000-0"


def test_subscription_rejected_valid_example():
    schema = load_control_schema("subscription-rejected")
    example_path = (
        Path(__file__).parent.parent
        / "schema"
        / "stream"
        / "examples"
        / "subscription-rejected.json"
    )
    example = json.loads(example_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []


@pytest.mark.parametrize("missing_field", ["topics", "reason"])
def test_subscription_rejected_missing_required_field_fails(missing_field: str):
    schema = load_control_schema("subscription-rejected")
    example = {
        "topics": ["invalid.topic"],
        "reason": "Topic not found",
        "code": "unknown_topic",
    }
    del example[missing_field]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any(missing_field in err.message for err in errors)


def test_subscription_rejected_empty_topics_fails():
    schema = load_control_schema("subscription-rejected")
    example = {
        "topics": [],
        "reason": "Topic not found",
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1


def test_all_control_schemas_exist_and_validate():
    names = [
        "subscribe",
        "subscribed",
        "cursor-expired",
        "lagging",
        "epoch-changed",
        "subscription-rejected",
    ]
    for name in names:
        schema = load_control_schema(name)
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema["$id"] == f"stream/control/{name}"
