import json
from pathlib import Path

import yaml

from tools.validate import check_stream_consistency


def create_minimal_stream_tree(tmp_path: Path) -> Path:
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)

    dummy_payload = stream_dir / "dummy.schema.json"
    dummy_payload.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "stream/dummy", "type": "object"}'
    )

    envelope = stream_dir / "envelope.schema.json"
    envelope.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "stream/envelope",
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["durable_test", "ephemeral_test"],
                    }
                },
            }
        )
    )

    topics = stream_dir / "topics.yaml"
    topics.write_text(
        yaml.dump(
            {
                "topics": {
                    "durable_test": {
                        "class": "durable",
                        "retention": {"duration": "P1D", "entries": 200000},
                        "backpressure": {"coalesce": False, "on_overflow": "lag"},
                        "payload_schema": "schema/stream/dummy.schema.json",
                        "replay": "unbounded",
                        "notes": "test",
                    },
                    "ephemeral_test": {
                        "class": "ephemeral",
                        "retention": {"duration": "PT1H", "entries": 1000},
                        "backpressure": {
                            "coalesce": True,
                            "coalesce_key": ["symbol"],
                            "on_overflow": "coalesce",
                        },
                        "payload_schema": "schema/stream/dummy.schema.json",
                        "replay": "retention_only",
                        "notes": "test",
                    },
                }
            }
        )
    )
    return schema_root


def test_consistency_durable_with_coalesce_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    data = yaml.safe_load(topics_file.read_text())
    data["topics"]["durable_test"]["backpressure"]["coalesce"] = True
    data["topics"]["durable_test"]["backpressure"]["coalesce_key"] = ["id"]
    topics_file.write_text(yaml.dump(data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "durable_test" in problems[0].reason
    assert "coalesce" in problems[0].reason.lower()


def test_consistency_ephemeral_with_unbounded_replay_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    data = yaml.safe_load(topics_file.read_text())
    data["topics"]["ephemeral_test"]["replay"] = "unbounded"
    topics_file.write_text(yaml.dump(data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "ephemeral_test" in problems[0].reason
    assert (
        "unbounded" in problems[0].reason.lower()
        or "retention_only" in problems[0].reason.lower()
    )


def test_consistency_topic_in_yaml_absent_from_envelope_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    envelope_file = schema_root / "stream" / "envelope.schema.json"
    env_data = json.loads(envelope_file.read_text())
    env_data["properties"]["topic"]["enum"] = ["ephemeral_test"]
    envelope_file.write_text(json.dumps(env_data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "durable_test" in problems[0].reason


def test_consistency_topic_in_envelope_absent_from_yaml_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    envelope_file = schema_root / "stream" / "envelope.schema.json"
    env_data = json.loads(envelope_file.read_text())
    env_data["properties"]["topic"]["enum"].append("ghost_topic")
    envelope_file.write_text(json.dumps(env_data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "ghost_topic" in problems[0].reason


def test_consistency_payload_schema_nonexistent_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    data = yaml.safe_load(topics_file.read_text())
    missing_path = "schema/stream/nonexistent.schema.json"
    data["topics"]["durable_test"]["payload_schema"] = missing_path
    topics_file.write_text(yaml.dump(data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "durable_test" in problems[0].reason
    assert missing_path in problems[0].reason


def test_consistency_coalesce_key_with_coalesce_false_fails(tmp_path: Path):
    schema_root = create_minimal_stream_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    data = yaml.safe_load(topics_file.read_text())
    data["topics"]["durable_test"]["backpressure"]["coalesce_key"] = ["forbidden_key"]
    topics_file.write_text(yaml.dump(data))

    problems = check_stream_consistency(schema_root)
    assert len(problems) == 1
    assert "durable_test" in problems[0].reason
    assert "coalesce_key" in problems[0].reason


def test_delivered_tree_stream_consistency():
    real_schema_root = Path(__file__).parent.parent / "schema"
    problems = check_stream_consistency(real_schema_root)
    assert problems == []
