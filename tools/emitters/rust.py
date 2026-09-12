"""Rust source emitter."""

import json
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


def _ref_name(ref: str, ref_map: dict[str, str]) -> str:
    stem = ref.rsplit("/", 1)[-1].removesuffix(".schema.json")
    return ref_map.get(stem, _pascal(stem))


def _field_name(name: str) -> str:
    return f"r#{name}" if name in RUST_KEYWORDS else name


def _type_for(schema: dict[str, Any], ref_map: dict[str, str]) -> str:
    if "$ref" in schema:
        return _ref_name(str(schema["$ref"]), ref_map)
    if "const" in schema or "enum" in schema:
        return "String"
    if "oneOf" in schema or "anyOf" in schema:
        choices = schema.get("oneOf", schema.get("anyOf", []))
        non_null = [choice for choice in choices if choice.get("type") != "null"]
        if len(non_null) == 1 and len(non_null) != len(choices):
            return f"Option<{_type_for(non_null[0], ref_map)}>"
        return "serde_json::Value"
    kind = schema.get("type")
    if isinstance(kind, list):
        return "serde_json::Value"
    if kind == "array":
        return f"Vec<{_type_for(schema.get('items', {}), ref_map)}>"
    if kind == "boolean":
        return "bool"
    if kind == "integer":
        return "i64"
    if kind == "number":
        return "f64"
    if kind == "string":
        return "String"
    return "serde_json::Value"


def _emit_object(
    name: str, schema: dict[str, Any], ref_map: dict[str, str]
) -> list[str]:
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
        annotation = _type_for(properties[field], ref_map)
        if field not in required and not annotation.startswith("Option<"):
            annotation = f"Option<{annotation}>"
        lines.append(f"    pub {rust_field}: {annotation},")
    lines.append("}")
    return lines


def _emit_outcome(
    name: str, schema: dict[str, Any], ref_map: dict[str, str]
) -> list[str]:
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
            annotation = _type_for(properties[field], ref_map)
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


def _emit_topic_policies(topics: dict[str, Any]) -> list[str]:
    lines = [
        "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
        "pub struct TopicRetention {",
        "    pub duration: String,",
        "    pub entries: i64,",
        "}",
        "",
        "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
        "pub struct TopicBackpressure {",
        "    pub coalesce: bool,",
        "    pub coalesce_key: Option<Vec<String>>,",
        "    pub on_overflow: String,",
        "}",
        "",
        "#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
        "pub struct TopicPolicy {",
        "    pub backpressure: TopicBackpressure,",
        '    #[serde(rename = "class")]',
        "    pub r#class: String,",
        "    pub notes: Option<String>,",
        "    pub payload_schema: String,",
        "    pub replay: String,",
        "    pub retention: TopicRetention,",
        "}",
        "",
        "pub const TOPIC_NAMES: &[&str] = &[",
    ]
    for topic_name in sorted(topics):
        lines.append(f'    "{topic_name}",')
    lines.extend(
        [
            "];",
            "",
            "pub fn get_topic_policy(topic: &str) -> Option<TopicPolicy> {",
            "    match topic {",
        ]
    )
    for topic_name in sorted(topics):
        entry = topics[topic_name]
        bp = entry.get("backpressure", {})
        coalesce = "true" if bp.get("coalesce", False) else "false"
        on_overflow = json.dumps(bp.get("on_overflow", ""))
        coalesce_key = bp.get("coalesce_key")
        if coalesce_key is not None:
            ck_items = ", ".join(f"{json.dumps(k)}.to_string()" for k in coalesce_key)
            ck_str = f"Some(vec![{ck_items}])"
        else:
            ck_str = "None"
        ret = entry.get("retention", {})
        duration = json.dumps(ret.get("duration", ""))
        entries = ret.get("entries", 0)
        cls = json.dumps(entry.get("class", ""))
        ps = json.dumps(entry.get("payload_schema", ""))
        replay = json.dumps(entry.get("replay", ""))
        notes = entry.get("notes")
        notes_str = (
            f"Some({json.dumps(notes)}.to_string())" if notes is not None else "None"
        )

        lines.extend(
            [
                f'        "{topic_name}" => Some(TopicPolicy {{',
                "            backpressure: TopicBackpressure {",
                f"                coalesce: {coalesce},",
                f"                coalesce_key: {ck_str},",
                f"                on_overflow: {on_overflow}.to_string(),",
                "            },",
                f"            r#class: {cls}.to_string(),",
                f"            notes: {notes_str},",
                f"            payload_schema: {ps}.to_string(),",
                f"            replay: {replay}.to_string(),",
                "            retention: TopicRetention {",
                f"                duration: {duration}.to_string(),",
                f"                entries: {entries},",
                "            },",
                "        }),",
            ]
        )
    lines.extend(
        [
            "        _ => None,",
            "    }",
            "}",
            "",
            "pub fn all_topic_policies() -> Vec<(&'static str, TopicPolicy)> {",
            "    TOPIC_NAMES",
            "        .iter()",
            "        .filter_map(|&name| get_topic_policy(name).map(|policy| (name, policy)))",
            "        .collect()",
            "}",
        ]
    )
    return lines


def emit(unit: GenerationUnit) -> str:
    source_list = ", ".join(path.as_posix() for path in unit.sources)
    lines = [
        f"// GENERATED FILE - DO NOT EDIT. Source schemas: {source_list}",
        "use serde::{Deserialize, Serialize};",
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
        if document.get("oneOf") and all(
            isinstance(branch, dict)
            and branch.get("properties", {}).get("outcome", {}).get("const")
            for branch in document["oneOf"]
        ):
            lines.extend(_emit_outcome(name, document, ref_map))
        elif document.get("type") == "object":
            lines.extend(_emit_object(name, document, ref_map))
        elif document.get("type") == "array":
            lines.append(f"pub type {name} = {_type_for(document, ref_map)};")
        else:
            lines.append(f"pub type {name} = {_type_for(document, ref_map)};")
        lines.append("")
    if topics_doc is not None:
        lines.extend(_emit_topic_policies(topics_doc.get("topics", {})))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
