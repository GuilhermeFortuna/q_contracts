from pathlib import Path

import yaml

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"
CANCEL_PATH = "/api/v1/backtest/{run_id}/cancel"


def _operation() -> dict:
    doc = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    return doc["paths"][CANCEL_PATH]["post"]


def test_backtest_cancel_returns_status_response() -> None:
    schema = _operation()["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/BacktestStatusResponse"}


def test_backtest_cancel_takes_run_id_path_parameter() -> None:
    (param,) = _operation()["parameters"]
    assert param["in"] == "path"
    assert param["name"] == "run_id"
    assert param["required"] is True
