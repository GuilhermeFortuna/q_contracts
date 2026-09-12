import json
from pathlib import Path

import yaml

from tools.validate import check_edge_consistency


def create_minimal_edge_tree(tmp_path: Path) -> Path:
    schema_root = tmp_path / "schema"
    edge_dir = schema_root / "edge"
    exec_dir = edge_dir / "execution"
    exec_dir.mkdir(parents=True)

    # 1. data-gateway.yaml
    gw_file = edge_dir / "data-gateway.yaml"
    gw_file.write_text(
        yaml.dump(
            {
                "schema_major": 1,
                "schema_version": "1.0",
                "endpoints": {
                    "/v1/health": {
                        "method": "GET",
                        "response": {"status": 200},
                    }
                },
            }
        )
    )

    # 2. execution.yaml
    exec_file = edge_dir / "execution.yaml"
    exec_file.write_text(
        yaml.dump(
            {
                "schema_major": 1,
                "schema_version": "1.0",
                "endpoints": {
                    "/v1/health": {
                        "method": "GET",
                        "response": {"status": 200},
                    }
                },
            }
        )
    )

    # 3. submit-request.schema.json
    submit_req_file = exec_dir / "submit-request.schema.json"
    submit_req_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "edge/execution/submit-request",
                "type": "object",
                "required": ["intent_id", "order"],
                "properties": {
                    "intent_id": {"type": "string"},
                    "order": {"type": "object"},
                },
            }
        )
    )

    # 4. submit-outcome.schema.json (exactly 3 members)
    submit_outcome_file = exec_dir / "submit-outcome.schema.json"
    submit_outcome_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "edge/execution/submit-outcome",
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {"outcome": {"const": "accepted"}},
                        "required": ["outcome"],
                    },
                    {
                        "type": "object",
                        "properties": {"outcome": {"const": "rejected"}},
                        "required": ["outcome"],
                    },
                    {
                        "type": "object",
                        "properties": {"outcome": {"const": "indeterminate"}},
                        "required": ["outcome"],
                    },
                ],
            }
        )
    )

    # 5. lookup-outcome.schema.json (exactly 4 members, all declaring closes_intent)
    lookup_outcome_file = exec_dir / "lookup-outcome.schema.json"
    lookup_outcome_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "edge/execution/lookup-outcome",
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "outcome": {"const": "filled"},
                            "closes_intent": {"const": True},
                        },
                        "required": ["outcome", "closes_intent"],
                    },
                    {
                        "type": "object",
                        "properties": {
                            "outcome": {"const": "rejected"},
                            "closes_intent": {"const": True},
                        },
                        "required": ["outcome", "closes_intent"],
                    },
                    {
                        "type": "object",
                        "properties": {
                            "outcome": {"const": "not_found"},
                            "closes_intent": {"const": True},
                        },
                        "required": ["outcome", "closes_intent"],
                    },
                    {
                        "type": "object",
                        "properties": {
                            "outcome": {"const": "unavailable"},
                            "closes_intent": {"const": False},
                        },
                        "required": ["outcome", "closes_intent"],
                    },
                ],
            }
        )
    )

    # 6. quote-response.schema.json
    quote_resp_file = exec_dir / "quote-response.schema.json"
    quote_resp_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "edge/execution/quote-response",
                "type": "object",
                "required": ["symbol", "bid", "ask", "last", "time_msc", "age_ms"],
                "properties": {
                    "symbol": {"type": "string"},
                    "bid": {"type": "number"},
                    "ask": {"type": "number"},
                    "last": {"type": "number"},
                    "time_msc": {"type": "integer"},
                    "age_ms": {"type": "integer"},
                },
            }
        )
    )

    return schema_root


def test_edge_consistency_valid_tree_passes(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    problems = check_edge_consistency(schema_root)
    assert problems == []


def test_edge_contract_missing_schema_major_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    exec_file = schema_root / "edge" / "execution.yaml"
    data = yaml.safe_load(exec_file.read_text())
    del data["schema_major"]
    exec_file.write_text(yaml.dump(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "schema_major" in problems[0].reason.lower()


def test_edge_contract_missing_health_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    gw_file = schema_root / "edge" / "data-gateway.yaml"
    data = yaml.safe_load(gw_file.read_text())
    del data["endpoints"]["/v1/health"]
    gw_file.write_text(yaml.dump(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "health" in problems[0].reason.lower()


def test_submit_outcome_not_three_members_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    so_file = schema_root / "edge" / "execution" / "submit-outcome.schema.json"
    data = json.loads(so_file.read_text())
    # Add a 4th member
    data["oneOf"].append(
        {
            "type": "object",
            "properties": {"outcome": {"const": "extra"}},
            "required": ["outcome"],
        }
    )
    so_file.write_text(json.dumps(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "submit" in problems[0].reason.lower()
    assert "3" in problems[0].reason


def test_lookup_outcome_not_four_members_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    lo_file = schema_root / "edge" / "execution" / "lookup-outcome.schema.json"
    data = json.loads(lo_file.read_text())
    data["oneOf"] = data["oneOf"][:2]
    lo_file.write_text(json.dumps(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "lookup" in problems[0].reason.lower()
    assert "4" in problems[0].reason


def test_lookup_member_missing_closes_intent_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    lo_file = schema_root / "edge" / "execution" / "lookup-outcome.schema.json"
    data = json.loads(lo_file.read_text())
    del data["oneOf"][2]["properties"]["closes_intent"]
    data["oneOf"][2]["required"].remove("closes_intent")
    lo_file.write_text(json.dumps(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "closes_intent" in problems[0].reason.lower()


def test_submit_request_missing_intent_id_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    sr_file = schema_root / "edge" / "execution" / "submit-request.schema.json"
    data = json.loads(sr_file.read_text())
    data["required"].remove("intent_id")
    sr_file.write_text(json.dumps(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "intent_id" in problems[0].reason.lower()


def test_quote_response_missing_age_ms_fails(tmp_path: Path):
    schema_root = create_minimal_edge_tree(tmp_path)
    qr_file = schema_root / "edge" / "execution" / "quote-response.schema.json"
    data = json.loads(qr_file.read_text())
    data["required"].remove("age_ms")
    qr_file.write_text(json.dumps(data))

    problems = check_edge_consistency(schema_root)
    assert len(problems) == 1
    assert "age_ms" in problems[0].reason.lower()
