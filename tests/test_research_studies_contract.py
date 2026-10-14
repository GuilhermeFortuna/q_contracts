import copy
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"


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


def validator_for(
    registry: referencing.Registry, schema_name: str
) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": f"urn:openapi#/components/schemas/{schema_name}"},
        registry=registry,
    )


def valid_create_request() -> dict:
    return {
        "name": "Keltner 20/2",
        "symbol": "WDO$N",
        "timeframe": "M10",
        "timestamps": ["2026-01-05T13:00:00+00:00", "2026-01-05T13:10:00+00:00"],
        "series": [
            {
                "key": "kc_upper",
                "label": "kc_upper",
                "pane": "price",
                "color": "#6eb5ff",
                "lineStyle": "dashed",
                "lineWidth": 1.5,
                "values": [1.0, None],
            }
        ],
    }


def test_study_routes_present(openapi_doc: dict) -> None:
    paths = openapi_doc["paths"]
    assert {"get", "post"} <= set(paths["/api/v1/research/studies"])
    assert {"patch", "delete"} <= set(paths["/api/v1/research/studies/{study_id}"])
    assert "get" in paths["/api/v1/research/studies/{study_id}/series"]


def test_create_request_accepts_valid_payload(
    openapi_registry: referencing.Registry,
) -> None:
    validator_for(openapi_registry, "ResearchStudyCreateRequest").validate(
        valid_create_request()
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda body: body["series"][0].update(pane="sidebar"),
        lambda body: body["series"][0].update(lineStyle="wavy"),
        lambda body: body["series"][0].update(lineWidth=0),
        lambda body: body.update(series=[]),
        lambda body: body.update(name="x" * 121),
        lambda body: body.update(name=""),
    ],
)
def test_create_request_rejects_invalid_payload(
    openapi_registry: referencing.Registry, mutate
) -> None:
    body = copy.deepcopy(valid_create_request())
    mutate(body)
    with pytest.raises(jsonschema.ValidationError):
        validator_for(openapi_registry, "ResearchStudyCreateRequest").validate(body)
