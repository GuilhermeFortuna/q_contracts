"""Rust source emitter."""

import re
from typing import Any

from tools.generate import GenerationUnit


RUST_KEYWORDS = frozenset(
    {
        "as",
        "async",
        "await",
        "break",
        "const",
        "continue",
        "crate",
        "dyn",
        "else",
        "enum",
        "extern",
        "false",
        "fn",
        "for",
        "if",
        "impl",
        "in",
        "let",
        "loop",
        "match",
        "mod",
        "move",
        "mut",
        "pub",
        "ref",
        "return",
        "self",
        "Self",
        "static",
        "struct",
        "super",
        "trait",
        "true",
        "type",
        "unsafe",
        "use",
        " where",
        "while",
        "yield",
    }
)


def _pascal(name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", name)
    return "".join(word[:1].upper() + word[1:] for word in words) or "GeneratedType"


def _ref_name(ref: str) -> str:
    return _pascal(ref.rsplit("/", 1)[-1].removesuffix(".schema.json"))


def _field_name(name: str) -> str:
    return f"r#{name}" if name in RUST_KEYWORDS else name


def _type_for(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return _ref_name(str(schema["$ref"]))
    if "const" in schema or "enum" in schema:
        return "String"
    if "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        non_null = [choice for choice in choices if choice.get("type") != "null"]
        if len(non_null) == 1 and len(non_null) != len(choices):
            return f"Option<{_type_for(non_null[0])}>"
        return "serde_json::Value"
    kind = schema.get("type")
    if kind == "array":
        return f"Vec<{_type_for(schema.get('items', {}))}>"
    if kind == "boolean":
        return "bool"
    if kind == "integer":
        return "i64"
    if kind == "number":
        return "f64"
    if kind == "string":
        return "String"
    return "serde_json::Value"


def _emit_object(name: str, schema: dict[str, Any]) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not isinstance(properties, dict):
        return []
    lines = [
        "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
        f"pub struct {name} {{",
    ]
    for field in sorted(properties):
        rust_field = _field_name(field)
        if rust_field != field:
            lines.append(f'    #[serde(rename = "{field}")]')
        annotation = _type_for(properties[field])
        if field not in required and not annotation.startswith("Option<"):
            annotation = f"Option<{annotation}>"
        lines.append(f"    pub {rust_field}: {annotation},")
    lines.append("}")
    return lines


def _emit_outcome(name: str, schema: dict[str, Any]) -> list[str]:
    lines = [
        "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
        f"pub enum {name} {{",
    ]
    for branch in schema.get("oneOf", []):
        properties = branch.get("properties", {})
        outcome = properties.get("outcome", {}).get("const")
        variant = _pascal(str(outcome)) if outcome is not None else "Variant"
        fields = []
        required = set(branch.get("required", []))
        for field in sorted(properties):
            if field == "outcome":
                continue
            annotation = _type_for(properties[field])
            if field not in required and not annotation.startswith("Option<"):
                annotation = f"Option<{annotation}>"
            fields.append(f"        pub {_field_name(field)}: {annotation},")
        if fields:
            lines.append(f"    {variant} {{")
            lines.extend(fields)
            lines.append("    },")
        else:
            lines.append(f"    {variant},")
    lines.append("}")
    return lines


def emit(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    lines = [
        f"// GENERATED FILE - DO NOT EDIT. Source schemas: {source_list}",
        "use serde::{Deserialize, Serialize};",
        "",
    ]
    definitions: list[tuple[str, dict[str, Any]]] = []
    for document in unit.documents:
        title = document.get("title")
        if isinstance(title, str) and title:
            definitions.append((_pascal(title), document))
    for name, document in sorted(definitions):
        if document.get("oneOf") and all(
            isinstance(branch, dict)
            and branch.get("properties", {}).get("outcome", {}).get("const")
            for branch in document["oneOf"]
        ):
            lines.extend(_emit_outcome(name, document))
        elif document.get("type") == "object":
            lines.extend(_emit_object(name, document))
        elif document.get("type") == "array":
            lines.append(f"pub type {name} = {_type_for(document)};")
        else:
            lines.append(f"pub type {name} = {_type_for(document)};")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
