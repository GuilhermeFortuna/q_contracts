"""Python source emitter."""

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


def _type_for(
    schema: dict[str, Any],
    ref_map: dict[str, str],
    *,
    optional: bool = False,
    quote_refs: bool = False,
) -> str:
    if "$ref" in schema:
        ref_name = _ref_name(str(schema["$ref"]), ref_map)
        result = f'"{ref_name}"' if quote_refs else ref_name
    elif "const" in schema:
        result = repr(schema["const"])
    elif "enum" in schema:
        values = [json.dumps(value) for value in schema["enum"]]
        inline = ", ".join(values)
        if len(f"Literal[{inline}]") <= 88:
            result = f"Literal[{inline}]"
        else:
            result = (
                "Literal[\n"
                + "".join(f"        {value},\n" for value in values)
                + "    ]"
            )
    elif "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        non_null = [choice for choice in choices if choice.get("type") != "null"]
        if len(non_null) == 1 and len(non_null) != len(choices):
            return _type_for(non_null[0], ref_map, optional=True, quote_refs=quote_refs)
        result = (
            " | ".join(
                _type_for(choice, ref_map, quote_refs=quote_refs) for choice in choices
            )
            or "Any"
        )
    else:
        kind = schema.get("type")
        if isinstance(kind, list):
            result = " | ".join(
                _type_for({"type": item}, ref_map, quote_refs=quote_refs)
                for item in kind
            )
        elif kind == "array":
            result = f"list[{_type_for(schema.get('items', {}), ref_map, quote_refs=quote_refs)}]"
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


def _emit_object(
    name: str, schema: dict[str, Any], ref_map: dict[str, str]
) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not isinstance(properties, dict):
        return []
    lines = ["@dataclass(frozen=True)", f"class {name}:"]
    if not properties:
        lines.append("    pass")
        return lines
    for field in sorted(properties, key=lambda value: (value not in required, value)):
        field_schema = properties[field]
        annotation = _type_for(field_schema, ref_map, optional=field not in required)
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
        elif document.get("oneOf"):
            choices = document["oneOf"]
            variants = [
                _type_for(choice, ref_map)
                for choice in choices
                if isinstance(choice, dict)
            ]
            lines.extend([f"{name} = " + " | ".join(variants or ["Any"])])
        else:
            lines.append(f"{name} = {_type_for(document, ref_map, quote_refs=True)}")
        lines.extend(["", ""])
    return "\n".join(lines).rstrip() + "\n"
