"""Shared pytest hooks and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _offline_guard_blocks_fetch_openapi_outside_live_tests(request, monkeypatch):
    """Default CI must never call a running backend, even if Q_API_BASE_URL is set."""
    if request.node.get_closest_marker("live"):
        return

    def _forbidden(*_args, **_kwargs):
        raise AssertionError(
            "fetch_openapi must not run outside @pytest.mark.live tests"
        )

    monkeypatch.setattr("tools.capture_api.fetch_openapi", _forbidden)
