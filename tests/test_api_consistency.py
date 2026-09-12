import json
from pathlib import Path

import yaml

from tools.validate import check_api_consistency


def create_minimal_api_tree(tmp_path: Path) -> Path:
    schema_root = tmp_path / "schema"
    api_dir = schema_root / "api"
    arrow_dir = api_dir / "arrow"
    stream_dir = schema_root / "stream"
    arrow_dir.mkdir(parents=True)
    stream_dir.mkdir(parents=True)

    # Valid error schema
    error_file = api_dir / "error.schema.json"
    error_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "api/error",
                "type": "object",
                "required": ["message"],
                "properties": {"message": {"type": "string"}},
            }
        )
    )

    # Valid arrow schema
    bars_file = arrow_dir / "bars.schema.json"
    bars_file.write_text(
        json.dumps(
            {
                "name": "bars",
                "fields": [
                    {
                        "name": "time",
                        "type": "timestamp[us]",
                        "nullable": False,
                        "tz": "naive-wallclock-America/Sao_Paulo",
                    },
                    {
                        "name": "close",
                        "type": "float64",
                        "nullable": False,
                    },
                ],
            }
        )
    )

    # Valid OpenAPI document referencing error.schema.json for failing operation
    openapi_file = api_dir / "openapi.yaml"
    openapi_file.write_text(
        yaml.dump(
            {
                "openapi": "3.1.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {
                    "/items": {
                        "get": {
                            "operationId": "list_items",
                            "responses": {
                                "200": {"description": "OK"},
                                "500": {
                                    "description": "Error",
                                    "content": {
                                        "application/json": {
                                            "schema": {"$ref": "error.schema.json"}
                                        }
                                    },
                                },
                            },
                        }
                    }
                },
            }
        )
    )

    # Valid topics.yaml and envelope.schema.json
    envelope_file = stream_dir / "envelope.schema.json"
    envelope_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "stream/envelope",
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": ["bars.completed"]}},
            }
        )
    )

    topics_file = stream_dir / "topics.yaml"
    topics_file.write_text(
        yaml.dump(
            {
                "topics": {
                    "bars.completed": {
                        "class": "ephemeral",
                        "retention": {"duration": "P1D", "entries": 1000},
                        "backpressure": {
                            "coalesce": False,
                            "on_overflow": "lag",
                        },
                        "payload_schema": "schema/api/arrow/bars.schema.json",
                        "replay": "retention_only",
                        "notes": "Completed bars",
                    }
                }
            }
        )
    )

    return schema_root


def test_arrow_field_lacking_type_fails(tmp_path: Path):
    schema_root = create_minimal_api_tree(tmp_path)
    bars_file = schema_root / "api" / "arrow" / "bars.schema.json"
    data = json.loads(bars_file.read_text())
    del data["fields"][1]["type"]
    bars_file.write_text(json.dumps(data))

    problems = check_api_consistency(schema_root)
    assert len(problems) == 1
    assert "close" in problems[0].reason
    assert "type" in problems[0].reason.lower()


def test_arrow_timestamp_lacking_tz_fails(tmp_path: Path):
    schema_root = create_minimal_api_tree(tmp_path)
    bars_file = schema_root / "api" / "arrow" / "bars.schema.json"
    data = json.loads(bars_file.read_text())
    del data["fields"][0]["tz"]
    bars_file.write_text(json.dumps(data))

    problems = check_api_consistency(schema_root)
    assert len(problems) == 1
    assert "time" in problems[0].reason
    assert "tz" in problems[0].reason.lower()


def test_operation_failure_response_not_referencing_error_schema_fails(
    tmp_path: Path,
):
    schema_root = create_minimal_api_tree(tmp_path)
    openapi_file = schema_root / "api" / "openapi.yaml"
    data = yaml.safe_load(openapi_file.read_text())
    # Modify the 500 response to point to another schema instead of error.schema.json
    data["paths"]["/items"]["get"]["responses"]["500"]["content"]["application/json"][
        "schema"
    ]["$ref"] = "other_error.schema.json"
    openapi_file.write_text(yaml.dump(data))

    problems = check_api_consistency(schema_root)
    assert len(problems) == 1
    assert "list_items" in problems[0].reason or "/items" in problems[0].reason
    assert "error.schema.json" in problems[0].reason


def test_topics_arrow_payload_schema_not_resolving_fails(tmp_path: Path):
    schema_root = create_minimal_api_tree(tmp_path)
    topics_file = schema_root / "stream" / "topics.yaml"
    data = yaml.safe_load(topics_file.read_text())
    data["topics"]["bars.completed"][
        "payload_schema"
    ] = "schema/api/arrow/nonexistent.schema.json"
    topics_file.write_text(yaml.dump(data))

    problems = check_api_consistency(schema_root)
    assert len(problems) == 1
    assert "bars.completed" in problems[0].reason
    assert (
        "schema/api/arrow" in problems[0].reason
        or "resolve" in problems[0].reason.lower()
    )


def test_valid_repo_tree_has_no_api_consistency_problems():
    problems = check_api_consistency(Path("schema"))
    assert problems == []
