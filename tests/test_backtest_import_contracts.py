import copy
import json
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"
EXAMPLES = Path(__file__).parent.parent / "schema" / "api" / "examples" / "backtests"


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


def reject_schema(
    registry: referencing.Registry, schema_name: str, instance: dict
) -> None:
    validator = jsonschema.Draft202012Validator(
        {"$ref": f"urn:openapi#/components/schemas/{schema_name}"},
        registry=registry,
    )
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(instance)


@pytest.fixture(scope="module")
def import_request() -> dict:
    return json.loads((EXAMPLES / "import-request.json").read_text(encoding="utf-8"))


def test_complete_import_request_fixture_validates(
    openapi_registry: referencing.Registry, import_request: dict
) -> None:
    validate_schema(openapi_registry, "BacktestImportRequest", import_request)


@pytest.mark.parametrize("missing_field", ["config", "result", "provenance"])
def test_import_request_missing_required_field_rejected(
    openapi_registry: referencing.Registry,
    import_request: dict,
    missing_field: str,
) -> None:
    payload = copy.deepcopy(import_request)
    del payload[missing_field]
    reject_schema(openapi_registry, "BacktestImportRequest", payload)


def test_run_list_item_without_origin_still_validates(
    openapi_registry: referencing.Registry,
) -> None:
    item = json.loads((EXAMPLES / "run-list-item.json").read_text(encoding="utf-8"))
    assert "origin" not in item
    validate_schema(openapi_registry, "BacktestRunListItem", item)


def test_run_detail_without_origin_still_validates(
    openapi_registry: referencing.Registry,
) -> None:
    detail = json.loads((EXAMPLES / "run-detail.json").read_text(encoding="utf-8"))
    assert "origin" not in detail
    validate_schema(openapi_registry, "BacktestRunDetailResponse", detail)


def test_invalid_origin_enum_rejected_on_list_item(
    openapi_registry: referencing.Registry,
) -> None:
    item = json.loads((EXAMPLES / "run-list-item.json").read_text(encoding="utf-8"))
    item["origin"] = "notebook"
    reject_schema(openapi_registry, "BacktestRunListItem", item)


def test_origin_defaults_to_stack_in_openapi(
    openapi_doc: dict,
) -> None:
    origin = openapi_doc["components"]["schemas"]["BacktestRunListItem"]["properties"][
        "origin"
    ]
    assert origin.get("default") == "stack"
    detail_origin = openapi_doc["components"]["schemas"]["BacktestRunDetailResponse"][
        "properties"
    ]["origin"]
    assert detail_origin.get("default") == "stack"


def test_import_operation_present(openapi_doc: dict) -> None:
    post = openapi_doc["paths"]["/api/v1/backtests/import"]["post"]
    assert post["operationId"] == "import_backtest_api_v1_backtests_import_post"
    body_schema = post["requestBody"]["content"]["application/json"]["schema"]
    assert body_schema["$ref"].endswith("/BacktestImportRequest")
    assert "201" in post["responses"]


def test_list_backtests_origin_query_parameter(openapi_doc: dict) -> None:
    params = openapi_doc["paths"]["/api/v1/backtests"]["get"]["parameters"]
    origin_param = next(p for p in params if p.get("name") == "origin")
    assert origin_param["in"] == "query"
    assert origin_param["required"] is False
    schema = origin_param["schema"]
    assert schema["$ref"].endswith("/BacktestOrigin")
