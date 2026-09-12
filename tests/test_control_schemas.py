import json
from pathlib import Path

import jsonschema

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


def test_all_five_control_schemas_exist_and_validate():
    names = ["subscribe", "subscribed", "cursor-expired", "lagging", "epoch-changed"]
    for name in names:
        schema = load_control_schema(name)
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema["$id"] == f"stream/control/{name}"
