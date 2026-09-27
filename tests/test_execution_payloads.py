import json
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

STREAM_DIR = Path(__file__).parent.parent / "schema" / "stream"
PAYLOADS_DIR = STREAM_DIR / "payloads"
EXAMPLES_DIR = STREAM_DIR / "examples"
TOPICS_FILE = STREAM_DIR / "topics.yaml"

EXECUTION_TOPICS = [
    "decisions",
    "orders",
    "fills",
    "risk",
    "ledger",
    "deployments",
]


def load_payload_validator(name: str) -> jsonschema.Draft202012Validator:
    schema_path = PAYLOADS_DIR / f"{name}.schema.json"
    assert schema_path.is_file(), f"Payload schema file {schema_path} must exist"
    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))

    resources = []
    for file in STREAM_DIR.rglob("*.schema.json"):
        s = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(s, dict) or "$schema" not in s:
            continue
        res = referencing.Resource.from_contents(s)
        resources.append((file.name, res))
        resources.append((file.as_posix(), res))
        resources.append((file.relative_to(STREAM_DIR).as_posix(), res))
        resources.append((f"../payloads/{file.name}", res))
        if "$id" in s:
            resources.append((s["$id"], res))
            resources.append((f"{s['$id']}.schema.json", res))
    registry = referencing.Registry().with_resources(resources)
    return jsonschema.Draft202012Validator(schema_data, registry=registry)


def test_execution_topics_point_at_dedicated_payloads():
    topics_data = yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8"))["topics"]
    for topic in EXECUTION_TOPICS:
        assert topic in topics_data
        payload_schema = topics_data[topic].get("payload_schema")
        assert payload_schema is not None
        assert (
            payload_schema != "schema/stream/envelope.schema.json"
        ), f"Topic '{topic}' must not point at envelope.schema.json"
        assert Path(
            payload_schema
        ).is_file(), (
            f"Payload schema '{payload_schema}' for topic '{topic}' must exist on disk"
        )


@pytest.mark.parametrize(
    "schema_name,example_name",
    [
        ("execution-deployment", "execution-deployment.json"),
        ("execution-decision", "execution-decision.json"),
        ("execution-order", "execution-order.json"),
        ("execution-fill", "execution-fill.json"),
        ("execution-risk", "execution-risk-rejection.json"),
        ("execution-risk", "execution-risk-kill-switch.json"),
        ("execution-ledger", "execution-ledger.json"),
    ],
)
def test_execution_examples_validate(schema_name: str, example_name: str):
    validator = load_payload_validator(schema_name)
    example_path = EXAMPLES_DIR / example_name
    assert example_path.is_file(), f"Example file {example_path} must exist"
    data = json.loads(example_path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(data))
    assert errors == [], f"Validation errors for {example_name}: {errors}"


def test_missing_id_fails():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    del bad["id"]
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any("id" in str(err.path) or "id" in err.message for err in errors)


def test_missing_deployment_id_fails():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    del bad["deployment_id"]
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any(
        "deployment_id" in str(err.path) or "deployment_id" in err.message
        for err in errors
    )


def test_missing_position_after_on_fill_fails():
    validator = load_payload_validator("execution-fill")
    example = json.loads(
        (EXAMPLES_DIR / "execution-fill.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    del bad["position_after"]
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any(
        "position_after" in str(err.path) or "position_after" in err.message
        for err in errors
    )


def test_missing_account_after_on_ledger_fails():
    validator = load_payload_validator("execution-ledger")
    example = json.loads(
        (EXAMPLES_DIR / "execution-ledger.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    del bad["account_after"]
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any(
        "account_after" in str(err.path) or "account_after" in err.message
        for err in errors
    )


def test_numeric_decimal_fails():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    bad["quantity"] = 100.5
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any(
        "quantity" in str(err.path) or "quantity" in err.message for err in errors
    )


def test_unknown_order_status_fails():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    bad = dict(example)
    bad["status"] = "in_progress"
    errors = list(validator.iter_errors(bad))
    assert len(errors) >= 1
    assert any("status" in str(err.path) or "status" in err.message for err in errors)


def test_check_execution_payloads_topic_pointing_at_envelope_fails(tmp_path: Path):
    from tools.validate import check_execution_payloads

    stream_dir = tmp_path / "schema" / "stream"
    stream_dir.mkdir(parents=True)
    topics_file = stream_dir / "topics.yaml"
    topics_file.write_text(
        yaml.dump(
            {
                "topics": {
                    "orders": {
                        "class": "durable",
                        "payload_schema": "schema/stream/envelope.schema.json",
                    }
                }
            }
        )
    )
    problems = check_execution_payloads(tmp_path / "schema")
    assert len(problems) >= 1
    assert any("orders" in p.reason and "envelope" in p.reason for p in problems)


def test_check_execution_payloads_snapshot_divergence_fails(tmp_path: Path):
    from tools.validate import check_execution_payloads

    schema_root = tmp_path / "schema"
    payloads_dir = schema_root / "stream" / "payloads"
    replay_dir = schema_root / "stream" / "replay"
    payloads_dir.mkdir(parents=True)
    replay_dir.mkdir(parents=True)

    dep_file = payloads_dir / "execution-deployment.schema.json"
    dep_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "entity": {"const": "deployment"},
                    "id": {"type": "string"},
                    "symbol": {"type": "string"},
                },
                "required": ["entity", "id", "symbol"],
            }
        )
    )

    snapshot_file = replay_dir / "execution-snapshot.schema.json"
    snapshot_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "deployments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity": {"const": "deployment"},
                                "id": {"type": "string"},
                                "different_field": {"type": "integer"},
                            },
                            "required": ["entity", "id", "different_field"],
                        },
                    }
                },
            }
        )
    )

    problems = check_execution_payloads(schema_root)
    assert len(problems) >= 1
    assert any("deployments" in p.reason and "diverges" in p.reason for p in problems)


def test_deployment_with_config_revision_and_paper_cost_config_validates():
    validator = load_payload_validator("execution-deployment")
    example = json.loads(
        (EXAMPLES_DIR / "execution-deployment.json").read_text(encoding="utf-8")
    )
    doc = dict(example)
    doc["config_revision"] = 1
    doc["paper_cost_config"] = {
        "point_value": "1.0",
        "slippage_points": "0.5",
        "cost_per_contract": "1.25",
        "cost_bps": "2.0",
    }
    errors = list(validator.iter_errors(doc))
    assert errors == []


def test_decision_with_config_revision_and_paper_cost_config_validates():
    validator = load_payload_validator("execution-decision")
    example = json.loads(
        (EXAMPLES_DIR / "execution-decision.json").read_text(encoding="utf-8")
    )
    doc = dict(example)
    doc["config_revision"] = 2
    doc["paper_cost_config"] = {
        "point_value": "0.2",
        "slippage_points": "0.0",
        "cost_per_contract": "0.0",
        "cost_bps": "0.0",
    }
    errors = list(validator.iter_errors(doc))
    assert errors == []


@pytest.mark.parametrize("bad_revision", [0, -1, "1", 1.5])
def test_invalid_config_revision_fails(bad_revision):
    validator = load_payload_validator("execution-deployment")
    example = json.loads(
        (EXAMPLES_DIR / "execution-deployment.json").read_text(encoding="utf-8")
    )
    doc = dict(example)
    doc["config_revision"] = bad_revision
    errors = list(validator.iter_errors(doc))
    assert len(errors) >= 1
    assert any(
        "config_revision" in str(err.path) or "config_revision" in err.message
        for err in errors
    )


@pytest.mark.parametrize(
    "bad_costs",
    [
        # JSON numbers instead of decimal strings
        {
            "point_value": 1.0,
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        {
            "point_value": "1.0",
            "slippage_points": 0.5,
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        {
            "point_value": "1.0",
            "slippage_points": "0.5",
            "cost_per_contract": 1.25,
            "cost_bps": "2.0",
        },
        {
            "point_value": "1.0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": 2.0,
        },
        # point_value zero or negative
        {
            "point_value": "0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        {
            "point_value": "0.0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        {
            "point_value": "-1.0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        # slippage negative
        {
            "point_value": "1.0",
            "slippage_points": "-0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
        # cost_per_contract negative
        {
            "point_value": "1.0",
            "slippage_points": "0.5",
            "cost_per_contract": "-1.25",
            "cost_bps": "2.0",
        },
        # cost_bps negative
        {
            "point_value": "1.0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "-2.0",
        },
        # missing required field
        {
            "point_value": "1.0",
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
        },
        {"point_value": "1.0", "slippage_points": "0.5", "cost_bps": "2.0"},
        {"point_value": "1.0", "cost_per_contract": "1.25", "cost_bps": "2.0"},
        {
            "slippage_points": "0.5",
            "cost_per_contract": "1.25",
            "cost_bps": "2.0",
        },
    ],
)
def test_invalid_paper_cost_config_fails(bad_costs):
    validator = load_payload_validator("execution-deployment")
    example = json.loads(
        (EXAMPLES_DIR / "execution-deployment.json").read_text(encoding="utf-8")
    )
    doc = dict(example)
    doc["paper_cost_config"] = bad_costs
    errors = list(validator.iter_errors(doc))
    assert len(errors) >= 1
    assert any(
        "paper_cost_config" in str(err.path) or "paper_cost_config" in err.message
        for err in errors
    )


def test_order_dispatch_attempted_at_validates():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    # Valid timestamp
    doc1 = dict(example)
    doc1["dispatch_attempted_at"] = "2026-09-18T14:30:01.120Z"
    assert list(validator.iter_errors(doc1)) == []

    # Null timestamp
    doc2 = dict(example)
    doc2["dispatch_attempted_at"] = None
    assert list(validator.iter_errors(doc2)) == []

    # Invalid timestamp type (must be string or null)
    doc3 = dict(example)
    doc3["dispatch_attempted_at"] = 12345
    errs = list(validator.iter_errors(doc3))
    assert len(errs) >= 1
    assert any(
        "dispatch_attempted_at" in str(err.path)
        or "dispatch_attempted_at" in err.message
        for err in errs
    )


def test_unknown_order_with_dispatch_attempt_and_no_fill_validates():
    validator = load_payload_validator("execution-order")
    example = json.loads(
        (EXAMPLES_DIR / "execution-order.json").read_text(encoding="utf-8")
    )
    doc = dict(example)
    doc["status"] = "unknown"
    doc["reconciliation_state"] = "ambiguous"
    doc["dispatch_attempted_at"] = "2026-09-18T14:30:01.120Z"
    doc["submitted_at"] = None
    doc["completed_at"] = None
    doc["external_order_id"] = None
    assert list(validator.iter_errors(doc)) == []


def test_historical_payloads_without_extensions_validate():
    """Historical payloads without config_revision, paper_cost_config, or dispatch_attempted_at must pass."""
    for schema_name, filename in [
        ("execution-deployment", "execution-deployment.json"),
        ("execution-decision", "execution-decision.json"),
        ("execution-order", "execution-order.json"),
    ]:
        validator = load_payload_validator(schema_name)
        data = json.loads((EXAMPLES_DIR / filename).read_text(encoding="utf-8"))
        assert list(validator.iter_errors(data)) == []
