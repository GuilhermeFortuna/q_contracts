import json
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

from tools.ml_filter_contracts import (
    FEATURE_ALLOWLIST,
    SERVICE_VALIDATIONS,
    validate_backtest_ml_filter_binding,
    validate_ml_filter_training_request,
    validate_threshold,
)

OPENAPI_PATH = Path(__file__).parent.parent / "schema" / "api" / "openapi.yaml"
JOBS_SUBMISSION = (
    Path(__file__).parent.parent
    / "schema"
    / "api"
    / "examples"
    / "jobs"
    / "submission.json"
)
SERVICE_DOC = (
    Path(__file__).parent.parent / "schema" / "api" / "ml-filter-service-validations.md"
)


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


def test_service_validation_rules_documented() -> None:
    assert SERVICE_DOC.is_file()
    text = SERVICE_DOC.read_text(encoding="utf-8")
    assert "MACrossoverMLFilter" in text
    assert "train_end" in text and "validation_end" in text
    assert "selected_features" in text
    assert "dataset_content_id" in text
    assert len(SERVICE_VALIDATIONS) >= 5


def test_legacy_backtest_submission_without_ml_filter_still_valid(
    openapi_registry: referencing.Registry,
) -> None:
    submission = json.loads(JOBS_SUBMISSION.read_text(encoding="utf-8"))
    assert "ml_filter" not in submission
    validate_schema(openapi_registry, "BacktestRequest", submission)


def test_backtest_ml_filter_binding_service_rules() -> None:
    assert validate_backtest_ml_filter_binding("MACrossover", None) == []
    assert validate_backtest_ml_filter_binding(
        "MACrossover", {"model_version_id": "x", "threshold": 0.5}
    )
    assert validate_backtest_ml_filter_binding("MACrossoverMLFilter", None)
    assert not validate_backtest_ml_filter_binding(
        "MACrossoverMLFilter",
        {"model_version_id": "mv-1", "threshold": 0.5},
    )


@pytest.mark.parametrize("threshold", [-0.1, 1.1, float("nan"), float("inf")])
def test_threshold_rejects_out_of_range_or_non_finite(threshold: float) -> None:
    assert validate_threshold(threshold)


def test_training_request_openapi_accepts_minimal_valid_payload(
    openapi_registry: referencing.Registry,
) -> None:
    payload = {
        "source_run_id": "run-1",
        "train_end": "2024-01-01T12:00:00Z",
        "validation_end": "2024-06-01T12:00:00Z",
        "selected_features": ["close", "side"],
        "algorithms": ["lightgbm"],
        "hyperparameters": {"lightgbm": {"n_estimators": 100}},
        "seed": 42,
    }
    validate_schema(openapi_registry, "MlFilterTrainingRequest", payload)
    assert validate_ml_filter_training_request(payload) == []


def test_training_request_rejects_duplicate_features_and_missing_side() -> None:
    base = {
        "source_run_id": "run-1",
        "train_end": "2024-01-01T12:00:00Z",
        "validation_end": "2024-06-01T12:00:00Z",
        "algorithms": ["lightgbm"],
    }
    dup = {
        **base,
        "selected_features": ["close", "close", "side"],
    }
    assert any("duplicate" in err for err in validate_ml_filter_training_request(dup))

    no_side = {**base, "selected_features": ["close", "open"]}
    assert any("side" in err for err in validate_ml_filter_training_request(no_side))


def test_training_request_rejects_malformed_utc_cutoffs() -> None:
    payload = {
        "source_run_id": "run-1",
        "train_end": "2024-01-01T12:00:00",
        "validation_end": "2024-06-01T12:00:00Z",
        "selected_features": ["close", "side"],
        "algorithms": ["lightgbm"],
    }
    errors = validate_ml_filter_training_request(payload)
    assert any("train_end" in err for err in errors)


def test_training_request_rejects_duplicate_algorithms() -> None:
    payload = {
        "source_run_id": "run-1",
        "train_end": "2024-01-01T12:00:00Z",
        "validation_end": "2024-06-01T12:00:00Z",
        "selected_features": ["close", "side"],
        "algorithms": ["lightgbm", "lightgbm"],
    }
    assert any(
        "algorithms" in err for err in validate_ml_filter_training_request(payload)
    )


def test_nullable_metric_fixture_preserves_unavailable_reason(
    openapi_registry: referencing.Registry,
) -> None:
    metric = {"value": None, "unavailable_reason": "single_class_validation_set"}
    validate_schema(openapi_registry, "MlFilterNullableFloat", metric)
    assert metric["value"] is None
    assert metric["unavailable_reason"]


def test_feature_allowlist_order_is_canonical() -> None:
    assert list(FEATURE_ALLOWLIST) == [
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "real_volume",
        "ma_short",
        "ma_long",
        "delta",
        "prev_delta",
        "side",
    ]


def test_generated_types_include_ml_filter_symbols() -> None:
    root = Path(__file__).parent.parent / "generated"
    api_ts = root / "typescript" / "api.ts"
    api_rs = root / "rust" / "api.rs"
    catalog_py = root / "python" / "q_contracts" / "catalog.py"
    for path, needle in (
        (api_ts, "MlFilterTrainingRequest"),
        (api_rs, "pub struct MlFilterTrainingRequest"),
        (catalog_py, "MlFilterDatasetManifest"),
    ):
        assert path.is_file(), f"missing generated {path}"
        assert needle in path.read_text(encoding="utf-8")


def test_strategy_info_exposes_optional_capability_fields(
    openapi_doc: dict,
) -> None:
    props = openapi_doc["components"]["schemas"]["StrategyInfo"]["properties"]
    for field in (
        "research_only",
        "supports_optimization",
        "supports_walkforward",
        "supports_discovery",
    ):
        assert field in props
