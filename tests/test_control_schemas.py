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
        "type": "subscribed",
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
        },
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors == []


def test_subscribed_missing_epoch_fails():
    schema = load_control_schema("subscribed")
    example = {
        "type": "subscribed",
        "topics": {
            "orders": {
                "cursor": "1710000000000-0",
                # "epoch" missing
                "last_seq": 105,
            }
        },
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("epoch" in err.message for err in errors)


def test_subscribed_missing_last_seq_fails():
    schema = load_control_schema("subscribed")
    example = {
        "type": "subscribed",
        "topics": {
            "orders": {
                "cursor": "1710000000000-0",
                "epoch": "outbox-epoch-42",
                # "last_seq" missing
            }
        },
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("last_seq" in err.message for err in errors)


def test_lagging_missing_from_seq_fails():
    schema = load_control_schema("lagging")
    example = {
        "type": "lagging",
        "topic": "bars.completed",
        # "from_seq" missing
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("from_seq" in err.message for err in errors)


def test_all_control_schemas_exist_and_validate():
    names = [
        "subscribe",
        "subscribed",
        "cursor-expired",
        "lagging",
        "epoch-changed",
        "rejected",
    ]
    for name in names:
        schema = load_control_schema(name)
        jsonschema.Draft202012Validator.check_schema(schema)
        assert schema["$id"] == f"stream/control/{name}"


def test_subscribe_pre_task_validates():
    schema = load_control_schema("subscribe")
    example = {"topics": ["quotes", "bars.forming"]}
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(example)) == []


def test_subscribe_with_cursors_validates():
    schema = load_control_schema("subscribe")
    example = {"topics": ["quotes"], "cursors": {"quotes": "1710000000000-0"}}
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(example)) == []


def test_rejected_frame_validates():
    schema = load_control_schema("rejected")
    example = {"type": "rejected", "reason": "unknown_topic", "topic": "nope"}
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(example)) == []


def test_rejected_frame_invalid_reason_rejected():
    schema = load_control_schema("rejected")
    example = {"type": "rejected", "reason": "other"}
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert len(errors) >= 1
    assert any("reason" in str(err.path) or "reason" in err.message for err in errors)


SERVER_FRAME_TYPES = {
    "subscribed": "subscribed",
    "rejected": "rejected",
    "cursor-expired": "cursor_expired",
    "lagging": "lagging",
    "epoch-changed": "epoch_changed",
}


def test_server_control_frames_require_a_type_discriminator():
    """Without a discriminator, clients must guess a frame's kind from which keys are present."""
    for name, frame_type in SERVER_FRAME_TYPES.items():
        schema = load_control_schema(name)
        assert "type" in schema["required"], name
        assert schema["properties"]["type"] == {
            "const": frame_type,
            "description": schema["properties"]["type"]["description"],
        }, name


def test_control_frame_without_type_fails():
    schema = load_control_schema("lagging")
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors({"topic": "bars.completed", "from_seq": 3}))
    assert (
        list(
            validator.iter_errors(
                {"type": "lagging", "topic": "bars.completed", "from_seq": 3}
            )
        )
        == []
    )


def test_control_frame_types_are_distinct_and_absent_from_the_envelope():
    """A text frame is a control frame exactly when it carries `type`; envelopes never do."""
    assert len(set(SERVER_FRAME_TYPES.values())) == len(SERVER_FRAME_TYPES)
    envelope = json.loads(
        (CONTROL_SCHEMA_DIR.parent / "envelope.schema.json").read_text(encoding="utf-8")
    )
    assert "type" not in envelope["properties"]
    assert envelope.get("additionalProperties") is False


def test_rejected_frame_names_an_invalid_client_frame():
    """A malformed request is not a schema-major mismatch and must not be reported as one."""
    schema = load_control_schema("rejected")
    validator = jsonschema.Draft202012Validator(schema)
    assert (
        list(
            validator.iter_errors(
                {"type": "rejected", "reason": "invalid_frame", "detail": "bad cursor"}
            )
        )
        == []
    )


def test_rejected_example_validates():
    schema = load_control_schema("rejected")
    example = json.loads(
        (CONTROL_SCHEMA_DIR.parent / "examples" / "rejected.json").read_text(
            encoding="utf-8"
        )
    )
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(example)) == []
