"""Validation tools for schema contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import jsonschema
import yaml

BOUNDARIES: tuple[str, ...] = ("api", "stream", "edge", "catalog")
SUPPORTED_DIALECTS: frozenset[str] = frozenset({
    "https://json-schema.org/draft/2020-12/schema",
    "https://json-schema.org/draft/2020-12/schema#",
})


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

    if not rel_path.parts or rel_path.parts[0] not in BOUNDARIES:
        return [
            SchemaProblem(
                path=path,
                reason=(
                    f"File sits outside boundary directories; boundary must be one of {BOUNDARIES}"
                ),
            )
        ]

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [SchemaProblem(path=path, reason=f"Cannot read file: {exc}")]

    if file_path.name.endswith(".yaml") or file_path.name.endswith(".yml"):
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            return [SchemaProblem(path=path, reason=f"Parse failure: {exc}")]
    else:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            return [SchemaProblem(path=path, reason=f"Parse failure: {exc}")]

    if not isinstance(data, dict):
        return [
            SchemaProblem(
                path=path,
                reason="Parse failure: schema root must be a JSON object / mapping",
            )
        ]

    dialect = data.get("$schema")
    if dialect is not None and dialect not in SUPPORTED_DIALECTS:
        return [
            SchemaProblem(
                path=path,
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
                path=path,
                reason=f"$id mismatch: declared '{declared_id}', expected '{expected_id}'",
            )
        ]

    try:
        jsonschema.Draft202012Validator.check_schema(data)
    except jsonschema.exceptions.SchemaError as exc:
        return [SchemaProblem(path=path, reason=f"Schema invalid: {exc.message}")]

    return []
