"""TypeScript source emitter."""

import json
import re
from typing import Any

from tools.generate import GenerationUnit


def _pascal(name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", name)
    return "".join(word[:1].upper() + word[1:] for word in words) or "GeneratedType"


def _ref_name(ref: str, ref_map: dict[str, str]) -> str:
    stem = ref.rsplit("/", 1)[-1].removesuffix(".schema.json")
    return ref_map.get(stem, _pascal(stem))


def _literal(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def _type_for(schema: dict[str, Any], ref_map: dict[str, str]) -> str:
    if "$ref" in schema:
        return _ref_name(str(schema["$ref"]), ref_map)
    if "const" in schema:
        return _literal(schema["const"])
    if "enum" in schema:
        return " | ".join(_literal(value) for value in schema["enum"]) or "never"
    if "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        return " | ".join(_type_for(choice, ref_map) for choice in choices) or "unknown"
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(_type_for({"type": item}, ref_map) for item in kind)
    if kind == "array":
        return f"Array<{_type_for(schema.get('items', {}), ref_map)}>"
    if kind == "boolean":
        return "boolean"
    if kind == "integer" or kind == "number":
        return "number"
    if kind == "null":
        return "null"
    if kind == "object":
        properties = schema.get("properties")
        if not isinstance(properties, dict) or not properties:
            return "Record<string, unknown>"
        fields = []
        required = set(schema.get("required", []))
        for field in sorted(properties):
            suffix = "" if field in required else "?"
            fields.append(f"{field}{suffix}: {_type_for(properties[field], ref_map)}")
        return "{ " + "; ".join(fields) + " }"
    if kind == "string":
        return "string"
    return "unknown"


def _emit_object(
    name: str, schema: dict[str, Any], ref_map: dict[str, str]
) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not isinstance(properties, dict):
        return []
    lines = [f"export interface {name} {{"]
    for field in sorted(properties):
        suffix = "" if field in required else "?"
        lines.append(f"  {field}{suffix}: {_type_for(properties[field], ref_map)}")
    lines.append("}")
    return lines


def _emit_topic_policies(topics: dict[str, Any]) -> list[str]:
    lines = [
        "export interface TopicRetention {",
        "  duration: string",
        "  entries: number",
        "}",
        "",
        "export interface TopicBackpressure {",
        "  coalesce: boolean",
        "  coalesce_key?: Array<string>",
        "  on_overflow: string",
        "}",
        "",
        "export interface TopicPolicy {",
        "  backpressure: TopicBackpressure",
        "  class: string",
        "  notes?: string",
        "  payload_schema: string",
        "  replay: string",
        "  retention: TopicRetention",
        "}",
        "",
        "export const TOPIC_NAMES: Array<string> = [",
    ]
    for topic_name in sorted(topics):
        lines.append(f'  "{topic_name}",')
    lines.extend(
        [
            "]",
            "",
            "export const TOPIC_POLICIES: Record<string, TopicPolicy> = {",
        ]
    )
    topic_items = sorted(topics.items())
    for i, (topic_name, entry) in enumerate(topic_items):
        bp = entry.get("backpressure", {})
        coalesce = "true" if bp.get("coalesce", False) else "false"
        on_overflow = json.dumps(bp.get("on_overflow", ""))
        coalesce_key = bp.get("coalesce_key")
        ret = entry.get("retention", {})
        duration = json.dumps(ret.get("duration", ""))
        entries = ret.get("entries", 0)
        cls = json.dumps(entry.get("class", ""))
        ps = json.dumps(entry.get("payload_schema", ""))
        replay = json.dumps(entry.get("replay", ""))
        notes = entry.get("notes")

        lines.extend(
            [
                f'  "{topic_name}": {{',
                "    backpressure: {",
                f"      coalesce: {coalesce},",
            ]
        )
        if coalesce_key is not None:
            ck_json = json.dumps(coalesce_key)
            lines.append(f"      coalesce_key: {ck_json},")
        lines.extend(
            [
                f"      on_overflow: {on_overflow}",
                "    },",
                f"    class: {cls},",
            ]
        )
        if notes is not None:
            lines.append(f"    notes: {json.dumps(notes)},")
        lines.extend(
            [
                f"    payload_schema: {ps},",
                f"    replay: {replay},",
                "    retention: {",
                f"      duration: {duration},",
                f"      entries: {entries}",
                "    }",
                "  }" + ("," if i < len(topic_items) - 1 else ""),
            ]
        )
    lines.append("}")
    return lines


def emit(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    lines = [
        f"// GENERATED FILE - DO NOT EDIT. Source schemas: {source_list}",
        "",
    ]
    ref_map = {
        path.name.removesuffix(".schema.json"): _pascal(document.get("title", ""))
        for path, document in zip(unit.sources, unit.documents, strict=False)
        if path.name.endswith(".schema.json") and isinstance(document.get("title"), str)
    }
    definitions: list[tuple[str, dict[str, Any]]] = []
    topics_doc: dict[str, Any] | None = None
    for document in unit.documents:
        if document.get("$type") == "topics_policy":
            topics_doc = document
            continue
        title = document.get("title")
        if isinstance(title, str) and title:
            definitions.append((_pascal(title), document))
    for name, document in sorted(definitions):
        if document.get("type") == "object":
            lines.extend(_emit_object(name, document, ref_map))
        else:
            lines.append(f"export type {name} = {_type_for(document, ref_map)}")
        lines.append("")
    if topics_doc is not None:
        lines.extend(_emit_topic_policies(topics_doc.get("topics", {})))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
