import json
from pathlib import Path

import jsonschema
import referencing

STREAM_DIR = Path(__file__).parent.parent / "schema" / "stream"
REPLAY_DIR = STREAM_DIR / "replay"
EXAMPLES_DIR = STREAM_DIR / "examples"


def load_replay_validator(name: str) -> jsonschema.Draft202012Validator:
    schema_path = REPLAY_DIR / f"{name}.schema.json"
    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))

    resources = []
    for file in STREAM_DIR.rglob("*.schema.json"):
        s = json.loads(file.read_text(encoding="utf-8"))
        res = referencing.Resource.from_contents(s)
        resources.append((file.name, res))
        resources.append((file.as_posix(), res))
        resources.append((f"../{file.name}", res))
        if "$id" in s:
            resources.append((s["$id"], res))
            resources.append((f"{s['$id']}.schema.json", res))
    registry = referencing.Registry().with_resources(resources)
    return jsonschema.Draft202012Validator(schema_data, registry=registry)


def make_valid_envelope(topic: str, seq: int) -> dict:
    return {
        "topic": topic,
        "schema_major": 1,
        "seq": seq,
        "epoch": "epoch-01",
        "producer_id": "test-producer",
        "origin_ts": "2026-09-12T10:00:00Z",
        "payload_kind": "control",
        "payload_schema": "schema/stream/control/subscribe.schema.json",
        "payload": {"topics": [topic]},
    }


def test_history_page_with_two_envelopes_and_null_next_seq_validates():
    validator = load_replay_validator("history-page")
    payload = {
        "topic": "orders",
        "epoch": "outbox-epoch-42",
        "entries": [
            make_valid_envelope("orders", 101),
            make_valid_envelope("orders", 102),
        ],
        "next_seq": None,
    }
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_history_page_entries_lacking_seq_rejected():
    validator = load_replay_validator("history-page")
    bad_envelope = make_valid_envelope("orders", 101)
    del bad_envelope["seq"]
    payload = {
        "topic": "orders",
        "epoch": "outbox-epoch-42",
        "entries": [bad_envelope],
        "next_seq": None,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) >= 1
    assert any("seq" in err.message for err in errors)


def test_history_expired_requires_requested_from_seq():
    validator = load_replay_validator("history-expired")
    payload = {
        "topic": "orders",
        "oldest_available_seq": 100,
    }
    errors = list(validator.iter_errors(payload))
    assert len(errors) >= 1
    assert any("requested_from_seq" in err.message for err in errors)

    valid_payload = {
        "topic": "orders",
        "requested_from_seq": 50,
        "oldest_available_seq": 100,
    }
    assert list(validator.iter_errors(valid_payload)) == []


def test_latest_response_keyed_symbol_validates():
    validator = load_replay_validator("latest")
    payload = {
        "topic": "quotes",
        "entries": {
            "WINZ25": make_valid_envelope("quotes", 501),
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_watermark_validates():
    validator = load_replay_validator("watermark")
    payload = {"jobs.terminal": {"epoch": "e1", "seq": 42}}
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_all_four_replay_schemas_exist_and_validate():
    names = ["history-page", "history-expired", "latest", "watermark"]
    for name in names:
        path = REPLAY_DIR / f"{name}.schema.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(data)
        assert data["$id"] == f"stream/replay/{name}"


def test_replay_examples_validate():
    names = ["history-page", "history-expired", "latest", "watermark"]
    for name in names:
        validator = load_replay_validator(name)
        example_path = EXAMPLES_DIR / f"{name}.json"
        data = json.loads(example_path.read_text(encoding="utf-8"))
        errors = list(validator.iter_errors(data))
        assert errors == [], f"Example {name}.json failed validation: {errors}"


def test_execution_snapshot_validates_example():
    validator = load_replay_validator("execution-snapshot")
    example_path = EXAMPLES_DIR / "execution-snapshot.json"
    assert example_path.is_file()
    data = json.loads(example_path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(data))
    assert errors == []


def test_execution_snapshot_watermark_missing_topic_fails():
    validator = load_replay_validator("execution-snapshot")
    example_path = EXAMPLES_DIR / "execution-snapshot.json"
    data = json.loads(example_path.read_text(encoding="utf-8"))
    for topic in [
        "decisions",
        "orders",
        "fills",
        "risk",
        "ledger",
        "deployments",
    ]:
        bad = json.loads(json.dumps(data))
        del bad["watermark"][topic]
        errors = list(validator.iter_errors(bad))
        assert len(errors) >= 1
        assert any(
            "watermark" in str(err.path) or topic in err.message for err in errors
        )


def test_snapshot_entity_shapes_equal_payload_shapes():
    from tools.validate import check_execution_payloads

    schema_root = STREAM_DIR.parent
    problems = check_execution_payloads(schema_root)
    assert problems == []
