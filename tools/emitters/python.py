"""Python source emitter."""

import re
from typing import Any

from tools.generate import GenerationUnit


def _pascal(name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", name)
    return "".join(word[:1].upper() + word[1:] for word in words) or "GeneratedType"


def _ref_name(ref: str) -> str:
    return _pascal(ref.rsplit("/", 1)[-1].removesuffix(".schema.json"))


def _type_for(schema: dict[str, Any], *, optional: bool = False) -> str:
    if "$ref" in schema:
        result = _ref_name(str(schema["$ref"]))
    elif "const" in schema:
        result = repr(schema["const"])
    elif "enum" in schema:
        values = ", ".join(repr(value) for value in schema["enum"])
        result = f"Literal[{values}]"
    elif "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        non_null = [choice for choice in choices if choice.get("type") != "null"]
        if len(non_null) == 1 and len(non_null) != len(choices):
            return _type_for(non_null[0], optional=True)
        result = " | ".join(_type_for(choice) for choice in choices) or "Any"
    else:
        kind = schema.get("type")
        if kind == "array":
            result = f"list[{_type_for(schema.get('items', {}))}]"
        else:
            result = {
                "boolean": "bool",
                "integer": "int",
                "number": "float",
                "null": "None",
                "object": "dict[str, Any]",
                "string": "str",
            }.get(kind, "Any")
    return f"{result} | None" if optional else result


def _emit_object(name: str, schema: dict[str, Any]) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not isinstance(properties, dict):
        return []
    lines = ["@dataclass(frozen=True)", f"class {name}:"]
    if not properties:
        lines.append("    pass")
        return lines
    for field in sorted(properties):
        field_schema = properties[field]
        annotation = _type_for(field_schema, optional=field not in required)
        default = " = None" if field not in required else ""
        lines.append(f"    {field}: {annotation}{default}")
    return lines


def emit(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    lines = [
        f"# GENERATED FILE - DO NOT EDIT. Source schemas: {source_list}",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Any, Literal",
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
        elif document.get("oneOf"):
            choices = document["oneOf"]
            variants = [
                _type_for(choice)
                for choice in choices
                if isinstance(choice, dict)
            ]
            lines.extend([f"{name} = " + " | ".join(variants or ["Any"])])
        else:
            lines.append(f"{name} = {_type_for(document)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
