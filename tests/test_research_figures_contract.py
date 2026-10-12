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


def test_six_routes_present(openapi_doc: dict) -> None:
    paths = openapi_doc["paths"]
    assert "/api/v1/research/figures" in paths
    assert "post" in paths["/api/v1/research/figures"]
    assert "get" in paths["/api/v1/research/figures"]

    assert "/api/v1/research/figures/{figure_id}" in paths
    assert "get" in paths["/api/v1/research/figures/{figure_id}"]
    assert "delete" in paths["/api/v1/research/figures/{figure_id}"]

    assert "/api/v1/research/figures/{figure_id}/content" in paths
    assert "get" in paths["/api/v1/research/figures/{figure_id}/content"]

    assert "/api/v1/research/figures/bulk-delete" in paths
    assert "post" in paths["/api/v1/research/figures/bulk-delete"]


def test_content_headers_present(openapi_doc: dict) -> None:
    content_op = openapi_doc["paths"]["/api/v1/research/figures/{figure_id}/content"][
        "get"
    ]
    resp_200 = content_op["responses"]["200"]
    headers = resp_200.get("headers", {})
    assert "ETag" in headers
    assert "X-Content-Type-Options" in headers
    assert "Content-Security-Policy" in headers


def test_content_discriminator_image(openapi_registry: referencing.Registry) -> None:
    payload = {
        "title": "Equity curve",
        "collection": "regimes",
        "content": {
            "kind": "image",
            "media_type": "image/png",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgADNjd8qAAAAABJRU5ErkJggg==",
            "width": 800,
            "height": 600,
        },
    }
    validate_schema(openapi_registry, "ResearchFigureCreateRequest", payload)

    # Missing width rejected
    bad_payload = copy.deepcopy(payload)
    del bad_payload["content"]["width"]
    reject_schema(openapi_registry, "ResearchFigureCreateRequest", bad_payload)


def test_content_discriminator_plotly(openapi_registry: referencing.Registry) -> None:
    payload = {
        "title": "Interactive equity",
        "collection": "regimes",
        "content": {
            "kind": "plotly",
            "figure": {
                "data": [{"type": "scatter", "y": [1, 2, 3]}],
                "layout": {"title": "Equity"},
            },
        },
    }
    validate_schema(openapi_registry, "ResearchFigureCreateRequest", payload)

    # Missing data array in figure rejected
    bad_payload = copy.deepcopy(payload)
    del bad_payload["content"]["figure"]["data"]
    reject_schema(openapi_registry, "ResearchFigureCreateRequest", bad_payload)


def test_metadata_shape_validates(openapi_registry: referencing.Registry) -> None:
    meta = {
        "figure_id": "fig-123456",
        "title": "Regime drawdown",
        "collection": "regimes",
        "notes": "H1 2024",
        "kind": "image",
        "media_type": "image/png",
        "width": 1200,
        "height": 800,
        "byte_size": 15420,
        "revision": 1,
        "created_at": "2026-10-12T12:00:00Z",
        "updated_at": "2026-10-12T12:00:00Z",
        "provenance": {
            "script": "research/drawdown.py",
            "git_revision": "abcdef1234",
            "git_dirty": False,
        },
    }
    validate_schema(openapi_registry, "ResearchFigureMetadata", meta)


def test_bulk_delete_one_of(openapi_registry: referencing.Registry) -> None:
    by_ids = {"figure_ids": ["fig-1", "fig-2"]}
    by_col = {"collection": "regimes"}
    validate_schema(openapi_registry, "BulkDeleteResearchFiguresRequest", by_ids)
    validate_schema(openapi_registry, "BulkDeleteResearchFiguresRequest", by_col)

    # Both provided -> rejected by oneOf
    reject_schema(
        openapi_registry,
        "BulkDeleteResearchFiguresRequest",
        {"figure_ids": ["fig-1"], "collection": "regimes"},
    )

    # Neither provided -> rejected
    reject_schema(openapi_registry, "BulkDeleteResearchFiguresRequest", {})
