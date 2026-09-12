from pathlib import Path

from tools.validate import discover


def test_discover_mixed_tree(tmp_path: Path):
    schema_root = tmp_path / "schema"
    (schema_root / "stream").mkdir(parents=True)
    (schema_root / "edge").mkdir(parents=True)
    (schema_root / "api").mkdir(parents=True)

    file_a = schema_root / "stream" / "a.schema.json"
    file_b = schema_root / "edge" / "b.schema.json"
    readme = schema_root / "api" / "README.md"

    file_a.write_text("{}")
    file_b.write_text("{}")
    readme.write_text("# API")

    found = discover(schema_root)
    assert found == [file_b, file_a]
    assert readme not in found


def test_discover_empty_tree(tmp_path: Path):
    schema_root = tmp_path / "schema"
    schema_root.mkdir(parents=True)

    assert discover(schema_root) == []
