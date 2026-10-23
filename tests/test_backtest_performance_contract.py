import copy
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


def _trade_stats(total: int = 0) -> dict:
    empty = total == 0
    return {
        "total": total,
        "winning": 0,
        "losing": 0,
        "breakeven": 0,
        "win_rate": None if empty else 0.5,
        "profit_factor": None,
        "expectancy": None if empty else 75.0,
        "avg_win": None,
        "avg_loss": None,
        "payoff_ratio": None,
        "largest_win": None,
        "largest_loss": None,
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0,
        "avg_hold_seconds": None,
        "avg_win_hold_seconds": None,
        "avg_loss_hold_seconds": None,
    }


def _performance() -> dict:
    portfolio = {
        "net_pnl": 350.0,
        "gross_profit": 500.0,
        "gross_loss": -150.0,
        "total_commission": 0.0,
        "return_pct": 0.035,
        "cagr_pct": None,
        "max_drawdown_value": 150.0,
        "max_drawdown_pct": 0.0147,
        "max_drawdown_duration_days": 16.0,
        "avg_drawdown_pct": 0.0147,
        "recovery_factor": 2.33,
        "calmar_ratio": None,
        "sharpe_ratio": None,
        "sortino_ratio": None,
        "annual_volatility_pct": 0.0,
        "time_in_market_pct": 0.4,
        "trades_per_month": 4.06,
    }
    return {
        "basis": {
            "equity": "closed_trade",
            "periods_per_year": 252,
            "risk_free_rate": 0.0,
        },
        "portfolio": portfolio,
        "trades": {
            "all": _trade_stats(4),
            "long": _trade_stats(2),
            "short": _trade_stats(2),
        },
        "drawdowns": [
            {
                "peak_time": "2024-01-04T00:00:00",
                "trough_time": "2024-01-12T00:00:00",
                "recovery_time": "2024-01-20T00:00:00",
                "depth_value": 150.0,
                "depth_pct": 0.0147,
                "duration_days": 16.0,
                "trades": 3,
            },
            {
                "peak_time": "2024-01-02T00:00:00",
                "trough_time": "2024-01-03T00:00:00",
                "recovery_time": None,
                "depth_value": 10.0,
                "depth_pct": 0.001,
                "duration_days": 30.0,
                "trades": 1,
            },
        ],
        "exit_reasons": [{"reason": "tp", "trades": 2, "pnl": 500.0, "win_rate": 1.0}],
    }


def _response(**extra) -> dict:
    return {"metrics": {}, "trades": [], "bars": [], "indicators": [], **extra}


def test_backtest_response_with_performance_validates(
    openapi_registry: referencing.Registry,
) -> None:
    _validator(openapi_registry, "BacktestResponse").validate(
        _response(performance=_performance())
    )


def test_performance_is_optional_and_nullable(
    openapi_registry: referencing.Registry,
) -> None:
    validator = _validator(openapi_registry, "BacktestResponse")
    validator.validate(_response())
    validator.validate(_response(performance=None))


def test_performance_basis_is_closed_trade_only(
    openapi_registry: referencing.Registry,
) -> None:
    payload = _performance()
    payload["basis"]["equity"] = "mark_to_market"

    with pytest.raises(jsonschema.ValidationError):
        _validator(openapi_registry, "BacktestPerformance").validate(payload)


def test_missing_portfolio_field_is_rejected(
    openapi_registry: referencing.Registry,
) -> None:
    payload = copy.deepcopy(_performance())
    del payload["portfolio"]["sharpe_ratio"]

    with pytest.raises(jsonschema.ValidationError):
        _validator(openapi_registry, "BacktestPerformance").validate(payload)


def test_drawdown_recovery_time_is_null_when_unrecovered(
    openapi_registry: referencing.Registry,
) -> None:
    payload = copy.deepcopy(_performance())
    payload["drawdowns"][0]["recovery_time"] = None

    _validator(openapi_registry, "BacktestPerformance").validate(payload)


def test_metrics_and_trades_remain_free_form(
    openapi_registry: referencing.Registry,
) -> None:
    _validator(openapi_registry, "BacktestResponse").validate(
        _response(metrics={"anything": [1, 2]}, trades=[{"extra": True}])
    )
