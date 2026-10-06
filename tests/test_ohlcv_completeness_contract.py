from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schema"


def test_ohlcv_metadata_and_continuation_contract():
    gateway = yaml.safe_load(
        (SCHEMA / "edge/data-gateway.yaml").read_text(encoding="utf-8")
    )
    ohlcv = gateway["endpoints"]["/v1/ohlcv"]

    # Endpoint description specifies the meaning of truncated states without
    # claiming broker or terminal completeness.
    desc = ohlcv["description"]
    assert "truncated" in desc
    assert "max_bars" in desc
    assert (
        "Neither value is a statement about how much history the broker or terminal keeps"
        in desc
    )

    response = ohlcv["response"]
    assert "metadata" in response
    metadata = response["metadata"]

    # metadata declares truncated boolean and max_bars integer >= 1
    assert metadata["truncated"] == "boolean"
    assert metadata["max_bars"]["type"] == "integer"
    assert metadata["max_bars"]["minimum"] == 1

    # continuation declares rule naming next start and unchanged end
    assert "continuation" in response
    continuation = response["continuation"]
    assert "next_start" in continuation or "start" in continuation
    next_start_val = continuation.get("next_start") or continuation.get("start")
    assert "last returned bar" in next_start_val or "last_bar" in next_start_val
    assert "1 second" in next_start_val or "one second" in next_start_val
    assert continuation["end"] == "unchanged"

    rule_text = str(continuation.get("rule", ""))
    assert "truncated: false" in rule_text or "truncated == false" in rule_text
    assert "no bars" in rule_text or "empty" in rule_text


def test_ohlcv_arrays_remain_unchanged():
    gateway = yaml.safe_load(
        (SCHEMA / "edge/data-gateway.yaml").read_text(encoding="utf-8")
    )
    ohlcv = gateway["endpoints"]["/v1/ohlcv"]
    response = ohlcv["response"]

    assert response["format"] == "npz"
    assert response["equal_length_requirement"] is True

    arrays = response["arrays"]
    expected_arrays = {
        "time": {"dtype": "int64", "optional": False},
        "open": {"dtype": "float64", "optional": False},
        "high": {"dtype": "float64", "optional": False},
        "low": {"dtype": "float64", "optional": False},
        "close": {"dtype": "float64", "optional": False},
        "tick_volume": {"dtype": "int64", "optional": False},
        "spread": {"dtype": "int64", "optional": True},
        "real_volume": {"dtype": "int64", "optional": True},
    }

    assert set(arrays.keys()) == set(expected_arrays.keys())
    for name, expected in expected_arrays.items():
        assert arrays[name]["dtype"] == expected["dtype"]
        is_optional = arrays[name].get("optional", False)
        assert is_optional is expected["optional"]


def test_ticks_and_trades_remain_unchanged():
    gateway = yaml.safe_load(
        (SCHEMA / "edge/data-gateway.yaml").read_text(encoding="utf-8")
    )
    endpoints = gateway["endpoints"]

    # /v1/ticks arrays remain unchanged
    ticks_arrays = endpoints["/v1/ticks"]["response"]["arrays"]
    expected_ticks_arrays = {
        "time_msc": "int64",
        "bid": "float64",
        "ask": "float64",
        "last": "float64",
        "volume": "float64",
        "flags": "int32",
    }
    assert set(ticks_arrays.keys()) == set(expected_ticks_arrays.keys())
    for name, dtype in expected_ticks_arrays.items():
        assert ticks_arrays[name]["dtype"] == dtype

    # /v1/trades arrays and metadata keys remain unchanged
    trades_resp = endpoints["/v1/trades"]["response"]
    trades_arrays = trades_resp["arrays"]
    expected_trades_arrays = {
        "time_msc": "int64",
        "price": "float64",
        "volume": "float64",
        "volume_real": "float64",
        "raw_flags": "int32",
        "occurrence": "int64",
    }
    assert set(trades_arrays.keys()) == set(expected_trades_arrays.keys())
    for name, dtype in expected_trades_arrays.items():
        assert trades_arrays[name]["dtype"] == dtype

    expected_trades_metadata = {
        "provider_id",
        "symbol",
        "source_generation",
        "volume_field",
        "volume_unit",
        "availability",
        "range_complete",
        "covered_from_utc",
        "covered_to_utc",
        "coverage_reason",
        "invalid_trade_count",
        "truncated",
    }
    assert set(trades_resp["metadata"].keys()) == expected_trades_metadata
