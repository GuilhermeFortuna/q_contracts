import json
from pathlib import Path

import jsonschema
import referencing
import yaml

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "schema"


def load_validator(schema_path: Path) -> jsonschema.Draft202012Validator:
    resources = []
    for path in SCHEMA.rglob("*.schema.json"):
        document = json.loads(path.read_text())
        if "$schema" not in document:
            continue
        resource = referencing.Resource.from_contents(document)
        resources.extend(
            [
                (path.name, resource),
                (path.as_posix(), resource),
                (f"../{path.name}", resource),
            ]
        )
        if "$id" in document:
            resources.extend(
                [
                    (document["$id"], resource),
                    (f"{document['$id']}.schema.json", resource),
                ]
            )
    registry = referencing.Registry().with_resources(resources)
    schema = json.loads(schema_path.read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry)


def test_trade_arrow_schema_declares_utc_fields_and_occurrence_identity():
    schema = json.loads((SCHEMA / "api/arrow/trades.schema.json").read_text())
    fields = {field["name"]: field for field in schema["fields"]}

    assert fields["time_msc"]["tz"] == "UTC"
    assert fields["time_msc"]["type"] == "timestamp[ms]"
    assert fields["price"]["type"] == "float64"
    assert fields["volume"]["type"] == "float64"
    assert fields["raw_flags"]["type"] == "int32"
    assert fields["occurrence"]["type"] == "int64"
    assert fields["volume_real"]["type"] == "float64"
    assert fields["volume_real"]["nullable"] is True


def test_trade_topics_are_retained_without_coalescing_and_status_coalesces():
    topics = yaml.safe_load((SCHEMA / "stream/topics.yaml").read_text())["topics"]

    trades = topics["trades"]
    assert trades["retention"] == {"duration": "P1D", "entries": 200000}
    assert trades["backpressure"] == {"coalesce": False, "on_overflow": "lag"}
    assert trades["replay"] == "retention_only"
    assert "4096" in trades["notes"]

    status = topics["trades.status"]
    assert status["retention"] == {"duration": "PT1H", "entries": 10000}
    assert status["backpressure"]["coalesce_key"] == ["symbol"]


def test_trade_snapshot_examples_validate():
    path = SCHEMA / "stream/replay/trade-snapshot.schema.json"
    assert path.is_file()
    schema = json.loads(path.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = load_validator(path)
    for name in ("trade-snapshot", "trade-snapshot-partial"):
        example = json.loads((SCHEMA / f"stream/examples/{name}.json").read_text())
        assert list(validator.iter_errors(example)) == []


def test_identical_trade_rows_remain_distinct_by_source_occurrence():
    batch = json.loads((SCHEMA / "stream/examples/trade-batch.json").read_text())
    assert batch["rows"][0] | {"occurrence": 0} == batch["rows"][1] | {"occurrence": 0}
    assert [row["occurrence"] for row in batch["rows"]] == [0, 1]
    context_path = SCHEMA / "stream/payloads/trade-delivery-context.schema.json"
    context_schema = json.loads(context_path.read_text())
    context = {name: batch[name] for name in context_schema["required"]}
    assert list(load_validator(context_path).iter_errors(context)) == []
    topics = yaml.safe_load((SCHEMA / "stream/topics.yaml").read_text())["topics"]
    assert topics["trades"]["context_schema"] == (
        "schema/stream/payloads/trade-delivery-context.schema.json"
    )


def test_trade_history_openapi_declares_pending_expired_and_headers():
    api = yaml.safe_load((SCHEMA / "api/openapi.yaml").read_text())
    paths = api["paths"]
    snapshot = paths["/api/v1/market/trades/snapshot"]["get"]["responses"]
    history = paths["/api/v1/market/trades/history"]["get"]["responses"]

    assert {"200", "202", "404", "503"} <= set(snapshot)
    assert snapshot["202"]["headers"]["Retry-After"]["schema"]["const"] == 1
    assert {"200", "404", "410", "503"} <= set(history)
    headers = history["200"]["headers"]
    assert all(name.startswith("X-Q-Trade-") for name in headers)
    assert "X-Q-Trade-Frozen-Seq" in headers


def test_trade_status_and_pending_examples_cover_range_and_classification():
    status_schema = json.loads(
        (SCHEMA / "stream/payloads/trade-source-status.schema.json").read_text()
    )
    assert "classification_coverage" in status_schema["required"]
    assert "coverage_reason" in status_schema["required"]
    assert "coverage_reason" in status_schema["properties"]
    pending_path = SCHEMA / "stream/replay/trade-history-pending.schema.json"
    pending = json.loads(
        (SCHEMA / "stream/examples/trade-history-pending.json").read_text()
    )
    assert list(load_validator(pending_path).iter_errors(pending)) == []
    error_validator = load_validator(SCHEMA / "api/error.schema.json")
    for name in ("trade-history-expired", "trade-source-unavailable"):
        error = json.loads((SCHEMA / f"stream/examples/{name}.json").read_text())
        assert list(error_validator.iter_errors(error)) == []
    status_path = SCHEMA / "stream/payloads/trade-source-status.schema.json"
    status_example = json.loads(
        (SCHEMA / "stream/examples/trade-source-status.json").read_text()
    )
    assert list(load_validator(status_path).iter_errors(status_example)) == []


def test_trade_history_page_metadata_example_matches_header_contract():
    headers_path = SCHEMA / "stream/replay/trade-history-headers.schema.json"
    headers = json.loads(
        (SCHEMA / "stream/examples/trade-history-page-metadata.json").read_text()
    )
    assert list(load_validator(headers_path).iter_errors(headers)) == []
    api = yaml.safe_load((SCHEMA / "api/openapi.yaml").read_text())
    wire_headers = set(
        api["paths"]["/api/v1/market/trades/history"]["get"]["responses"]["200"][
            "headers"
        ]
    )
    declared_headers = {
        field["http_header"]
        for field in json.loads(headers_path.read_text())["properties"].values()
    }
    assert wire_headers == declared_headers


def test_gateway_trade_range_is_utc_and_uses_all_ticks_with_explicit_coverage():
    gateway = yaml.safe_load((SCHEMA / "edge/data-gateway.yaml").read_text())
    trades = gateway["endpoints"]["/v1/trades"]
    assert trades["retrieval"]["flags"] == "COPY_TICKS_ALL"
    assert trades["query_parameters"]["end_utc"]["description"].startswith("Exclusive")
    filtering = trades["retrieval"]["filtering"]
    assert set(filtering["required_any_flags"]) == {"LAST", "VOLUME", "BUY", "SELL"}
    assert filtering["require_finite_positive"] == ["last", "selected_volume"]
    assert filtering["exclude_quote_only_even_with_carried_last_volume"]
    assert filtering["both_or_neither_aggressor_flags"] == "eligible_with_unknown_side"
    assert "range_complete" in trades["response"]["metadata"]


def test_snapshot_context_mismatch_fixtures_are_rejected():
    from tools.validate import trade_snapshot_context_errors

    for path in sorted((ROOT / "tests/fixtures/trades").glob("*-mismatch.json")):
        payload = json.loads(path.read_text())
        assert trade_snapshot_context_errors(payload), path.name


def test_openapi_snapshot_coverage_matches_trade_source_status_contract():
    api = yaml.safe_load((SCHEMA / "api/openapi.yaml").read_text())
    openapi_status = api["components"]["schemas"]["TradeSourceStatus"]
    source_status = json.loads(
        (SCHEMA / "stream/payloads/trade-source-status.schema.json").read_text()
    )
    assert set(openapi_status["required"]) == set(source_status["required"])
    assert set(openapi_status["properties"]) == set(source_status["properties"])
    assert (
        openapi_status["additionalProperties"] is source_status["additionalProperties"]
    )
    for name, source_property in source_status["properties"].items():
        if name == "last_trade_watermark":
            continue
        api_property = openapi_status["properties"][name]
        for keyword in ("type", "enum", "format", "minimum", "minLength"):
            assert api_property.get(keyword) == source_property.get(keyword), name
    api_watermark = openapi_status["properties"]["last_trade_watermark"]
    watermark_schema = json.loads(
        (SCHEMA / "stream/replay/trade-watermark.schema.json").read_text()
    )
    assert api_watermark["type"] == watermark_schema["type"]
    assert api_watermark["required"] == watermark_schema["required"]
    assert api_watermark["properties"] == watermark_schema["properties"]
    snapshot = api["components"]["schemas"]["TradeSnapshotResponse"]
    assert snapshot["properties"]["coverage"]["$ref"].endswith("/TradeSourceStatus")


def test_gateway_volume_array_matches_raw_arrow_volume_semantics():
    gateway = yaml.safe_load((SCHEMA / "edge/data-gateway.yaml").read_text())
    trades = gateway["endpoints"]["/v1/trades"]
    assert trades["response"]["arrays"]["volume"]["description"] == (
        "Raw provider tick volume."
    )
    assert trades["response"]["arrays"]["volume_real"]["optional"] is True
    assert trades["response"]["metadata"]["volume_unit"]["describes"] == (
        "volume_field"
    )
