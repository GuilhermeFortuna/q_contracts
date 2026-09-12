import ast
import os
import zipfile
from pathlib import Path

import pytest
import yaml


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


def gateway_schema_version(gateway_path: Path | str | None = None) -> str:
    target_file = _get_gateway_path(gateway_path)
    source = target_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "SCHEMA_VERSION"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    return node.value.value
    raise ValueError("SCHEMA_VERSION literal not found in gateway source")


def gateway_columnar_tick_keys(
    gateway_path: Path | str | None = None,
) -> tuple[str, ...]:
    target_file = _get_gateway_path(gateway_path)
    source = target_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "COLUMNAR_TICK_KEYS"
                    and isinstance(node.value, ast.Tuple)
                ):
                    keys = []
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            keys.append(elt.value)
                    return tuple(keys)
    raise ValueError("COLUMNAR_TICK_KEYS literal not found in gateway source")


def inspect_npz_arrays(npz_path: Path) -> dict[str, str]:
    """Read array names and normalized dtype names ('int64', 'float64', etc.) from .npz."""
    arrays = {}
    with zipfile.ZipFile(npz_path) as zf:
        for fname in sorted(zf.namelist()):
            if fname.endswith(".npy"):
                arr_name = fname[:-4]
                raw = zf.read(fname)
                header_len = int.from_bytes(raw[8:10], "little")
                header_str = (
                    raw[10 : 10 + header_len].decode("ascii", errors="ignore").strip()
                )
                header_dict = ast.literal_eval(header_str)
                descr = header_dict["descr"]
                dtype_map = {
                    "<i8": "int64",
                    "|i8": "int64",
                    ">i8": "int64",
                    "int64": "int64",
                    "<f8": "float64",
                    "|f8": "float64",
                    ">f8": "float64",
                    "float64": "float64",
                    "<i4": "int32",
                    "|i4": "int32",
                    ">i4": "int32",
                    "int32": "int32",
                }
                arrays[arr_name] = dtype_map.get(descr, descr)
    return arrays


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


def test_contract_paths_equal_gateway_routes():
    if "Q_BACKEND_PATH" not in os.environ:
        pytest.skip("Q_BACKEND_PATH environment variable not set")
    contract_path = Path("schema/edge/data-gateway.yaml")
    assert contract_path.is_file(), "schema/edge/data-gateway.yaml must exist"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    declared_paths = set(contract.get("endpoints", {}).keys())
    assert declared_paths == gateway_routes()


def test_contract_schema_version_equals_gateway_version():
    if "Q_BACKEND_PATH" not in os.environ:
        pytest.skip("Q_BACKEND_PATH environment variable not set")
    contract_path = Path("schema/edge/data-gateway.yaml")
    assert contract_path.is_file(), "schema/edge/data-gateway.yaml must exist"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    assert str(contract.get("schema_version")) == gateway_schema_version()


def test_contract_tick_keys_match_columnar_tick_keys():
    if "Q_BACKEND_PATH" not in os.environ:
        pytest.skip("Q_BACKEND_PATH environment variable not set")
    contract_path = Path("schema/edge/data-gateway.yaml")
    assert contract_path.is_file(), "schema/edge/data-gateway.yaml must exist"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    declared_tick_arrays = tuple(
        contract["endpoints"]["/v1/ticks"]["response"]["arrays"].keys()
    )
    assert declared_tick_arrays == gateway_columnar_tick_keys()


def test_contract_timestamp_convention():
    contract_path = Path("schema/edge/data-gateway.yaml")
    assert contract_path.is_file(), "schema/edge/data-gateway.yaml must exist"
    content = contract_path.read_text(encoding="utf-8").lower()
    assert "naive" in content
    assert "wall-clock" in content or "wall_clock" in content
    assert "no timezone conversion" in content or "no conversion" in content


def test_gateway_npz_fixture_matches_contract():
    fixture_path = Path("tests/fixtures/ticks_sample.npz")
    assert fixture_path.is_file(), "tests/fixtures/ticks_sample.npz must exist"
    contract_path = Path("schema/edge/data-gateway.yaml")
    assert contract_path.is_file(), "schema/edge/data-gateway.yaml must exist"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    contract_arrays = contract["endpoints"]["/v1/ticks"]["response"]["arrays"]
    fixture_arrays = inspect_npz_arrays(fixture_path)

    # Names and dtypes must match field-for-field
    assert set(fixture_arrays.keys()) == set(contract_arrays.keys())
    for name, expected_type in contract_arrays.items():
        assert fixture_arrays[name] == expected_type["dtype"]
