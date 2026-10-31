"""Strategy-file backtests explicitly choose their market-data source."""

from pathlib import Path

import jsonschema
import pytest
import yaml


@pytest.fixture(scope="module")
def schemas():
    return yaml.safe_load(
        (Path(__file__).parents[1] / "schema/api/openapi.yaml").read_text()
    )["components"]["schemas"]


def test_data_mode_is_optional_and_defaults_to_bars(schemas):
    request = schemas["BacktestRequest"]
    assert "research_data_mode" not in request["required"]
    mode = request["properties"]["research_data_mode"]
    assert mode["default"] == "bars"
    for value in ("bars", "ticks"):
        jsonschema.validate(value, mode)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate("auto", mode)


def test_discovery_distinguishes_required_and_optional_tick_hooks(schemas):
    assert schemas["StrategyFile"]["properties"]["requires_tick_data"] == {
        "default": False,
        "title": "Requires Tick Data",
        "type": "boolean",
    }
