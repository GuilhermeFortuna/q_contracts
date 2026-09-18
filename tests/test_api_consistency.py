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


def test_valid_repo_tree_has_no_idempotency_problems():
    from tools.validate import check_idempotency

    problems = check_idempotency(Path("schema"))
    assert problems == []


def test_idempotency_policy_values_and_replay_rules():
    idemp_path = Path("schema/api/idempotency.yaml")
    assert idemp_path.is_file()
    data = yaml.safe_load(idemp_path.read_text(encoding="utf-8"))

    assert data["header"] == "Idempotency-Key"
    assert data["key_format"] == "uuid"
    assert data["ttl"] == "PT24H"

    # Replay rule specifies 24 hours and conflicting key refusal
    replay_rule = data["replay_rule"]["description"]
    assert "24 hours" in replay_rule or "PT24H" in replay_rule
    assert "idempotency_key_reused" in replay_rule
    assert "idempotency_in_progress" in replay_rule

    error_codes = data["error_codes"]
    assert error_codes["required"] == "idempotency_key_required"
    assert error_codes["reused"] == "idempotency_key_reused"
    assert error_codes["in_progress"] == "idempotency_in_progress"

    # Covered commands
    required_for = data["required_for"]
    assert "create_execution_account_api_v1_execution_accounts_post" in required_for
    assert (
        "create_execution_deployment_api_v1_execution_deployments_post" in required_for
    )
    assert (
        "deployment_action_api_v1_execution_deployments__deployment_id__actions_post"
        in required_for
    )
    assert "update_kill_switch_api_v1_execution_kill_switch_put" in required_for
    assert (
        "resolve_execution_order_api_v1_execution_orders__order_id__resolve_post"
        in required_for
    )


def test_idempotency_missing_header_fails(tmp_path: Path):
    from tools.validate import check_idempotency

    api_dir = tmp_path / "schema" / "api"
    api_dir.mkdir(parents=True)
    idemp_file = api_dir / "idempotency.yaml"
    idemp_file.write_text(
        yaml.dump(
            {
                "ttl": "PT24H",
                "required_for": [],
            }
        )
    )
    problems = check_idempotency(tmp_path / "schema")
    assert len(problems) >= 1
    assert any("header" in p.reason.lower() for p in problems)


def test_idempotency_invalid_ttl_fails(tmp_path: Path):
    from tools.validate import check_idempotency

    api_dir = tmp_path / "schema" / "api"
    api_dir.mkdir(parents=True)
    idemp_file = api_dir / "idempotency.yaml"
    idemp_file.write_text(
        yaml.dump(
            {
                "header": "Idempotency-Key",
                "ttl": "24 hours",  # not ISO 8601 duration
                "required_for": [],
            }
        )
    )
    problems = check_idempotency(tmp_path / "schema")
    assert len(problems) >= 1
    assert any("ttl" in p.reason.lower() for p in problems)


def test_idempotency_unknown_operation_fails(tmp_path: Path):
    from tools.validate import check_idempotency

    api_dir = tmp_path / "schema" / "api"
    api_dir.mkdir(parents=True)
    idemp_file = api_dir / "idempotency.yaml"
    idemp_file.write_text(
        yaml.dump(
            {
                "header": "Idempotency-Key",
                "ttl": "PT24H",
                "required_for": ["nonexistent_operation_id"],
            }
        )
    )
    openapi_file = api_dir / "openapi.yaml"
    openapi_file.write_text(
        yaml.dump(
            {
                "openapi": "3.1.0",
                "paths": {},
            }
        )
    )
    problems = check_idempotency(tmp_path / "schema")
    assert len(problems) >= 1
    assert any("nonexistent_operation_id" in p.reason for p in problems)
