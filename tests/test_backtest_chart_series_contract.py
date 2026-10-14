import copy
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"


@pytest.fixture(scope="module")
def validator() -> jsonschema.Draft202012Validator:
    doc = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    resource = referencing.Resource.from_contents(
        doc, default_specification=referencing.jsonschema.DRAFT202012
    )
    registry = referencing.Registry().with_resource("urn:openapi", resource)
    return jsonschema.Draft202012Validator(
        {"$ref": "urn:openapi#/components/schemas/ChartIndicatorSeries"},
        registry=registry,
    )


def valid_segment_series() -> dict:
    return {
        "key": "top",
        "label": "Top",
        "pane": "price",
        "kind": "segment",
        "color": "#26a69a",
        "values": [None, 5076.0, None],
        "start_index": [None, 3, None],
    }


def test_legacy_line_series_without_kind_remains_valid(validator) -> None:
    legacy = {"key": "sma", "label": "SMA", "pane": "price", "values": [1.0, None]}
    validator.validate(legacy)


def test_segment_series_is_valid(validator) -> None:
    validator.validate(valid_segment_series())


@pytest.mark.parametrize(
    "patch",
    [
        {"kind": "scatter"},
        {"shape": "star"},
        {"position": "middle"},
        {"size": 0},
        {"size": 33},
        {"fill_opacity": 1.0},
        {"start_index": [-1]},
    ],
)
def test_invalid_fields_are_rejected(validator, patch) -> None:
    series = valid_segment_series()
    series.update(patch)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(series)


def test_start_index_must_be_integers_or_null(validator) -> None:
    series = copy.deepcopy(valid_segment_series())
    series["start_index"] = [1.5, None, None]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(series)
