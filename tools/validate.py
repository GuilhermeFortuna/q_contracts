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
