"""Validation tools for schema contracts."""

from pathlib import Path


def discover(schema_root: Path) -> list[Path]:
    """Every *.schema.json and *.yaml under schema/, sorted; no registry consulted."""
    found: list[Path] = []
    if not schema_root.is_dir():
        return found
    for path in schema_root.rglob("*"):
        if path.is_file() and (path.name.endswith(".schema.json") or path.name.endswith(".yaml")):
            found.append(path)
    return sorted(found)
