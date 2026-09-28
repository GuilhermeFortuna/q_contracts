import json
from unittest.mock import patch

from tools.capture_api import fetch_openapi, normalize, routes_of


def test_normalize_is_idempotent():
    doc = {
        "z": 1,
        "a": {"y": 2, "b": 3},
        "list": [{"b": 1, "a": 2}],
    }
    normalized_once = normalize(doc)
    normalized_twice = normalize(normalized_once)
    assert normalized_once == normalized_twice


def test_normalize_sorts_two_key_mapping_into_key_order():
    doc = {"b": 1, "a": 2}
    normalized = normalize(doc)
    assert list(normalized.keys()) == ["a", "b"]


def test_routes_of_extracts_path_and_lowercase_method_pairs():
    fixture = {
        "paths": {
            "/a": {
                "GET": {"description": "get a"},
                "POST": {"description": "post a"},
            }
        }
    }
    assert routes_of(fixture) == {("/a", "get"), ("/a", "post")}


def test_fetch_openapi_requests_openapi_json_only():
    captured: dict[str, str] = {}

    class FakeResponse:
        def read(self):
            return json.dumps({"paths": {}}).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(req, timeout=10):
        captured["url"] = req.full_url
        captured["timeout"] = str(timeout)
        return FakeResponse()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        fetch_openapi("http://backend.example:9000/api/")

    assert captured["url"] == "http://backend.example:9000/api/openapi.json"
