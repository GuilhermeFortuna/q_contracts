from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tools.emitters.python import emit
from tools.emitters.rust import emit as emit_rust
from tools.emitters.typescript import emit as emit_typescript
from tools.generate import LANGUAGES, GenerationError, generate, plan_units

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


def test_python_emitter_generates_topic_policies_as_data() -> None:
    units = plan_units(SCHEMA_ROOT)
    stream = next(unit for unit in units if unit.name == "stream")
    output = emit(stream)

    assert "schema/stream/topics.yaml" in output.splitlines()[0]
    assert "class TopicPolicy:" in output
    assert "class TopicRetention:" in output
    assert "class TopicBackpressure:" in output
    assert "TOPIC_NAMES: tuple[str, ...] = (" in output
    assert "TOPIC_POLICIES: dict[str, TopicPolicy] = {" in output
    assert '"orders": TopicPolicy(' in output
    assert '"quotes": TopicPolicy(' in output
    assert 'class_="durable"' in output
    assert 'class_="ephemeral"' in output
    assert "JobProgressPayload" in output
    assert "JobTerminalPayload" in output
    assert "SubscriptionRejectedFrame" in output
    assert "HistoryResponse" in output
    assert "LatestResponse" in output
    assert "WatermarkResponse" in output
    assert "WebSocketBinaryHeader" in output


def test_typescript_emitter_generates_topic_policies_as_data() -> None:
    units = plan_units(SCHEMA_ROOT)
    stream = next(unit for unit in units if unit.name == "stream")
    output = emit_typescript(stream)

    assert "schema/stream/topics.yaml" in output.splitlines()[0]
    assert "export interface TopicPolicy {" in output
    assert "export const TOPIC_NAMES: Array<string> =" in output
    assert "export const TOPIC_POLICIES: Record<string, TopicPolicy> = {" in output
    assert '"bars.completed": {' in output
    assert "export interface JobProgressPayload {" in output
    assert "export interface JobTerminalPayload {" in output
    assert "export interface HistoryResponse {" in output
    assert "export interface LatestResponse {" in output
    assert "export interface WatermarkResponse {" in output
    assert "export interface WebSocketBinaryHeader {" in output


def test_rust_emitter_generates_topic_policies_as_data() -> None:
    units = plan_units(SCHEMA_ROOT)
    stream = next(unit for unit in units if unit.name == "stream")
    output = emit_rust(stream)

    assert "schema/stream/topics.yaml" in output.splitlines()[0]
    assert "pub struct TopicPolicy {" in output
    assert "pub const TOPIC_NAMES: &[&str] = &[" in output
    assert "pub fn get_topic_policy(topic: &str) -> Option<TopicPolicy> {" in output
    assert "pub fn all_topic_policies() -> Vec<(&'static str, TopicPolicy)> {" in output
    assert '"orders" => Some(TopicPolicy {' in output
    assert "pub struct JobProgressPayload {" in output
    assert "pub struct JobTerminalPayload {" in output
    assert "pub struct HistoryResponse {" in output
    assert "pub struct LatestResponse {" in output
    assert "pub struct WatermarkResponse {" in output
    assert "pub struct WebSocketBinaryHeader {" in output
