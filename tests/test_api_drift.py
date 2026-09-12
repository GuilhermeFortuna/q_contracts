import os
import urllib.error
from pathlib import Path

import pytest
import yaml

from tools.capture_api import fetch_openapi, normalize, routes_of


def test_api_route_drift_against_live_backend():
    base_url = os.getenv("Q_API_BASE_URL", "http://127.0.0.1:8000")
    try:
        raw_captured = fetch_openapi(base_url)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"Live backend unreachable at {base_url}: {exc}")

    captured_doc = normalize(raw_captured)
    captured_routes = routes_of(captured_doc)

    committed_path = Path("schema/api/openapi.yaml")
    assert committed_path.is_file(), "schema/api/openapi.yaml must exist"
    committed_doc = yaml.safe_load(committed_path.read_text(encoding="utf-8"))
    committed_routes = routes_of(committed_doc)

    sym_diff = captured_routes ^ committed_routes
    added = captured_routes - committed_routes
    removed = committed_routes - captured_routes

    assert not sym_diff, (
        f"OpenAPI route drift detected between {base_url} and {committed_path}!\n"
        f"Routes present in live backend but missing from committed schema ({len(added)}):\n"
        f"  {sorted(added)}\n"
        f"Routes present in committed schema but missing from live backend ({len(removed)}):\n"
        f"  {sorted(removed)}"
    )
