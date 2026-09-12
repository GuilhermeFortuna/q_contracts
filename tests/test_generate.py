from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

from tools.emitters.python import emit
from tools.emitters.rust import emit as emit_rust
from tools.emitters.typescript import emit as emit_typescript
from tools.generate import (
    LANGUAGES,
    GenerationError,
    generate,
    plan_policy_units,
    plan_units,
)

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


def test_rust_emitter_generates_structs_and_outcome_enums() -> None:
    units = plan_units(SCHEMA_ROOT)
    stream = next(unit for unit in units if unit.name == "stream")
    edge = next(unit for unit in units if unit.name == "edge")

    stream_output = emit_rust(stream)
    edge_output = emit_rust(edge)

    assert stream_output == emit_rust(stream)
    assert stream_output.splitlines()[0].startswith("// ")
    assert "GENERATED FILE - DO NOT EDIT" in stream_output.splitlines()[0]
    assert "schema/stream/envelope.schema.json" in stream_output.splitlines()[0]
    assert "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]" in stream_output
    assert "pub struct StreamEnvelope" in stream_output
    assert "pub seq: i64" in stream_output
    assert "pub epoch: String" in stream_output

    submit_body = re.search(
        r"pub enum SubmitOutcome \{(.*?)\n\}", edge_output, re.DOTALL
    )
    lookup_body = re.search(
        r"pub enum LookupOutcome \{(.*?)\n\}", edge_output, re.DOTALL
    )
    assert submit_body and lookup_body
    assert re.findall(r"^    (\w+)(?:\s*\{|,)", submit_body.group(1), re.MULTILINE) == [
        "Accepted",
        "Rejected",
        "Indeterminate",
    ]
    assert re.findall(r"^    (\w+)(?:\s*\{|,)", lookup_body.group(1), re.MULTILINE) == [
        "Filled",
        "Rejected",
        "NotFound",
        "Unavailable",
    ]


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_generate_produces_byte_identical_trees_on_repeated_runs(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    first_paths = generate(SCHEMA_ROOT, first_root, LANGUAGES)
    second_paths = generate(SCHEMA_ROOT, second_root, LANGUAGES)

    assert [path.relative_to(first_root) for path in first_paths] == sorted(
        path.relative_to(first_root) for path in first_paths
    )
    assert [path.relative_to(first_root) for path in first_paths] == [
        path.relative_to(second_root) for path in second_paths
    ]
    assert _tree_bytes(first_root) == _tree_bytes(second_root)
    assert _tree_bytes(first_root) == _tree_bytes(SCHEMA_ROOT.parent / "generated")
    assert (first_root / "typescript" / "api.ts").is_file()
    assert (first_root / "python" / "q_contracts" / "stream.py").is_file()
    assert (first_root / "rust" / "stream.rs").is_file()


def test_plan_policy_units_emits_topics_unit() -> None:
    units = plan_policy_units(SCHEMA_ROOT)
    assert len(units) == 1
    assert units[0].name == "topics"
    assert units[0].sources == (Path("schema/stream/topics.yaml"),)


def test_generate_emits_policy_for_all_languages(tmp_path: Path) -> None:
    out_root = tmp_path / "generated"
    generate(SCHEMA_ROOT, out_root, LANGUAGES)

    assert (out_root / "python" / "q_contracts" / "topics.py").is_file()
    assert (out_root / "typescript" / "topics.ts").is_file()
    assert (out_root / "rust" / "topics.rs").is_file()


def test_generated_python_topics_values() -> None:
    from generated.python.q_contracts.topics import TOPICS

    assert TOPICS["quotes"].retention_entries == 100000
    assert TOPICS["bars.forming"].coalesce_key == ("symbol", "timeframe")
    assert TOPICS["jobs.progress"].coalesce_key == ("kind", "job_id")
