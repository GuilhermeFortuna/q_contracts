import json
from pathlib import Path

import jsonschema
import pytest
import referencing
import yaml


@pytest.fixture(scope="module")
def openapi_doc():
    doc_path = Path("schema/api/openapi.yaml")
    assert doc_path.is_file(), "schema/api/openapi.yaml must exist"
    return yaml.safe_load(doc_path.read_text(encoding="utf-8"))


def test_job_lifecycle_examples_exist_and_validate(openapi_doc):
    examples_dir = Path("schema/api/examples/jobs")
    assert examples_dir.is_dir(), "schema/api/examples/jobs directory must exist"

    required_examples = [
        "submission.json",
        "identifier.json",
        "running.json",
        "progress.json",
        "terminal-success.json",
        "terminal-error.json",
    ]
    for name in required_examples:
        example_path = examples_dir / name
        assert example_path.is_file(), f"Missing example file {name}"

    resource = referencing.Resource.from_contents(
        openapi_doc, default_specification=referencing.jsonschema.DRAFT202012
    )
    registry = referencing.Registry().with_resource("urn:openapi", resource)

    def validate_against(schema_name: str, instance: dict):
        validator = jsonschema.Draft202012Validator(
            {"$ref": f"urn:openapi#/components/schemas/{schema_name}"},
            registry=registry,
        )
        validator.validate(instance)

    # 1. Submission validates against BacktestRequest
    sub = json.loads((examples_dir / "submission.json").read_text())
    validate_against("BacktestRequest", sub)

    # 2. Returned identifier validates against BacktestStartResponse
    ident = json.loads((examples_dir / "identifier.json").read_text())
    validate_against("BacktestStartResponse", ident)

    # 3. Running status validates against BacktestStatusResponse
    running = json.loads((examples_dir / "running.json").read_text())
    validate_against("BacktestStatusResponse", running)
    assert running["status"] == "running"

    # 4. Progress status validates against DiscoveryAbStatusResponse
    prog = json.loads((examples_dir / "progress.json").read_text())
    validate_against("DiscoveryAbStatusResponse", prog)
    assert prog["status"] == "running"
    assert "progress" in prog

    # 5. Terminal success validates against BacktestStatusResponse
    succ = json.loads((examples_dir / "terminal-success.json").read_text())
    validate_against("BacktestStatusResponse", succ)
    assert succ["status"] == "completed"

    # 6. Terminal error validates against BacktestStatusResponse
    err = json.loads((examples_dir / "terminal-error.json").read_text())
    validate_against("BacktestStatusResponse", err)
    assert err["status"] == "failed"
    assert err.get("error") is not None
