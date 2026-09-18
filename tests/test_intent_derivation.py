import ast
import os
from pathlib import Path
import uuid
from typing import Any

import pytest
import yaml

from tools.validate import check_intent_vectors


def _formula_magic(order_id: uuid.UUID, base: int = 0) -> int:
    return int((base ^ (order_id.int & 0x7FFFFFFF)) & 0x7FFFFFFF)


def _formula_comment(order_id: uuid.UUID) -> str:
    compact = str(order_id).replace("-", "")[:24]
    return f"q:{compact}"


def load_execution_yaml() -> dict[str, Any]:
    p = Path("schema/edge/execution.yaml")
    assert p.is_file(), "schema/edge/execution.yaml must exist"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_intent_derivation_vectors_match_formula():
    doc = load_execution_yaml()
    safety = doc.get("safety_invariants", {})
    derivation = safety.get("intent_derivation", {})
    assert derivation, "safety_invariants must declare intent_derivation"
    assert derivation.get("refusal_error_code") == "intent_field_mismatch"

    vectors = derivation.get("vectors", [])
    assert len(vectors) >= 5, "At least 5 vectors required"

    for vec in vectors:
        u = uuid.UUID(vec["intent_id"])
        expected_magic = _formula_magic(u)
        expected_comment = _formula_comment(u)
        assert vec["magic"] == expected_magic, f"Vector {vec['intent_id']} magic mismatch"
        assert vec["comment"] == expected_comment, f"Vector {vec['intent_id']} comment mismatch"


def _extract_backend_intent_funcs(backend_path: Path) -> dict[str, Any]:
    if backend_path.is_dir():
        target = backend_path / "src" / "q_backend" / "execution" / "brokers" / "metatrader.py"
    else:
        target = backend_path
    if not target.is_file():
        raise FileNotFoundError(f"Backend metatrader file not found at {target}")

    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(target))
    funcs: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ("intent_magic", "intent_comment"):
            mod = ast.Module(body=[node], type_ignores=[])
            code = compile(mod, filename=str(target), mode="exec")
            ns: dict[str, Any] = {"UUID": uuid.UUID}
            exec(code, ns)
            funcs[node.name] = ns[node.name]
    return funcs


@pytest.mark.skipif(
    "Q_BACKEND_PATH" not in os.environ,
    reason="Q_BACKEND_PATH environment variable not set",
)
def test_intent_vectors_match_backend_source():
    backend_path = Path(os.environ["Q_BACKEND_PATH"])
    funcs = _extract_backend_intent_funcs(backend_path)
    assert "intent_magic" in funcs, "intent_magic not found in backend source"
    assert "intent_comment" in funcs, "intent_comment not found in backend source"

    doc = load_execution_yaml()
    vectors = doc["safety_invariants"]["intent_derivation"]["vectors"]

    for vec in vectors:
        u = uuid.UUID(vec["intent_id"])
        backend_magic = funcs["intent_magic"](u)
        backend_comment = funcs["intent_comment"](u)
        assert vec["magic"] == backend_magic, f"Vector {vec['intent_id']} differs from backend intent_magic"
        assert vec["comment"] == backend_comment, f"Vector {vec['intent_id']} differs from backend intent_comment"


def test_check_intent_vectors_clean_tree():
    problems = check_intent_vectors(Path("schema"))
    assert problems == []


def test_check_intent_vectors_detects_magic_mismatch(tmp_path: Path):
    edge_dir = tmp_path / "edge"
    edge_dir.mkdir(parents=True)
    doc = load_execution_yaml()
    doc["safety_invariants"]["intent_derivation"]["vectors"][0]["magic"] = 999999
    (edge_dir / "execution.yaml").write_text(yaml.dump(doc))

    problems = check_intent_vectors(tmp_path)
    assert len(problems) == 1
    assert "magic mismatch" in problems[0].reason


def test_check_intent_vectors_detects_comment_mismatch(tmp_path: Path):
    edge_dir = tmp_path / "edge"
    edge_dir.mkdir(parents=True)
    doc = load_execution_yaml()
    doc["safety_invariants"]["intent_derivation"]["vectors"][0]["comment"] = "q:wrong"
    (edge_dir / "execution.yaml").write_text(yaml.dump(doc))

    problems = check_intent_vectors(tmp_path)
    assert len(problems) == 1
    assert "comment mismatch" in problems[0].reason


def test_check_intent_vectors_detects_fewer_than_5_vectors(tmp_path: Path):
    edge_dir = tmp_path / "edge"
    edge_dir.mkdir(parents=True)
    doc = load_execution_yaml()
    doc["safety_invariants"]["intent_derivation"]["vectors"] = doc["safety_invariants"]["intent_derivation"]["vectors"][:3]
    (edge_dir / "execution.yaml").write_text(yaml.dump(doc))

    problems = check_intent_vectors(tmp_path)
    assert len(problems) == 1
    assert "at least 5 test vectors" in problems[0].reason


def test_check_intent_vectors_detects_missing_derivation(tmp_path: Path):
    edge_dir = tmp_path / "edge"
    edge_dir.mkdir(parents=True)
    doc = load_execution_yaml()
    del doc["safety_invariants"]["intent_derivation"]
    (edge_dir / "execution.yaml").write_text(yaml.dump(doc))

    problems = check_intent_vectors(tmp_path)
    assert len(problems) == 1
    assert "must declare 'intent_derivation'" in problems[0].reason
