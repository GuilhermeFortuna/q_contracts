from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.generate import GenerationError, plan_units


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
