import json
from pathlib import Path

from tests.fixtures.framing import decode_binary_frame

STREAM_EXAMPLES = Path(__file__).parent.parent / "schema" / "stream" / "examples"


def test_binary_frame_roundtrip_decoding():
    bin_path = STREAM_EXAMPLES / "frame-quotes.bin"
    json_path = STREAM_EXAMPLES / "envelope-quotes.json"

    assert bin_path.is_file(), f"{bin_path} must exist"
    assert json_path.is_file(), f"{json_path} must exist"

    raw_frame = bin_path.read_bytes()
    expected_envelope = json.loads(json_path.read_text(encoding="utf-8"))

    decoded_envelope = decode_binary_frame(raw_frame)

    assert decoded_envelope == expected_envelope


def test_envelope_quotes_example_validates():
    import jsonschema

    schema_path = (
        Path(__file__).parent.parent / "schema" / "stream" / "envelope.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    envelope_data = json.loads(
        (STREAM_EXAMPLES / "envelope-quotes.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(envelope_data)) == []
