from pathlib import Path

from tools.validate import check_file, discover


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


def test_check_tree_empty(tmp_path: Path, monkeypatch):
    from tools.validate import check_tree, main

    schema_root = tmp_path / "schema"
    schema_root.mkdir()
    assert check_tree(schema_root) == []

    monkeypatch.chdir(tmp_path)
    assert main([]) == 0


def test_check_tree_and_main_with_malformed_file(tmp_path: Path, monkeypatch, capsys):
    from tools.validate import check_tree, main

    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    broken = stream_dir / "broken.schema.json"
    broken.write_text("{")

    monkeypatch.chdir(tmp_path)

    problems = check_tree(Path("schema"))
    assert len(problems) == 1
    assert "parse" in problems[0].reason.lower()

    exit_code = main([])
    assert exit_code == 1

    captured = capsys.readouterr()
    rel_path_str = "schema/stream/broken.schema.json"
    assert rel_path_str in captured.err


def test_check_file_topics_yaml_valid(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    topics = stream_dir / "topics.yaml"
    topics.write_text("""topics:
  decisions:
    class: durable
    retention:
      duration: P1D
      entries: 200000
    backpressure:
      coalesce: false
      on_overflow: lag
    payload_schema: schema/stream/envelope.schema.json
    replay: unbounded
description: 100
""")
    problems = check_file(topics, schema_root)
    assert problems == []


def test_check_file_topics_yaml_not_mapping(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    topics = stream_dir / "topics.yaml"
    topics.write_text("- not a mapping\n")

    problems = check_file(topics, schema_root)
    assert len(problems) == 1
    assert problems[0].path == topics
    assert "mapping" in problems[0].reason.lower()


def test_check_file_json_schema_in_stream_still_checked(tmp_path: Path):
    schema_root = tmp_path / "schema"
    stream_dir = schema_root / "stream"
    stream_dir.mkdir(parents=True)
    bad_schema = stream_dir / "bad.schema.json"
    bad_schema.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "stream/bad", "type": 123}'
    )

    problems = check_file(bad_schema, schema_root)
    assert len(problems) == 1
    assert "schema invalid" in problems[0].reason.lower()
