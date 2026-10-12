"""BacktestStatusResponse carries optional live progress without breaking older statuses."""

from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml

ROOT = Path(__file__).parent.parent
OPENAPI_PATH = ROOT / "schema" / "api" / "openapi.yaml"

PROGRESS_FIELDS = (
    "phase",
    "progress",
    "message",
    "started_at",
    "updated_at",
    "simulated_until",
    "bars_total",
    "candles_replayed",
    "candles_substituted",
)


@pytest.fixture(scope="module")
def registry() -> referencing.Registry:
    doc = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    resource = referencing.Resource.from_contents(
        doc, default_specification=referencing.jsonschema.DRAFT202012
    )
    return referencing.Registry().with_resource("urn:openapi", resource)


def validator(registry: referencing.Registry) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        {"$ref": "urn:openapi#/components/schemas/BacktestStatusResponse"},
        registry=registry,
    )


def live_status(**overrides) -> dict:
    status = {
        "run_id": "5b1f0c2e-7a3d-4c1e-9d0f-2a6b8c4e1f10",
        "status": "running",
        "error": None,
        "phase": "simulating",
        "progress": 0.42,
        "message": "Replaying ticks · 2023-03-22",
        "started_at": "2026-10-12T07:14:21Z",
        "updated_at": "2026-10-12T07:17:42Z",
        "simulated_until": "2023-03-22T10:00:00Z",
        "bars_total": 35040,
        "candles_replayed": 250,
        "candles_substituted": 3,
    }
    status.update(overrides)
    return status


def test_status_without_progress_fields_still_validates(registry):
    legacy = {"run_id": "run-1", "status": "completed", "error": None}

    validator(registry).validate(legacy)


def test_status_with_every_progress_field_null_validates(registry):
    nulls = {
        "run_id": "run-1",
        "status": "completed",
        "error": None,
        **{name: None for name in PROGRESS_FIELDS},
    }

    validator(registry).validate(nulls)


def test_live_status_validates_with_every_progress_field(registry):
    validator(registry).validate(live_status())


@pytest.mark.parametrize(
    "phase", ["queued", "loading_data", "preparing", "simulating", "saving"]
)
def test_each_documented_phase_validates(registry, phase):
    validator(registry).validate(live_status(phase=phase))


@pytest.mark.parametrize(
    "override",
    [
        {"phase": "warming"},
        {"progress": 1.5},
        {"progress": -0.1},
        {"bars_total": 1.5},
    ],
)
def test_out_of_contract_progress_values_are_rejected(registry, override):
    with pytest.raises(jsonschema.ValidationError):
        validator(registry).validate(live_status(**override))


def test_generated_typescript_and_rust_expose_the_progress_fields():
    ts = (ROOT / "generated" / "typescript" / "api.ts").read_text(encoding="utf-8")
    rs = (ROOT / "generated" / "rust" / "api.rs").read_text(encoding="utf-8")

    assert (
        'phase?: "queued" | "loading_data" | "preparing" | "simulating" | "saving" | null'
        in ts
    )
    assert "progress?: number | null" in ts
    assert "started_at?: string | null" in ts
    assert "pub phase: Option<String>" in rs
    assert "pub progress: Option<f64>" in rs
