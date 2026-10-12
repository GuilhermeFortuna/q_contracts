from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"


@pytest.fixture(scope="module")
def openapi_registry() -> referencing.Registry:
    doc = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    resource = referencing.Resource.from_contents(
        doc, default_specification=referencing.jsonschema.DRAFT202012
    )
    return referencing.Registry().with_resource("urn:openapi", resource)


def _validator(
    registry: referencing.Registry, schema_name: str
) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": f"urn:openapi#/components/schemas/{schema_name}"},
        registry=registry,
    )


def _response(**extra) -> dict:
    return {"metrics": {}, "trades": [], "bars": [], "indicators": [], **extra}


def test_backtest_response_without_notes_still_validates(
    openapi_registry: referencing.Registry,
) -> None:
    _validator(openapi_registry, "BacktestResponse").validate(_response())


def test_backtest_response_with_notes_validates(
    openapi_registry: referencing.Registry,
) -> None:
    note = {
        "code": "intrabar_incomplete_ticks",
        "message": "412 trades: 397 exits decided on real ticks.",
        "details": {"candles_substituted": 3, "affected_sessions": ["2022-02-11"]},
    }
    _validator(openapi_registry, "BacktestResponse").validate(_response(notes=[note]))


def test_backtest_note_details_are_optional(
    openapi_registry: referencing.Registry,
) -> None:
    note = {"code": "intrabar_incomplete_ticks", "message": "Ticks were incomplete."}
    _validator(openapi_registry, "BacktestNote").validate(note)


@pytest.mark.parametrize("missing", ["code", "message"])
def test_backtest_note_requires_code_and_message(
    openapi_registry: referencing.Registry, missing: str
) -> None:
    note = {"code": "intrabar_incomplete_ticks", "message": "Ticks were incomplete."}
    del note[missing]
    with pytest.raises(jsonschema.ValidationError):
        _validator(openapi_registry, "BacktestNote").validate(note)
