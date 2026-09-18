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
    schema_root = STREAM_DIR.parent
    for file in schema_root.rglob("*.schema.json"):
        s = json.loads(file.read_text(encoding="utf-8"))
        res = referencing.Resource.from_contents(s)
        resources.append((file.name, res))
        resources.append((file.as_posix(), res))
        resources.append((file.relative_to(schema_root).as_posix(), res))
        rel_str = f"schema/{file.relative_to(schema_root).as_posix()}"
        resources.append((rel_str, res))
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
