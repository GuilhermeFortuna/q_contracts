"""Tools for capturing, normalizing, and extracting routes from OpenAPI schemas."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
)
VOLATILE_KEYS: frozenset[str] = frozenset(
    {"x-generation-date", "x-generation-time", "timestamp"}
)


def fetch_openapi(base_url: str) -> dict:
    """GET {base_url}/openapi.json from a running q_backend."""
    url = f"{base_url.rstrip('/')}/openapi.json"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize(document: Any) -> Any:
    """Strip volatile keys and sort every mapping so two captures diff cleanly."""
    if isinstance(document, dict):
        return {
            k: normalize(document[k])
            for k in sorted(document.keys())
            if k not in VOLATILE_KEYS
        }
    if isinstance(document, list):
        return [normalize(item) for item in document]
    return document


def routes_of(document: dict) -> set[tuple[str, str]]:
    """(path, lowercase method) pairs, the comparison unit for drift."""
    routes: set[tuple[str, str]] = set()
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        return routes

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in path_item:
            method_lower = method.lower()
            if method_lower in HTTP_METHODS:
                routes.add((path, method_lower))
    return routes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture and normalize OpenAPI schema from q_backend"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("Q_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Base URL of q_backend (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("schema/api/openapi.yaml"),
        help="Output path for normalized OpenAPI YAML (default: schema/api/openapi.yaml)",
    )
    args = parser.parse_args(argv)

    try:
        raw_doc = fetch_openapi(args.base_url)
    except urllib.error.URLError as exc:
        sys.stderr.write(
            f"Failed to fetch OpenAPI schema from {args.base_url}: {exc}\n"
        )
        return 1

    normalized_doc = normalize(raw_doc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        yaml.safe_dump(normalized_doc, f, sort_keys=False)

    print(f"Captured and normalized OpenAPI schema written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
