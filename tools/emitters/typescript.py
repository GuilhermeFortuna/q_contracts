"""TypeScript source emitter."""

import json
import re
from typing import Any

from tools.generate import GenerationUnit


def _pascal(name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", name)
    return "".join(word[:1].upper() + word[1:] for word in words) or "GeneratedType"


def _ref_name(ref: str) -> str:
    return _pascal(ref.rsplit("/", 1)[-1].removesuffix(".schema.json"))


def _literal(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def _type_for(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return _ref_name(str(schema["$ref"]))
    if "const" in schema:
        return _literal(schema["const"])
    if "enum" in schema:
        return " | ".join(_literal(value) for value in schema["enum"]) or "never"
    if "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        return " | ".join(_type_for(choice) for choice in choices) or "unknown"
    kind = schema.get("type")
    if kind == "array":
        return f"Array<{_type_for(schema.get('items', {}))}>"
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
            fields.append(f"{field}{suffix}: {_type_for(properties[field])}")
        return "{ " + "; ".join(fields) + " }"
    if kind == "string":
        return "string"
    return "unknown"


def _emit_object(name: str, schema: dict[str, Any]) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not isinstance(properties, dict):
        return []
    lines = [f"export interface {name} {{"]
    for field in sorted(properties):
        suffix = "" if field in required else "?"
        lines.append(f"  {field}{suffix}: {_type_for(properties[field])}")
    lines.append("}")
    return lines


def emit(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    lines = [
        f"// GENERATED FILE - DO NOT EDIT. Source schemas: {source_list}",
        "",
    ]
    definitions: list[tuple[str, dict[str, Any]]] = []
    for document in unit.documents:
        title = document.get("title")
        if isinstance(title, str) and title:
            definitions.append((_pascal(title), document))
    for name, document in sorted(definitions):
        if document.get("type") == "object":
            lines.extend(_emit_object(name, document))
        else:
            lines.append(f"export type {name} = {_type_for(document)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
