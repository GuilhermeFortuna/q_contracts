from tools.capture_api import normalize, routes_of


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
