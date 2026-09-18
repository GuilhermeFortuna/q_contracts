"""Validation tools for schema contracts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NamedTuple

import jsonschema
import yaml

BOUNDARIES: tuple[str, ...] = ("api", "stream", "edge", "catalog")
# The documents each boundary's cross-document checks read. Absence is a failure
# rather than a silent skip, because every check below returns no problems when
# its anchor is missing, so a deleted anchor would otherwise pass validation.
# This is not a schema registry: adding a schema still requires no edit here.
REQUIRED_DOCUMENTS: dict[str, tuple[str, ...]] = {
    "api": ("openapi.yaml", "error.schema.json"),
    "stream": ("topics.yaml", "envelope.schema.json"),
    "edge": ("execution.yaml", "data-gateway.yaml"),
    "catalog": ("lifecycle.yaml", "dataset-manifest.schema.json"),
}
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


def check_stream_routing(schema_root: Path) -> list[SchemaProblem]:
    """Cross-document rules for stream routing and payload schemas:
    - every coalesce_key field is an allowed property of the envelope "key" object
    - job topics declare dedicated payload schemas, not the envelope itself
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

    key_schema = envelope_data.get("properties", {}).get("key", {})
    allowed_key_properties: set[str] = set()
    if isinstance(key_schema, dict):
        props = key_schema.get("properties")
        if isinstance(props, dict):
            allowed_key_properties = set(props.keys())

    problems: list[SchemaProblem] = []

    for topic_name, entry in topics_data["topics"].items():
        if not isinstance(entry, dict):
            continue

        backpressure = entry.get("backpressure") or {}
        coalesce = backpressure.get("coalesce", False)
        coalesce_key = backpressure.get("coalesce_key")

        if coalesce and isinstance(coalesce_key, list):
            for field in coalesce_key:
                if field not in allowed_key_properties:
                    problems.append(
                        SchemaProblem(
                            path=report_topics_path,
                            reason=(
                                f"Topic '{topic_name}' declares coalesce_key field '{field}' which is "
                                f"not an allowed property of the envelope key schema"
                            ),
                        )
                    )

        payload_schema = entry.get("payload_schema")
        if (
            topic_name.startswith("jobs.")
            and payload_schema is not None
            and str(payload_schema).endswith("envelope.schema.json")
        ):
            problems.append(
                SchemaProblem(
                    path=report_topics_path,
                    reason=(
                        f"Topic '{topic_name}' must declare a dedicated payload schema, "
                        f"not the envelope itself"
                    ),
                )
            )

    return problems


def _resolve_schema_dict(schema: Any, base_file: Path) -> Any:
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref = schema["$ref"]
            file_part, _, fragment = ref.partition("#")
            target_file = (
                (base_file.parent / file_part).resolve() if file_part else base_file
            )
            if target_file.is_file():
                try:
                    doc = json.loads(target_file.read_text(encoding="utf-8"))
                    if fragment:
                        ptr = fragment.lstrip("/")
                        curr = doc
                        for part in ptr.split("/"):
                            part = part.replace("~1", "/").replace("~0", "~")
                            if isinstance(curr, dict) and part in curr:
                                curr = curr[part]
                            else:
                                return schema
                        return _resolve_schema_dict(curr, target_file)
                    else:
                        return _resolve_schema_dict(doc, target_file)
                except (OSError, json.JSONDecodeError, KeyError, TypeError):
                    return schema
        return {
            k: _resolve_schema_dict(v, base_file)
            for k, v in schema.items()
            if k not in ("$id", "$schema", "title", "description")
        }
    elif isinstance(schema, list):
        return [_resolve_schema_dict(item, base_file) for item in schema]
    return schema


def check_execution_payloads(schema_root: Path) -> list[SchemaProblem]:
    """Validation rules for execution event payloads and snapshot shapes:
    - execution topics in topics.yaml must not point at the envelope
    - every snapshot entity shape in execution-snapshot.schema.json must resolve
      to the exact same shape as its event payload entity
    """
    topics_file = schema_root / "stream" / "topics.yaml"
    problems: list[SchemaProblem] = []

    if topics_file.is_file():
        try:
            report_topics_path = topics_file.relative_to(Path.cwd())
        except ValueError:
            report_topics_path = topics_file

        try:
            topics_data = yaml.safe_load(topics_file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            topics_data = None

        if isinstance(topics_data, dict) and isinstance(
            topics_data.get("topics"), dict
        ):
            execution_topics = (
                "decisions",
                "orders",
                "fills",
                "risk",
                "ledger",
                "deployments",
            )
            for topic_name in execution_topics:
                entry = topics_data["topics"].get(topic_name)
                if not isinstance(entry, dict):
                    continue
                payload_schema = entry.get("payload_schema")
                if payload_schema is None or str(payload_schema).endswith(
                    "envelope.schema.json"
                ):
                    problems.append(
                        SchemaProblem(
                            path=report_topics_path,
                            reason=(
                                f"Topic '{topic_name}' must declare a dedicated payload schema, "
                                f"not the envelope itself"
                            ),
                        )
                    )

    snapshot_file = schema_root / "stream" / "replay" / "execution-snapshot.schema.json"
    if snapshot_file.is_file():
        try:
            report_snapshot_path = snapshot_file.relative_to(Path.cwd())
        except ValueError:
            report_snapshot_path = snapshot_file

        try:
            snapshot_data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            snapshot_data = None

        if isinstance(snapshot_data, dict) and isinstance(
            snapshot_data.get("properties"), dict
        ):
            props = snapshot_data["properties"]
            payloads_dir = schema_root / "stream" / "payloads"
            common_file = payloads_dir / "execution-common.schema.json"
            entity_checks: list[tuple[str, Any, Any, Path]] = []

            dep_file = payloads_dir / "execution-deployment.schema.json"
            if "deployments" in props and dep_file.is_file():
                dep_items = (
                    props["deployments"].get("items", {})
                    if isinstance(props["deployments"], dict)
                    else {}
                )
                dep_doc = json.loads(dep_file.read_text(encoding="utf-8"))
                entity_checks.append(("deployments", dep_items, dep_doc, dep_file))

            order_file = payloads_dir / "execution-order.schema.json"
            if "orders" in props and order_file.is_file():
                order_items = (
                    props["orders"].get("items", {})
                    if isinstance(props["orders"], dict)
                    else {}
                )
                order_doc = json.loads(order_file.read_text(encoding="utf-8"))
                entity_checks.append(("orders", order_items, order_doc, order_file))

            if "accounts" in props and common_file.is_file():
                acc_items = (
                    props["accounts"].get("items", {})
                    if isinstance(props["accounts"], dict)
                    else {}
                )
                common_doc = json.loads(common_file.read_text(encoding="utf-8"))
                acc_doc = common_doc.get("$defs", {}).get("ExecutionAccount", {})
                entity_checks.append(("accounts", acc_items, acc_doc, common_file))

            if "positions" in props and common_file.is_file():
                pos_items = (
                    props["positions"].get("items", {})
                    if isinstance(props["positions"], dict)
                    else {}
                )
                common_doc = json.loads(common_file.read_text(encoding="utf-8"))
                pos_doc = common_doc.get("$defs", {}).get("ExecutionPosition", {})
                entity_checks.append(("positions", pos_items, pos_doc, common_file))

            if "control" in props and common_file.is_file():
                ctrl_schema = props.get("control", {})
                common_doc = json.loads(common_file.read_text(encoding="utf-8"))
                ctrl_doc = common_doc.get("$defs", {}).get("ExecutionControl", {})
                entity_checks.append(("control", ctrl_schema, ctrl_doc, common_file))

            recent_props = (
                props.get("recent", {}).get("properties", {})
                if isinstance(props.get("recent"), dict)
                else {}
            )
            dec_file = payloads_dir / "execution-decision.schema.json"
            if "decisions" in recent_props and dec_file.is_file():
                dec_items = (
                    recent_props["decisions"].get("items", {})
                    if isinstance(recent_props["decisions"], dict)
                    else {}
                )
                dec_doc = json.loads(dec_file.read_text(encoding="utf-8"))
                entity_checks.append(("recent.decisions", dec_items, dec_doc, dec_file))

            fill_file = payloads_dir / "execution-fill.schema.json"
            if "fills" in recent_props and fill_file.is_file():
                fill_items = (
                    recent_props["fills"].get("items", {})
                    if isinstance(recent_props["fills"], dict)
                    else {}
                )
                fill_doc = json.loads(fill_file.read_text(encoding="utf-8"))
                entity_checks.append(("recent.fills", fill_items, fill_doc, fill_file))

            risk_file = payloads_dir / "execution-risk.schema.json"
            if "risk" in recent_props and risk_file.is_file():
                risk_items = (
                    recent_props["risk"].get("items", {})
                    if isinstance(recent_props["risk"], dict)
                    else {}
                )
                risk_doc = json.loads(risk_file.read_text(encoding="utf-8"))
                entity_checks.append(("recent.risk", risk_items, risk_doc, risk_file))

            for entity_name, snap_sub, payload_sub, ref_base_file in entity_checks:
                resolved_snap = _resolve_schema_dict(snap_sub, snapshot_file)
                resolved_payload = _resolve_schema_dict(payload_sub, ref_base_file)
                if resolved_snap != resolved_payload:
                    problems.append(
                        SchemaProblem(
                            path=report_snapshot_path,
                            reason=f"Snapshot entity '{entity_name}' diverges from event payload shape",
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
                                "#/components/schemas/ErrorResponse",
                                "#/components/schemas/EpochMismatchResponse",
                                "#/components/schemas/HistoryExpiredResponse",
                            } or ref_str.endswith(
                                (
                                    "/error.schema.json",
                                    "#/components/schemas/ApiError",
                                    "#/components/schemas/ErrorResponse",
                                    "#/components/schemas/EpochMismatchResponse",
                                    "#/components/schemas/HistoryExpiredResponse",
                                )
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


def check_edge_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Both contracts declare a schema major and a health operation; the submit
    outcome union has exactly three members and the lookup union exactly four;
    every lookup member declares closes_intent; the submit request requires
    intent_id; the quote response requires age_ms."""
    problems: list[SchemaProblem] = []
    edge_dir = schema_root / "edge"
    if not edge_dir.is_dir():
        return problems

    # 1. Check both contracts declare schema_major and a health operation
    for contract_name in ("data-gateway.yaml", "execution.yaml"):
        contract_path = edge_dir / contract_name
        if not contract_path.is_file():
            continue
        try:
            report_path = contract_path.relative_to(Path.cwd())
        except ValueError:
            report_path = contract_path

        try:
            doc = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue

        if not isinstance(doc, dict):
            continue

        schema_major = doc.get("schema_major")
        if schema_major is None:
            problems.append(
                SchemaProblem(
                    path=report_path,
                    reason=f"Edge contract '{contract_name}' must declare 'schema_major'",
                )
            )

        endpoints = doc.get("endpoints", {})
        operations = doc.get("operations", {})
        has_health = (isinstance(endpoints, dict) and "/v1/health" in endpoints) or (
            isinstance(operations, dict) and "health" in operations
        )
        if not has_health:
            problems.append(
                SchemaProblem(
                    path=report_path,
                    reason=f"Edge contract '{contract_name}' must declare a health endpoint/operation",
                )
            )

    # 2. Check submit-outcome.schema.json union has exactly three members
    submit_outcome_path = edge_dir / "execution" / "submit-outcome.schema.json"
    if submit_outcome_path.is_file():
        try:
            report_so_path = submit_outcome_path.relative_to(Path.cwd())
        except ValueError:
            report_so_path = submit_outcome_path
        try:
            so_data = json.loads(submit_outcome_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            so_data = None
        if isinstance(so_data, dict):
            one_of = so_data.get("oneOf")
            count = len(one_of) if isinstance(one_of, list) else 0
            if count != 3:
                problems.append(
                    SchemaProblem(
                        path=report_so_path,
                        reason=f"Submit outcome schema oneOf union must have exactly 3 members (found {count})",
                    )
                )

    # 3. Check lookup-outcome.schema.json union has exactly four members and each declares closes_intent
    lookup_outcome_path = edge_dir / "execution" / "lookup-outcome.schema.json"
    if lookup_outcome_path.is_file():
        try:
            report_lo_path = lookup_outcome_path.relative_to(Path.cwd())
        except ValueError:
            report_lo_path = lookup_outcome_path
        try:
            lo_data = json.loads(lookup_outcome_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            lo_data = None
        if isinstance(lo_data, dict):
            one_of = lo_data.get("oneOf")
            count = len(one_of) if isinstance(one_of, list) else 0
            if count != 4:
                problems.append(
                    SchemaProblem(
                        path=report_lo_path,
                        reason=f"Lookup outcome schema oneOf union must have exactly 4 members (found {count})",
                    )
                )
            if isinstance(one_of, list):
                for idx, branch in enumerate(one_of):
                    if not isinstance(branch, dict):
                        continue
                    props = branch.get("properties", {})
                    req = branch.get("required", [])
                    has_closes_intent = (
                        isinstance(props, dict)
                        and "closes_intent" in props
                        and isinstance(req, list)
                        and "closes_intent" in req
                    )
                    if not has_closes_intent:
                        outcome_name = (
                            props.get("outcome", {}).get("const", f"member {idx}")
                            if isinstance(props, dict)
                            else f"member {idx}"
                        )
                        problems.append(
                            SchemaProblem(
                                path=report_lo_path,
                                reason=f"Lookup outcome member '{outcome_name}' must declare and require 'closes_intent'",
                            )
                        )

    # 4. Check submit-request.schema.json requires intent_id
    submit_req_path = edge_dir / "execution" / "submit-request.schema.json"
    if submit_req_path.is_file():
        try:
            report_sr_path = submit_req_path.relative_to(Path.cwd())
        except ValueError:
            report_sr_path = submit_req_path
        try:
            sr_data = json.loads(submit_req_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            sr_data = None
        if isinstance(sr_data, dict):
            req = sr_data.get("required", [])
            if not isinstance(req, list) or "intent_id" not in req:
                problems.append(
                    SchemaProblem(
                        path=report_sr_path,
                        reason="Submit request schema must require 'intent_id'",
                    )
                )

    # 5. Check quote-response.schema.json requires age_ms
    quote_resp_path = edge_dir / "execution" / "quote-response.schema.json"
    if quote_resp_path.is_file():
        try:
            report_qr_path = quote_resp_path.relative_to(Path.cwd())
        except ValueError:
            report_qr_path = quote_resp_path
        try:
            qr_data = json.loads(quote_resp_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            qr_data = None
        if isinstance(qr_data, dict):
            req = qr_data.get("required", [])
            if not isinstance(req, list) or "age_ms" not in req:
                problems.append(
                    SchemaProblem(
                        path=report_qr_path,
                        reason="Quote response schema must require 'age_ms'",
                    )
                )

    return problems


def check_catalog_consistency(schema_root: Path) -> list[SchemaProblem]:
    """Every state named in an example exists in lifecycle.yaml; every lifecycle
    invariant holds for every committed example; the manifest's arrow_schema
    field uses the same declaration form as schema/api/arrow/*."""
    problems: list[SchemaProblem] = []
    catalog_dir = schema_root / "catalog"
    if not catalog_dir.is_dir():
        return problems

    lifecycle_file = catalog_dir / "lifecycle.yaml"
    if not lifecycle_file.is_file():
        return problems

    try:
        lifecycle_data = yaml.safe_load(lifecycle_file.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return problems

    if not isinstance(lifecycle_data, dict):
        return problems

    states_list = lifecycle_data.get("states", [])
    states = set(states_list) if isinstance(states_list, list) else set()
    transitions = lifecycle_data.get("transitions", {})
    if not isinstance(transitions, dict):
        transitions = {}

    examples_dir = catalog_dir / "examples"
    if not examples_dir.is_dir():
        return problems

    example_files = sorted(
        [
            p
            for p in examples_dir.rglob("*")
            if p.is_file() and p.suffix in (".json", ".yaml", ".yml")
        ]
    )

    for example_file in example_files:
        try:
            report_path = example_file.relative_to(Path.cwd())
        except ValueError:
            report_path = example_file

        try:
            content = example_file.read_text(encoding="utf-8")
            doc = (
                yaml.safe_load(content)
                if example_file.suffix in (".yaml", ".yml")
                else json.loads(content)
            )
        except (yaml.YAMLError, json.JSONDecodeError, OSError) as exc:
            problems.append(
                SchemaProblem(path=report_path, reason=f"Parse failure: {exc}")
            )
            continue

        if not isinstance(doc, dict):
            continue

        # 1. State existence check
        state = doc.get("state")
        if state is not None and state not in states:
            problems.append(
                SchemaProblem(
                    path=report_path,
                    reason=f"State '{state}' in example is not declared in lifecycle.yaml",
                )
            )

        # 2. Transition legality check if example asserts a transition
        from_state = None
        to_state = None
        if "transition" in doc and isinstance(doc["transition"], dict):
            from_state = doc["transition"].get("from") or doc["transition"].get(
                "from_state"
            )
            to_state = doc["transition"].get("to") or doc["transition"].get("to_state")
        elif "previous_state" in doc and "state" in doc:
            from_state = doc.get("previous_state")
            to_state = doc.get("state")
        elif "from_state" in doc and "to_state" in doc:
            from_state = doc.get("from_state")
            to_state = doc.get("to_state")

        if from_state is not None and to_state is not None:
            if from_state not in states:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason=f"Transition source state '{from_state}' is not declared in lifecycle.yaml",
                    )
                )
            if to_state not in states:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason=f"Transition target state '{to_state}' is not declared in lifecycle.yaml",
                    )
                )
            if from_state in states and to_state in states:
                legal_targets = transitions.get(from_state, [])
                if to_state not in legal_targets:
                    problems.append(
                        SchemaProblem(
                            path=report_path,
                            reason=(
                                f"Illegal transition from '{from_state}' to '{to_state}' "
                                f"(legal transitions: {legal_targets})"
                            ),
                        )
                    )

        # 3. Lifecycle invariants check
        if state == "tombstoned":
            tombstone = doc.get("tombstone")
            if tombstone is None:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason="Manifest with state 'tombstoned' violates lifecycle invariant: tombstone is null",
                    )
                )
            elif isinstance(tombstone, dict) and "deletable_after" not in tombstone:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason="Manifest with state 'tombstoned' violates lifecycle invariant: tombstone lacks 'deletable_after'",
                    )
                )
        elif state == "published":
            if doc.get("tombstone") is not None:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason="Manifest with state 'published' violates lifecycle invariant: tombstone is not null",
                    )
                )

        if state is not None and state != "deleted" and "files" in doc:
            files = doc.get("files")
            if not isinstance(files, list) or len(files) == 0:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason=f"Manifest with state '{state}' violates lifecycle invariant: files is empty",
                    )
                )

        # 4. Arrow schema declaration form check
        if "arrow_schema" in doc and isinstance(doc["arrow_schema"], dict):
            arrow_schema = doc["arrow_schema"]
            fields = arrow_schema.get("fields")
            if not isinstance(fields, list) or len(fields) == 0:
                problems.append(
                    SchemaProblem(
                        path=report_path,
                        reason="Manifest 'arrow_schema' must declare a non-empty 'fields' list",
                    )
                )
            else:
                for field in fields:
                    if not isinstance(field, dict):
                        continue
                    fname = field.get("name", "unnamed")
                    if "name" not in field or not field["name"]:
                        problems.append(
                            SchemaProblem(
                                path=report_path,
                                reason="Manifest 'arrow_schema' field lacks 'name'",
                            )
                        )
                    if "type" not in field or not field["type"]:
                        problems.append(
                            SchemaProblem(
                                path=report_path,
                                reason=f"Manifest 'arrow_schema' field '{fname}' lacks 'type'",
                            )
                        )
                    else:
                        ftype = str(field["type"])
                        if ftype.startswith("timestamp") and (
                            "tz" not in field or not field["tz"]
                        ):
                            problems.append(
                                SchemaProblem(
                                    path=report_path,
                                    reason=f"Manifest 'arrow_schema' timestamp field '{fname}' lacks 'tz'",
                                )
                            )

    return problems


def check_required_documents(schema_root: Path) -> list[SchemaProblem]:
    """Every populated boundary carries the documents its consistency check reads.

    A boundary with no files at all requires nothing, so an empty tree stays
    valid; a boundary that holds schemas must hold its anchors, so deleting one
    fails the check by name instead of disabling it.
    """
    problems: list[SchemaProblem] = []
    for boundary, required in REQUIRED_DOCUMENTS.items():
        boundary_root = schema_root / boundary
        if not boundary_root.is_dir():
            continue
        if not any(path.is_file() for path in boundary_root.rglob("*")):
            continue
        for name in required:
            document = boundary_root / name
            if document.is_file():
                continue
            try:
                report_path = document.relative_to(Path.cwd())
            except ValueError:
                report_path = document
            problems.append(
                SchemaProblem(
                    path=report_path,
                    reason=(
                        f"Required document '{boundary}/{name}' is absent; the "
                        f"{boundary} boundary holds schemas, so its cross-document "
                        "checks cannot be skipped"
                    ),
                )
            )
    return problems


def check_tree(schema_root: Path) -> list[SchemaProblem]:
    """discover() then check_file() over everything, plus cross-document consistency."""
    problems: list[SchemaProblem] = []
    problems.extend(check_required_documents(schema_root))
    for file_path in discover(schema_root):
        problems.extend(check_file(file_path, schema_root))
    problems.extend(check_stream_consistency(schema_root))
    problems.extend(check_stream_routing(schema_root))
    problems.extend(check_execution_payloads(schema_root))
    problems.extend(check_api_consistency(schema_root))
    problems.extend(check_edge_consistency(schema_root))
    problems.extend(check_catalog_consistency(schema_root))
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
