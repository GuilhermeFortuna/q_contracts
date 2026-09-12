"""TypeScript source emitter."""

import json
import re
from typing import Any

from tools.generate import HEADER, GenerationUnit


def _emit_topics(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    document = unit.documents[0]
    topics_data = document.get("topics", {})

    lines = [
        f"// {HEADER}. Source schemas: {source_list}",
        "",
        "export interface TopicPolicy {",
        "  name: string",
        '  topic_class: "durable" | "ephemeral"',
        "  retention_duration: string",
        "  retention_entries: number",
        "  coalesce_key: readonly string[]",
        '  on_overflow: "lag" | "coalesce"',
        '  replay: "unbounded" | "retention_only"',
        "  payload_schema: string",
        "}",
        "",
        "export const TOPICS: Readonly<Record<string, TopicPolicy>> = {",
    ]

    for name in sorted(topics_data):
        entry = topics_data[name]
        topic_class = json.dumps(entry.get("class"))
        retention = entry.get("retention", {})
        duration = json.dumps(retention.get("duration", ""))
        entries = retention.get("entries", 0)
        backpressure = entry.get("backpressure", {})
        coalesce = backpressure.get("coalesce", False)
        coalesce_key = list(backpressure.get("coalesce_key", [])) if coalesce else []
        coalesce_key_json = json.dumps(coalesce_key)
        on_overflow = json.dumps(backpressure.get("on_overflow", "lag"))
        replay = json.dumps(entry.get("replay", "unbounded"))
        payload_schema = json.dumps(entry.get("payload_schema", ""))

        lines.append(f'  "{name}": {{')
        lines.append(f'    name: "{name}",')
        lines.append(f"    topic_class: {topic_class},")
        lines.append(f"    retention_duration: {duration},")
        lines.append(f"    retention_entries: {entries},")
        lines.append(f"    coalesce_key: {coalesce_key_json},")
        lines.append(f"    on_overflow: {on_overflow},")
        lines.append(f"    replay: {replay},")
        lines.append(f"    payload_schema: {payload_schema},")
        lines.append("  },")

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


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


def emit(unit: GenerationUnit) -> str:
    if unit.name == "topics":
        return _emit_topics(unit)
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
    for document in unit.documents:
        title = document.get("title")
        if isinstance(title, str) and title:
            definitions.append((_pascal(title), document))
    for name, document in sorted(definitions):
        if document.get("type") == "object":
            lines.extend(_emit_object(name, document, ref_map))
        else:
            lines.append(f"export type {name} = {_type_for(document, ref_map)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
