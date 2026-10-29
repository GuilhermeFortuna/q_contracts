import json
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"
EXAMPLES = Path(__file__).parent.parent / "schema" / "api" / "examples"


@pytest.fixture(scope="module")
def openapi_doc() -> dict:
    assert OPENAPI_PATH.is_file()
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def openapi_registry(openapi_doc: dict) -> referencing.Registry:
    resource = referencing.Resource.from_contents(
        openapi_doc, default_specification=referencing.jsonschema.DRAFT202012
    )
    return referencing.Registry().with_resource("urn:openapi", resource)


def validate_schema(
    registry: referencing.Registry, schema_name: str, instance: dict
) -> None:
    validator = jsonschema.Draft202012Validator(
        {"$ref": f"urn:openapi#/components/schemas/{schema_name}"},
        registry=registry,
    )
    validator.validate(instance)


def test_deployment_summary_example_validates(
    openapi_registry: referencing.Registry,
) -> None:
    path = EXAMPLES / "deployments" / "deployment-summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_schema(openapi_registry, "DeploymentSummaryResponse", data)


def test_deployment_detail_example_validates(
    openapi_registry: referencing.Registry,
) -> None:
    path = EXAMPLES / "deployments" / "deployment-detail.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_schema(openapi_registry, "DeploymentDetailResponse", data)


def test_backtest_run_detail_with_order_kinds_validates(
    openapi_registry: referencing.Registry,
) -> None:
    path = EXAMPLES / "backtests" / "run-detail.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_schema(openapi_registry, "BacktestRunDetailResponse", data)


def test_backtest_run_list_item_strategy_file_validates(
    openapi_registry: referencing.Registry,
) -> None:
    path = EXAMPLES / "backtests" / "run-list-item-strategy-file.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_schema(openapi_registry, "BacktestRunListItem", data)
