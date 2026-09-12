import json
from pathlib import Path

import yaml

from tools.validate import check_stream_routing


def create_routing_stream_tree(tmp_path: Path) -> Path:
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    payloads_dir = stream_dir / "payloads"
    payloads_dir.mkdir(parents=True)

    dummy_payload = payloads_dir / "job-progress.schema.json"
    dummy_payload.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "stream/payloads/job-progress", "type": "object"}'
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
                        "enum": ["quotes", "jobs.progress"],
                    },
                    "key": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "timeframe": {"type": "string"},
                            "kind": {"type": "string"},
                            "job_id": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
            }
        )
    )

    topics = stream_dir / "topics.yaml"
    topics.write_text(
        yaml.dump(
            {
                "topics": {
                    "quotes": {
                        "class": "ephemeral",
                        "retention": {"duration": "PT1H", "entries": 100000},
                        "backpressure": {
                            "coalesce": True,
                            "coalesce_key": ["symbol"],
                            "on_overflow": "coalesce",
                        },
                        "payload_schema": "schema/stream/payloads/job-progress.schema.json",
                        "replay": "retention_only",
                        "notes": "test",
                    },
                    "jobs.progress": {
                        "class": "ephemeral",
                        "retention": {"duration": "P1D", "entries": 50000},
                        "backpressure": {
                            "coalesce": True,
                            "coalesce_key": ["kind", "job_id"],
                            "on_overflow": "coalesce",
                        },
                        "payload_schema": "schema/stream/payloads/job-progress.schema.json",
                        "replay": "retention_only",
                        "notes": "test",
                    },
                }
            }
        )
    )
    return schema_root


def test_routing_coalesce_key_not_in_envelope_key_fails(tmp_path: Path):
    schema_root = create_routing_stream_tree(tmp_path)
    envelope_file = schema_root / "stream" / "envelope.schema.json"
    env_data = json.loads(envelope_file.read_text())
    # Envelope key allows only timeframe, kind, job_id (symbol is disallowed)
    env_data["properties"]["key"]["properties"] = {
        "timeframe": {"type": "string"},
        "kind": {"type": "string"},
        "job_id": {"type": "string"},
    }
    envelope_file.write_text(json.dumps(env_data))

    problems = check_stream_routing(schema_root)
    assert len(problems) == 1
    assert "quotes" in problems[0].reason
    assert "symbol" in problems[0].reason


def test_routing_job_topic_naming_envelope_fails(tmp_path: Path):
    schema_root = create_routing_stream_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    topics_data = yaml.safe_load(topics_file.read_text())
    topics_data["topics"]["jobs.progress"][
        "payload_schema"
    ] = "schema/stream/envelope.schema.json"
    topics_file.write_text(yaml.dump(topics_data))

    problems = check_stream_routing(schema_root)
    assert len(problems) == 1
    assert "jobs.progress" in problems[0].reason


def test_delivered_tree_stream_routing():
    real_schema_root = Path(__file__).parent.parent / "schema"
    problems = check_stream_routing(real_schema_root)
    assert problems == []
