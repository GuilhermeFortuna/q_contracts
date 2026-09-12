import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


def normalize_arrow_type(type_str: str) -> str:
    """Normalize Arrow / NumPy type strings for comparison."""
    type_str = type_str.lower()
    if type_str in ("double", "float64", "f8"):
        return "float64"
    if type_str in ("int64", "i8"):
        return "int64"
    if type_str in ("int32", "i4"):
        return "int32"
    if type_str in ("uint32", "u4"):
        return "uint32"
    if type_str.startswith("timestamp"):
        return type_str
    return type_str


def test_bars_parquet_matches_arrow_schema():
    schema_path = Path("schema/api/arrow/bars.schema.json")
    assert schema_path.is_file(), "bars.schema.json must exist"

    schema_doc = json.loads(schema_path.read_text(encoding="utf-8"))
    declared_fields = schema_doc["fields"]

    fixture_path = Path("tests/fixtures/bars_sample.parquet")
    assert fixture_path.is_file(), "bars_sample.parquet fixture must exist"

    table = pq.read_table(fixture_path)
    parquet_fields = list(table.schema)

    # Assert exact column count and names in order
    declared_names = [f["name"] for f in declared_fields]
    actual_names = [f.name for f in parquet_fields]
    assert (
        actual_names == declared_names
    ), f"Column names/order mismatch:\nActual:   {actual_names}\nDeclared: {declared_names}"

    # Assert types match field-for-field
    for declared, actual in zip(declared_fields, parquet_fields, strict=True):
        decl_type = normalize_arrow_type(declared["type"])
        act_type = normalize_arrow_type(str(actual.type))
        assert (
            act_type == decl_type
        ), f"Type mismatch for column '{declared['name']}': actual '{act_type}' != declared '{decl_type}'"


def test_ticks_npz_matches_arrow_schema():
    schema_path = Path("schema/api/arrow/ticks.schema.json")
    assert schema_path.is_file(), "ticks.schema.json must exist"

    schema_doc = json.loads(schema_path.read_text(encoding="utf-8"))
    declared_fields = schema_doc["fields"]

    fixture_path = Path("tests/fixtures/ticks_sample.npz")
    assert fixture_path.is_file(), "ticks_sample.npz fixture must exist"

    npz = np.load(fixture_path)
    npz_keys = list(npz.files)

    declared_names = [f["name"] for f in declared_fields]
    assert (
        npz_keys == declared_names
    ), f"Tick keys/order mismatch:\nActual:   {npz_keys}\nDeclared: {declared_names}"

    for declared in declared_fields:
        col = declared["name"]
        arr = npz[col]
        decl_type = normalize_arrow_type(declared["type"])
        act_type = normalize_arrow_type(str(arr.dtype))
        # timestamp[ms] is stored as int64 in numpy arrays
        if decl_type.startswith("timestamp") and act_type == "int64":
            continue
        assert (
            act_type == decl_type
        ), f"Type mismatch for tick column '{col}': actual '{act_type}' != declared '{decl_type}'"
