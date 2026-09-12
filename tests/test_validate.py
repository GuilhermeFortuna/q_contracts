from pathlib import Path

from tools.validate import SchemaProblem, check_file, discover


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


def test_check_file_parse_failure(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    broken = stream_dir / "broken.schema.json"
    broken.write_text("{")

    problems = check_file(broken, schema_root)
    assert len(problems) == 1
    assert problems[0].path == broken
    assert "parse" in problems[0].reason.lower()


def test_check_file_unsupported_dialect(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    f = stream_dir / "draft07.schema.json"
    f.write_text('{"$schema": "http://json-schema.org/draft-07/schema#"}')

    problems = check_file(f, schema_root)
    assert len(problems) == 1
    assert "draft-07" in problems[0].reason


def test_check_file_id_mismatch(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    envelope = stream_dir / "envelope.schema.json"
    envelope.write_text('{"$id": "stream/other"}')

    problems = check_file(envelope, schema_root)
    assert len(problems) == 1
    assert "mismatch" in problems[0].reason.lower()


def test_check_file_valid(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    envelope = stream_dir / "envelope.schema.json"
    envelope.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "stream/envelope", "type": "object"}'
    )

    problems = check_file(envelope, schema_root)
    assert problems == []
