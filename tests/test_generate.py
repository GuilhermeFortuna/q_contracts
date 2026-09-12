from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.generate import GenerationError, plan_units
from tools.emitters.python import emit
from tools.emitters.typescript import emit as emit_typescript


SCHEMA_ROOT = Path(__file__).parents[1] / "schema"


def test_plan_units_is_sorted_and_stable_for_the_real_schema_tree() -> None:
    first = plan_units(SCHEMA_ROOT)
    second = plan_units(SCHEMA_ROOT)

    assert first == second
    assert [unit.name for unit in first] == sorted(unit.name for unit in first)
    assert [unit.name for unit in first] == ["api", "catalog", "edge", "stream"]


def test_plan_units_rejects_an_unsupported_dialect_with_path_and_language(
    tmp_path: Path,
) -> None:
    schema_root = tmp_path / "schema"
    stream_root = schema_root / "stream"
    stream_root.mkdir(parents=True)
    unsupported = stream_root / "unsupported.schema.json"
    unsupported.write_text(
        json.dumps(
            {
                "$schema": "https://example.com/unsupported-schema",
                "$id": "stream/unsupported",
                "type": "object",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GenerationError) as exc_info:
        plan_units(schema_root)

    message = str(exc_info.value)
    assert "schema/stream/unsupported.schema.json" in message
    assert "python" in message


def test_python_emitter_generates_the_stream_envelope_deterministically() -> None:
    stream = next(unit for unit in plan_units(SCHEMA_ROOT) if unit.name == "stream")

    first = emit(stream)
    second = emit(stream)

    assert first == second
    assert first.splitlines()[0].startswith("# ")
    assert "GENERATED FILE - DO NOT EDIT" in first.splitlines()[0]
    assert "schema/stream/envelope.schema.json" in first.splitlines()[0]
    assert "class StreamEnvelope:" in first
    for field in (
        "topic",
        "schema_major",
        "seq",
        "epoch",
        "producer_id",
        "origin_ts",
        "payload_kind",
        "payload_schema",
        "payload",
    ):
        assert f"    {field}:" in first
    assert "    seq: int" in first
    assert "    epoch: str" in first


def test_typescript_emitter_generates_the_stream_envelope_and_optional_fields() -> None:
    units = plan_units(SCHEMA_ROOT)
    stream = next(unit for unit in units if unit.name == "stream")

    first = emit_typescript(stream)
    second = emit_typescript(stream)

    assert first == second
    assert first.splitlines()[0].startswith("// ")
    assert "GENERATED FILE - DO NOT EDIT" in first.splitlines()[0]
    assert "schema/stream/envelope.schema.json" in first.splitlines()[0]
    assert "export interface StreamEnvelope" in first
    for field in (
        "topic",
        "schema_major",
        "seq",
        "epoch",
        "producer_id",
        "origin_ts",
        "payload_kind",
        "payload_schema",
        "payload",
    ):
        assert f"  {field}:" in first
    assert "  seq: number" in first
    assert "  epoch: string" in first
    assert "export interface CursorExpiredFrame" in first
    assert "  cursor?: string" in first
    assert "cursor: string | undefined" not in first
