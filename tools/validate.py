"""Validation tools for schema contracts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import jsonschema
import yaml

BOUNDARIES: tuple[str, ...] = ("api", "stream", "edge", "catalog")
SUPPORTED_DIALECTS: frozenset[str] = frozenset(
    {
        "https://json-schema.org/draft/2020-12/schema",
        "https://json-schema.org/draft/2020-12/schema#",
    }
)


class SchemaProblem(NamedTuple):
    path: Path  # repo-relative path of the offending file
    reason: str  # single-line explanation, names the file's actual defect


def expected_id_for_path(rel_path: Path) -> str:
    s = rel_path.as_posix()
    for ext in (".schema.json", ".json", ".yaml", ".yml"):
        if s.endswith(ext):
            return s[: -len(ext)]
    return s


def discover(schema_root: Path) -> list[Path]:
    """Every *.schema.json and *.yaml under schema/, sorted; no registry consulted."""
    found: list[Path] = []
    if not schema_root.is_dir():
        return found
    for path in schema_root.rglob("*"):
        if path.is_file() and (
            path.name.endswith(".schema.json") or path.name.endswith(".yaml")
        ):
            found.append(path)
    return sorted(found)


def check_file(path: Path, schema_root: Path) -> list[SchemaProblem]:
    """Parse, dialect check, and boundary-placement check for one file."""
    if path.is_relative_to(schema_root):
        rel_path = path.relative_to(schema_root)
        file_path = path
    else:
        if len(path.parts) > 1 and path.parts[0] == schema_root.name:
            rel_path = Path(*path.parts[1:])
            file_path = path if path.is_file() else (schema_root.parent / path)
        else:
            rel_path = path
            file_path = schema_root / path if (schema_root / path).is_file() else path

    try:
        report_path = path.relative_to(Path.cwd())
    except ValueError:
        report_path = path

    if not rel_path.parts or rel_path.parts[0] not in BOUNDARIES:
        return [
            SchemaProblem(
                path=report_path,
                reason=(
                    f"File sits outside boundary directories; boundary must be one of {BOUNDARIES}"
                ),
            )
        ]

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [SchemaProblem(path=report_path, reason=f"Cannot read file: {exc}")]

    if file_path.name.endswith(".yaml") or file_path.name.endswith(".yml"):
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            return [SchemaProblem(path=report_path, reason=f"Parse failure: {exc}")]
    else:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            return [SchemaProblem(path=report_path, reason=f"Parse failure: {exc}")]

    if not isinstance(data, dict):
        return [
            SchemaProblem(
                path=report_path,
                reason="Parse failure: schema root must be a JSON object / mapping",
            )
        ]

    dialect = data.get("$schema")
    if dialect is not None and dialect not in SUPPORTED_DIALECTS:
        return [
            SchemaProblem(
                path=report_path,
                reason=(
                    f"Unsupported schema dialect '{dialect}' (supported: {', '.join(sorted(SUPPORTED_DIALECTS))})"
                ),
            )
        ]

    declared_id = data.get("$id")
    expected_id = expected_id_for_path(rel_path)
    if declared_id is not None and declared_id != expected_id:
        return [
            SchemaProblem(
                path=report_path,
                reason=f"$id mismatch: declared '{declared_id}', expected '{expected_id}'",
            )
        ]

    # YAML policy files (such as schema/stream/topics.yaml) are policy declarations,
    # not JSON Schema meta-schemas.
    if file_path.name.endswith(".yaml") or file_path.name.endswith(".yml"):
        return []

    try:
        jsonschema.Draft202012Validator.check_schema(data)
    except jsonschema.exceptions.SchemaError as exc:
        return [
            SchemaProblem(path=report_path, reason=f"Schema invalid: {exc.message}")
        ]

    return []


def _resolve_schema_ref(schema_root: Path, ref: str) -> bool:
    candidates = [
        schema_root.parent / ref,
        schema_root / ref,
        schema_root / ref.removeprefix("schema/"),
        Path.cwd() / ref,
    ]
    return any(c.is_file() for c in candidates)


def check_stream_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Cross-document rules between topics.yaml and envelope.schema.json.

    Rules enforced, each producing a problem naming the offending topic:
      - every topics.yaml key is an accepted value of the envelope's `topic` enum
      - every envelope topic enum value is declared in topics.yaml
      - class == durable implies backpressure.coalesce is false
      - class == ephemeral implies replay == retention_only
      - payload_schema resolves to an existing file under schema/
      - coalesce_key is present iff coalesce is true
    """
    topics_file = schema_root / "stream" / "topics.yaml"
    envelope_file = schema_root / "stream" / "envelope.schema.json"

    if not topics_file.is_file() or not envelope_file.is_file():
        return []

    try:
        report_topics_path = topics_file.relative_to(Path.cwd())
    except ValueError:
        report_topics_path = topics_file

    try:
        report_envelope_path = envelope_file.relative_to(Path.cwd())
    except ValueError:
        report_envelope_path = envelope_file

    try:
        topics_data = yaml.safe_load(topics_file.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return []

    try:
        envelope_data = json.loads(envelope_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if (
        not isinstance(topics_data, dict)
        or "topics" not in topics_data
        or not isinstance(topics_data["topics"], dict)
    ):
        return []

    if not isinstance(envelope_data, dict):
        return []

    envelope_enum = envelope_data.get("properties", {}).get("topic", {}).get("enum", [])
    envelope_topics = set(envelope_enum) if isinstance(envelope_enum, list) else set()
    declared_topics = topics_data["topics"]
    declared_topic_names = set(declared_topics.keys())

    problems: list[SchemaProblem] = []

    # Rule 1: every topics.yaml key is an accepted value of the envelope's `topic` enum
    for topic_name in sorted(declared_topic_names):
        if topic_name not in envelope_topics:
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Topic '{topic_name}' declared in topics.yaml is not an "
                        "accepted value of the envelope topic enum"
                    ),
                )
            )

    # Rule 2: every envelope topic enum value is declared in topics.yaml
    for topic_name in sorted(envelope_topics):
        if topic_name not in declared_topic_names:
            problems.append(
                SchemaProblem(
                    path=report_envelope_path,
                    reason=(
                        f"Envelope topic enum value '{topic_name}' is not declared in topics.yaml"
                    ),
                )
            )

    # Per-topic invariants
    for topic_name, entry in declared_topics.items():
        if not isinstance(entry, dict):
            continue

        topic_class = entry.get("class")
        backpressure = entry.get("backpressure") or {}
        coalesce = backpressure.get("coalesce", False)
        has_coalesce_key = (
            "coalesce_key" in backpressure and backpressure["coalesce_key"] is not None
        )
        replay = entry.get("replay")
        payload_schema = entry.get("payload_schema")

        # Rule 3: class == durable implies backpressure.coalesce is false
        if topic_class == "durable" and coalesce:
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Durable topic '{topic_name}' must have backpressure coalesce set to false"
                    ),
                )
            )

        # Rule 4: class == ephemeral implies replay == retention_only
        if topic_class == "ephemeral" and replay != "retention_only":
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Ephemeral topic '{topic_name}' must have replay set to "
                        f"'retention_only' (found '{replay}')"
                    ),
                )
            )

        # Rule 5: payload_schema resolves to an existing file under schema/
        if payload_schema is None or not _resolve_schema_ref(
            schema_root, str(payload_schema)
        ):
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Topic '{topic_name}' payload_schema '{payload_schema}' does "
                        "not resolve to an existing file under schema/"
                    ),
                )
            )

        # Rule 6: coalesce_key is present iff coalesce is true
        if not coalesce and has_coalesce_key:
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Topic '{topic_name}' has coalesce_key present while coalesce is false"
                    ),
                )
            )
        elif coalesce and not has_coalesce_key:
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Topic '{topic_name}' has coalesce set to true but lacks coalesce_key"
                    ),
                )
            )

    return problems


def check_api_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Every failing operation references error.schema.json; every arrow schema
    resolves under the identifier form topics.yaml uses; every declared field
    carries a type, and timestamp fields carry a tz."""
    problems: list[SchemaProblem] = []

    # 1. Check arrow schemas under schema/api/arrow/
    arrow_dir = schema_root / "api" / "arrow"
    if arrow_dir.is_dir():
        for schema_file in sorted(arrow_dir.glob("*.schema.json")):
            try:
                report_path = schema_file.relative_to(Path.cwd())
            except ValueError:
                report_path = schema_file
            try:
                data = json.loads(schema_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            fields = data.get("fields", [])
            if isinstance(fields, list):
                for field in fields:
                    if not isinstance(field, dict):
                        continue
                    field_name = field.get("name", "unnamed")
                    if "type" not in field or not field["type"]:
                        problems.append(
                            SchemaProblem(
                                path=report_path,
                                reason=f"Arrow schema '{schema_file.name}' field '{field_name}' lacks a 'type'",
                            )
                        )
                    else:
                        field_type = str(field["type"])
                        if field_type.startswith("timestamp") and (
                            "tz" not in field or not field["tz"]
                        ):
                            problems.append(
                                SchemaProblem(
                                    path=report_path,
                                    reason=f"Arrow schema '{schema_file.name}' timestamp field '{field_name}' lacks 'tz'",
                                )
                            )

    # 2. Check topic payload_schema resolution under schema/api/arrow/
    topics_file = schema_root / "stream" / "topics.yaml"
    if topics_file.is_file():
        try:
            report_topics_path = topics_file.relative_to(Path.cwd())
        except ValueError:
            report_topics_path = topics_file
        try:
            topics_data = yaml.safe_load(topics_file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            topics_data = None
        if (
            isinstance(topics_data, dict)
            and "topics" in topics_data
            and isinstance(topics_data["topics"], dict)
        ):
            for topic_name, entry in topics_data["topics"].items():
                if not isinstance(entry, dict):
                    continue
                payload_schema = entry.get("payload_schema")
                if (
                    payload_schema
                    and (
                        str(payload_schema).startswith("schema/api/arrow/")
                        or str(payload_schema).startswith("api/arrow/")
                    )
                    and not _resolve_schema_ref(schema_root, str(payload_schema))
                ):
                    problems.append(
                        SchemaProblem(
                            path=report_topics_path,
                            reason=(
                                f"Topic '{topic_name}' payload_schema '{payload_schema}' does not resolve to a file under schema/api/arrow/"
                            ),
                        )
                    )

    # 3. Check failing operations reference error.schema.json in OpenAPI doc
    openapi_file = schema_root / "api" / "openapi.yaml"
    if not openapi_file.is_file():
        openapi_file = schema_root / "api" / "openapi.json"
    if openapi_file.is_file():
        try:
            report_openapi_path = openapi_file.relative_to(Path.cwd())
        except ValueError:
            report_openapi_path = openapi_file
        try:
            content = openapi_file.read_text(encoding="utf-8")
            doc = (
                yaml.safe_load(content)
                if openapi_file.name.endswith((".yaml", ".yml"))
                else json.loads(content)
            )
        except (yaml.YAMLError, json.JSONDecodeError, OSError):
            doc = None
        if isinstance(doc, dict):
            paths = doc.get("paths", {})
            if isinstance(paths, dict):
                for path, path_item in paths.items():
                    if not isinstance(path_item, dict):
                        continue
                    for method, op in path_item.items():
                        if method.lower() not in {
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                            "head",
                            "options",
                            "trace",
                        } or not isinstance(op, dict):
                            continue
                        op_id = op.get("operationId", f"{method.upper()} {path}")
                        responses = op.get("responses", {})
                        if not isinstance(responses, dict):
                            continue
                        for status_code_raw, resp in responses.items():
                            if not isinstance(resp, dict):
                                continue
                            status_code = str(status_code_raw)
                            is_failing_code = status_code in {"500", "default"} or (
                                status_code.startswith(("4", "5"))
                                and status_code not in {"422", "502", "503"}
                            )
                            if not is_failing_code:
                                continue
                            ref = resp.get("$ref")
                            if not ref:
                                schema = (
                                    resp.get("content", {})
                                    .get("application/json", {})
                                    .get("schema", {})
                                )
                                if isinstance(schema, dict):
                                    ref = schema.get("$ref")
                            ref_str = str(ref) if ref else ""
                            is_valid_error_ref = ref_str in {
                                "error.schema.json",
                                "api/error",
                                "#/components/schemas/ApiError",
                            } or ref_str.endswith(
                                ("/error.schema.json", "#/components/schemas/ApiError")
                            )
                            if not is_valid_error_ref:
                                problems.append(
                                    SchemaProblem(
                                        path=report_openapi_path,
                                        reason=(
                                            f"Operation '{op_id}' declares failure response '{status_code}' that does not reference error.schema.json"
                                        ),
                                    )
                                )

    return problems


def check_tree(schema_root: Path) -> list[SchemaProblem]:
    """discover() then check_file() over everything, plus cross-document consistency."""
    problems: list[SchemaProblem] = []
    for file_path in discover(schema_root):
        problems.extend(check_file(file_path, schema_root))
    problems.extend(check_stream_consistency(schema_root))
    problems.extend(check_api_consistency(schema_root))
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    """Prints one line per problem, returns 0 when there are none."""
    parser = argparse.ArgumentParser(description="Validate schema contracts")
    parser.add_argument(
        "schema_root",
        nargs="?",
        type=Path,
        default=Path("schema"),
        help="Path to schema root directory (default: schema)",
    )
    args = parser.parse_args(argv)
    problems = check_tree(args.schema_root)
    for p in problems:
        sys.stderr.write(f"{p.path}: {p.reason}\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
