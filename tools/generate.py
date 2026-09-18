"""Generate consumer types from q_contracts schemas."""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parents[1]))


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
        extra_documents: list[dict[str, Any]] = []
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
                    if (
                        dialect is not None
                        and dialect not in SUPPORTED_JSON_SCHEMA_DIALECTS
                    ):
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
            if path.name == "openapi.yaml":
                components = document.get("components", {}).get("schemas", {})
                if not isinstance(components, dict):
                    raise GenerationError(
                        f"OpenAPI schemas missing in {relative} for languages: {', '.join(LANGUAGES)}"
                    )
                for title in sorted(components):
                    component = components[title]
                    if not isinstance(component, dict):
                        raise GenerationError(
                            f"Schema {relative} component {title} is not an object for languages: "
                            f"{', '.join(LANGUAGES)}"
                        )
                    documents.append({"title": title, **component})
            else:
                documents.append(document)
                defs = document.get("$defs", {})
                if isinstance(defs, dict):
                    for def_name in sorted(defs):
                        def_doc = defs[def_name]
                        if isinstance(def_doc, dict):
                            extra_documents.append({"title": def_name, **def_doc})
        documents.extend(extra_documents)
        if sources:
            units.append(
                GenerationUnit(
                    name=name, sources=tuple(sources), documents=tuple(documents)
                )
            )
    return units


def plan_policy_units(schema_root: Path) -> list[GenerationUnit]:
    """Emit GenerationUnit for topic policy declarations in topics.yaml.

    Policy YAML documents are excluded by default in plan_units, but topics.yaml
    is emitted as generated data so relay, endpoints, and frontend don't duplicate
    retention, backpressure, coalesce_key, or topic classes.
    """
    topics_path = schema_root / "stream" / "topics.yaml"
    if not topics_path.is_file():
        return []
    try:
        relative = topics_path.relative_to(schema_root.parent)
    except ValueError:
        relative = topics_path
    try:
        data = yaml.safe_load(topics_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        raise GenerationError(
            f"Could not read policy {relative} for languages: {', '.join(LANGUAGES)}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise GenerationError(
            f"Policy {relative} is not an object for languages: {', '.join(LANGUAGES)}"
        )
    return [
        GenerationUnit(
            name="topics",
            sources=(relative,),
            documents=(data,),
        )
    ]


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def _index(language: str, units: list[GenerationUnit]) -> str:
    source_list = ", ".join(path.as_posix() for unit in units for path in unit.sources)
    if language == "python":
        return f"# {HEADER}. Source schemas: {source_list}\n"
    return f"// {HEADER}. Source schemas: {source_list}\n"


def generate(
    schema_root: Path, out_root: Path, languages: tuple[str, ...] | list[str]
) -> list[Path]:
    """Generate each requested language into a clean, deterministic output tree."""
    from tools.emitters import python as python_emitter
    from tools.emitters import rust as rust_emitter
    from tools.emitters import typescript as typescript_emitter

    unknown = sorted(set(languages) - set(LANGUAGES))
    if unknown:
        raise GenerationError(
            f"Unsupported target language(s): {', '.join(unknown)}; supported: {', '.join(LANGUAGES)}"
        )
    units = plan_units(schema_root) + plan_policy_units(schema_root)
    written: list[Path] = []
    emitters = {
        "python": python_emitter.emit,
        "typescript": typescript_emitter.emit,
        "rust": rust_emitter.emit,
    }
    for language in languages:
        selected_units = [
            unit for unit in units if not (language == "python" and unit.name == "api")
        ]
        for unit in selected_units:
            content = emitters[language](unit)
            if language == "python":
                destination = out_root / "python" / "q_contracts" / f"{unit.name}.py"
            elif language == "typescript":
                destination = out_root / "typescript" / f"{unit.name}.ts"
            else:
                destination = out_root / "rust" / f"{unit.name}.rs"
            written.append(_write(destination, content))
        if language == "python":
            destination = out_root / "python" / "q_contracts" / "__init__.py"
        elif language == "typescript":
            destination = out_root / "typescript" / "index.ts"
        else:
            destination = out_root / "rust" / "mod.rs"
        written.append(_write(destination, _index(language, selected_units)))
    return sorted(written)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema-root", type=Path, default=Path(__file__).parents[1] / "schema"
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parents[1] / "generated"
    )
    parser.add_argument(
        "--language", choices=LANGUAGES, action="append", dest="languages"
    )
    args = parser.parse_args(argv)
    try:
        paths = generate(args.schema_root, args.out, tuple(args.languages or LANGUAGES))
    except GenerationError as exc:
        print(f"generation failed: {exc}", file=sys.stderr)
        return 1
    print(f"generated {len(paths)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
