"""Contract checks for the execution edge pending, protective and order-listing actions (edge 1.2)."""

import json
from pathlib import Path

import jsonschema
import pytest

from tests.test_edge_schemas import EXAMPLES_DIR, load_execution_validator


def _example(name: str) -> dict:
    return json.loads((EXAMPLES_DIR / name).read_text(encoding="utf-8"))


def test_execution_contract_declares_edge_1_2_and_orders_operation():
    import yaml

    doc = yaml.safe_load(Path("schema/edge/execution.yaml").read_text(encoding="utf-8"))
    assert doc["schema_major"] == 1
    assert doc["schema_version"] == "1.2"
    assert doc["operations"]["orders"]["path"] == "/v1/orders"
    assert doc["operations"]["orders"]["method"] == "GET"
    assert "/v1/orders" in doc["endpoints"]


def test_submit_request_action_defaults_to_deal_and_keeps_market_shape():
    validator = load_execution_validator("submit-request.schema.json")
    market = {
        "intent_id": "018f6c38-89ab-7000-8000-000000000001",
        "order": {"symbol": "PETR4", "volume": 100.0, "side": "buy"},
    }
    validator.validate(market)

    market_with_levels = {
        "intent_id": "018f6c38-89ab-7000-8000-000000000001",
        "action": "deal",
        "order": {
            "symbol": "PETR4",
            "volume": 100.0,
            "side": "buy",
            "sl": 40.5,
            "tp": 42.0,
        },
    }
    validator.validate(market_with_levels)


@pytest.mark.parametrize(
    "example",
    [
        "submit-request-pending.json",
        "submit-request-sltp.json",
        "submit-request-remove.json",
    ],
)
def test_submit_request_examples_validate(example: str):
    validator = load_execution_validator("submit-request.schema.json")
    validator.validate(_example(example))


def test_pending_action_requires_price_and_a_pending_order_type():
    validator = load_execution_validator("submit-request.schema.json")
    base = _example("submit-request-pending.json")

    no_price = json.loads(json.dumps(base))
    del no_price["order"]["price"]
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(no_price)

    market_type = json.loads(json.dumps(base))
    market_type["order"]["type"] = 0
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(market_type)


def test_sltp_and_remove_require_their_identifiers():
    validator = load_execution_validator("submit-request.schema.json")

    sltp_without_position = _example("submit-request-sltp.json")
    del sltp_without_position["position"]
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(sltp_without_position)

    sltp_without_tp = _example("submit-request-sltp.json")
    del sltp_without_tp["tp"]
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(sltp_without_tp)

    remove_without_ticket = _example("submit-request-remove.json")
    del remove_without_ticket["order_ticket"]
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(remove_without_ticket)


def test_deal_and_pending_require_an_order_object():
    validator = load_execution_validator("submit-request.schema.json")
    for action in ("deal", "pending"):
        request = {
            "intent_id": "018f6c38-89ab-7000-8000-000000000005",
            "action": action,
        }
        with pytest.raises(jsonschema.exceptions.ValidationError):
            validator.validate(request)


def test_submit_request_rejects_unknown_action():
    validator = load_execution_validator("submit-request.schema.json")
    request = _example("submit-request-remove.json")
    request["action"] = "modify"
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(request)


def test_orders_response_and_request_validate():
    load_execution_validator("orders-request.schema.json").validate({"symbol": "PETR4"})
    load_execution_validator("orders-request.schema.json").validate({})
    validator = load_execution_validator("orders-response.schema.json")
    validator.validate(_example("orders-response.json"))
    validator.validate([])


def test_working_order_requires_ticket_and_price():
    validator = load_execution_validator("working-order.schema.json")
    order = _example("orders-response.json")[0]
    validator.validate(order)
    del order["price"]
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(order)


def test_deal_carries_position_id_and_reason():
    validator = load_execution_validator("deal.schema.json")
    deal = {
        "ticket": 98766,
        "order_ticket": 223344,
        "symbol": "PETR4",
        "volume": 100.0,
        "price": 41.50,
        "position_id": 123456,
        "reason": "sl",
    }
    validator.validate(deal)
    deal["reason"] = "manual"
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(deal)


def test_pending_lookup_outcome_members_declare_closes_intent():
    validator = load_execution_validator("pending-lookup-outcome.schema.json")
    schema = json.loads(
        Path("schema/edge/execution/pending-lookup-outcome.schema.json").read_text(
            encoding="utf-8"
        )
    )
    members = schema["oneOf"]
    assert len(members) == 7
    for member in members:
        assert "closes_intent" in member["required"]
        assert "closes_intent" in member["properties"]

    validator.validate(_example("lookup-outcome-pending-placed.json"))
    validator.validate(_example("lookup-outcome-pending-cancelled.json"))

    open_placed = {"outcome": "placed", "order_ticket": 223344, "closes_intent": True}
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(open_placed)

    final_unavailable = {
        "outcome": "unavailable",
        "reason": "MT5 disconnected",
        "closes_intent": True,
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate(final_unavailable)


def test_lookup_request_kind_defaults_to_deal():
    validator = load_execution_validator("lookup-request.schema.json")
    base = {
        "intent_id": "018f6c38-89ab-7000-8000-000000000002",
        "window_start": "2026-10-29T13:00:00Z",
        "window_end": "2026-10-29T13:05:00Z",
    }
    validator.validate(base)
    validator.validate({**base, "kind": "pending"})
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate({**base, "kind": "protective"})


def test_stream_order_enums_include_pending_types_and_statuses():
    payload = json.loads(
        Path("schema/stream/payloads/execution-common.schema.json").read_text(
            encoding="utf-8"
        )
    )
    defs = payload["$defs"]
    assert defs["ExecutionOrderType"]["enum"] == ["market", "stop", "limit"]
    for status in ("working", "cancelled", "expired"):
        assert status in defs["ExecutionOrderStatus"]["enum"]
