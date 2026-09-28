import os
import subprocess
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from _pytest.outcomes import Failed

from tools import capture_api
from tools.capture_api import normalize, routes_of

REPO_ROOT = Path(__file__).resolve().parents[1]


def _committed_routes() -> set[tuple[str, str]]:
    committed_path = Path("schema/api/openapi.yaml")
    assert committed_path.is_file(), "schema/api/openapi.yaml must exist"
    committed_doc = yaml.safe_load(committed_path.read_text(encoding="utf-8"))
    return routes_of(committed_doc)


def assert_no_route_drift(base_url: str) -> None:
    """Compare live /openapi.json routes to the committed schema; fail on drift or errors."""
    try:
        raw_captured = capture_api.fetch_openapi(base_url)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.fail(f"Live backend unreachable at {base_url}: {exc}")

    captured_doc = normalize(raw_captured)
    captured_routes = routes_of(captured_doc)
    committed_routes = _committed_routes()

    sym_diff = captured_routes ^ committed_routes
    added = captured_routes - committed_routes
    removed = committed_routes - captured_routes

    assert not sym_diff, (
        f"OpenAPI route drift detected between {base_url} and schema/api/openapi.yaml!\n"
        f"Routes present in live backend but missing from committed schema ({len(added)}):\n"
        f"  {sorted(added)}\n"
        f"Routes present in committed schema but missing from live backend ({len(removed)}):\n"
        f"  {sorted(removed)}"
    )


@pytest.mark.live
def test_api_route_drift_against_live_backend():
    base_url = os.getenv("Q_API_BASE_URL")
    if not base_url:
        pytest.fail(
            "Q_API_BASE_URL must be set (use: make check-live Q_API_BASE_URL=<url>)"
        )
    assert_no_route_drift(base_url)


def test_default_pytest_excludes_live_drift_test():
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "test_api_route_drift_against_live_backend" not in result.stdout


def test_check_live_requires_explicit_base_url():
    result = subprocess.run(
        ["make", "check-live"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "Q_API_BASE_URL" in combined


def test_live_drift_fails_when_backend_unreachable():
    base_url = "http://127.0.0.1:1"
    with (
        patch(
            "tools.capture_api.fetch_openapi",
            side_effect=urllib.error.URLError("connection refused"),
        ),
        pytest.raises(Failed, match="unreachable"),
    ):
        assert_no_route_drift(base_url)


def test_live_drift_reports_route_mismatch():
    base_url = "http://example.test:8000"
    with (
        patch(
            "tools.capture_api.fetch_openapi",
            return_value={"paths": {"/only-live": {"get": {}}}},
        ),
        pytest.raises(AssertionError, match="OpenAPI route drift"),
    ):
        assert_no_route_drift(base_url)
