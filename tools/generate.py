"""Generate consumer types from q_contracts schemas."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


LANGUAGES: tuple[str, ...] = ("python", "typescript", "rust")
HEADER = "GENERATED FILE - DO NOT EDIT"
SUPPORTED_JSON_SCHEMA_DIALECTS = frozenset(
    {
        "https://json-schema.org/draft/2020-12/schema",
        "https://json-schema.org/draft/2020-12/schema#",
    }
)


class GenerationError(Exception):
    """Raised when a schema cannot be generated for a target language."""


@dataclass(frozen=True)
class GenerationUnit:
    name: str
    sources: tuple[Path, ...]
    documents: tuple[dict[str, Any], ...]


def plan_units(schema_root: Path) -> list[GenerationUnit]:
    """Return the typed schema groups in stable boundary/name order.

    Policy YAML documents are intentionally not emitted as language bindings:
    they describe retention, lifecycle, and endpoint obligations rather than
    payload shapes. They remain part of ``make check`` through ``validate.py``.
    """
    units: list[GenerationUnit] = []
    for name in ("api", "catalog", "edge", "stream"):
        boundary = schema_root / name
        paths = sorted(boundary.rglob("*.schema.json")) if boundary.is_dir() else []
        if name == "api" and (boundary / "openapi.yaml").is_file():
            paths.append(boundary / "openapi.yaml")
        paths = sorted(paths)
        documents: list[dict[str, Any]] = []
        sources: list[Path] = []
        for path in paths:
            relative = path.relative_to(schema_root.parent)
            try:
                if path.suffix == ".yaml":
                    document = yaml.safe_load(path.read_text(encoding="utf-8"))
                    if not isinstance(document, dict) or not str(
                        document.get("openapi", "")
                    ).startswith("3.1"):
                        raise GenerationError(
                            f"Unsupported schema dialect in {relative} for languages: "
                            f"{', '.join(LANGUAGES)}"
                        )
                else:
                    document = json.loads(path.read_text(encoding="utf-8"))
                    dialect = document.get("$schema")
                    if dialect is not None and dialect not in SUPPORTED_JSON_SCHEMA_DIALECTS:
                        raise GenerationError(
                            f"Unsupported schema dialect in {relative} for languages: "
                            f"{', '.join(LANGUAGES)}"
                        )
            except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
                raise GenerationError(
                    f"Could not read schema {relative} for languages: {', '.join(LANGUAGES)}: {exc}"
                ) from exc
            if not isinstance(document, dict):
                raise GenerationError(
                    f"Schema {relative} is not an object for languages: {', '.join(LANGUAGES)}"
                )
            sources.append(relative)
            documents.append(document)
        if sources:
            units.append(
                GenerationUnit(name=name, sources=tuple(sources), documents=tuple(documents))
            )
    return units
