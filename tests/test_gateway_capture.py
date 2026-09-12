import ast
import os
from pathlib import Path

import pytest


def _get_gateway_path(gateway_path: Path | str | None = None) -> Path:
    if gateway_path is not None:
        p = Path(gateway_path)
    else:
        env_val = os.environ.get("Q_BACKEND_PATH")
        if not env_val:
            raise ValueError("Q_BACKEND_PATH environment variable not set")
        p = Path(env_val)
    if p.is_dir():
        return p / "gateway" / "mt5_gateway.py"
    return p


def gateway_routes(gateway_path: Path | str | None = None) -> set[str]:
    """Read the dispatch table out of q_backend/gateway/mt5_gateway.py by parsing
    it as source, never by importing it — importing pulls in MetaTrader5."""
    target_file = _get_gateway_path(gateway_path)
    source = target_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "_ROUTES"
                    and isinstance(node.value, ast.Dict)
                ):
                    routes: set[str] = set()
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            routes.add(key.value)
                    return routes
    return set()


def test_gateway_routes_parse():
    if "Q_BACKEND_PATH" not in os.environ:
        pytest.skip("Q_BACKEND_PATH environment variable not set")
    routes = gateway_routes()
    assert routes == {
        "/v1/health",
        "/v1/symbol_info",
        "/v1/symbols/search",
        "/v1/available_range",
        "/v1/ohlcv",
        "/v1/ticks",
    }
