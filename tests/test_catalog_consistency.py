import json
from pathlib import Path

import pytest
import yaml

LIFECYCLE_PATH = Path(__file__).parent.parent / "schema" / "catalog" / "lifecycle.yaml"


@pytest.fixture
def lifecycle_doc() -> dict:
    assert LIFECYCLE_PATH.is_file(), f"lifecycle.yaml must exist at {LIFECYCLE_PATH}"
    data = yaml.safe_load(LIFECYCLE_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "lifecycle.yaml must be a mapping"
    return data


def test_lifecycle_states_declared(lifecycle_doc: dict) -> None:
    expected_states = ["publishing", "published", "tombstoned", "deleted"]
    assert "states" in lifecycle_doc, "lifecycle.yaml must declare 'states'"
    assert lifecycle_doc["states"] == expected_states


def test_transition_map_is_total_over_state_list(lifecycle_doc: dict) -> None:
    states = lifecycle_doc.get("states", [])
    transitions = lifecycle_doc.get("transitions", {})
    assert isinstance(transitions, dict), "transitions must be a mapping"

    # Transition map must be total over the state list
    assert set(transitions.keys()) == set(
        states
    ), f"Transition map keys {set(transitions.keys())} do not match states {set(states)}"

    # Every target state in transitions must be a valid declared state
    for src, targets in transitions.items():
        assert isinstance(targets, list), f"Targets for {src} must be a list"
        for tgt in targets:
            assert (
                tgt in states
            ), f"Target state '{tgt}' from '{src}' not in declared states"


def test_deleted_state_has_no_outgoing_transitions(lifecycle_doc: dict) -> None:
    transitions = lifecycle_doc.get("transitions", {})
    assert (
        transitions.get("deleted") == []
    ), f"State 'deleted' must have no outgoing transitions, got: {transitions.get('deleted')}"


def test_publishing_state_has_exactly_one_outgoing_transition(
    lifecycle_doc: dict,
) -> None:
    transitions = lifecycle_doc.get("transitions", {})
    publishing_targets = transitions.get("publishing")
    assert isinstance(publishing_targets, list)
    assert (
        len(publishing_targets) == 1
    ), f"State 'publishing' must have exactly one outgoing transition, got: {publishing_targets}"
    assert publishing_targets == ["published"]


def test_lifecycle_invariants_declared(lifecycle_doc: dict) -> None:
    assert "invariants" in lifecycle_doc, "lifecycle.yaml must declare 'invariants'"
    invariants = lifecycle_doc["invariants"]
    assert isinstance(invariants, list)
    assert len(invariants) >= 3


def create_minimal_catalog_tree(tmp_path: Path) -> Path:
    schema_root = tmp_path / "schema"
    catalog_dir = schema_root / "catalog"
    examples_dir = catalog_dir / "examples"
    examples_dir.mkdir(parents=True)

    # 1. lifecycle.yaml
    lifecycle_file = catalog_dir / "lifecycle.yaml"
    lifecycle_file.write_text(
        yaml.dump(
            {
                "states": ["publishing", "published", "tombstoned", "deleted"],
                "transitions": {
                    "publishing": ["published"],
                    "published": ["tombstoned"],
                    "tombstoned": ["deleted"],
                    "deleted": [],
                },
                "invariants": [
                    "state == tombstoned implies tombstone is not null",
                    "state == published implies tombstone is null",
                    "files is non-empty for every state except deleted",
                ],
            }
        )
    )

    # 2. valid manifest example
    example_file = examples_dir / "manifest-bars-two-files.json"
    example_file.write_text(
        (
            Path(__file__).parent.parent
            / "schema"
            / "catalog"
            / "examples"
            / "manifest-bars-two-files.json"
        ).read_text(encoding="utf-8")
    )

    return schema_root


def test_consistency_illegal_transition_fails_naming_both_states(
    tmp_path: Path,
) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    transition_file = (
        schema_root / "catalog" / "examples" / "manifest-illegal-transition.json"
    )
    transition_file.write_text(
        json.dumps(
            {
                "dataset_id": "11111111-1111-1111-1111-111111111111",
                "previous_state": "published",
                "state": "publishing",
                "subject": {"kind": "bars", "symbol": "PETR4"},
                "version": 2,
                "supersedes": "c1a4e235-9831-4c4f-9e6b-a2c6d482ef10",
                "published_at": "2026-09-12T10:00:00Z",
                "checksum_algorithm": "sha256",
                "files": [
                    {
                        "path": "ohlcv/PETR4/D1/2024.parquet",
                        "size_bytes": 100,
                        "checksum": "abcd",
                    }
                ],
                "arrow_schema": {
                    "name": "bars",
                    "fields": [{"name": "open", "type": "float64"}],
                },
                "row_count": 10,
                "time_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-02T00:00:00Z",
                },
                "tombstone": None,
            }
        )
    )

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    reasons = [p.reason for p in problems]
    assert any(
        "published" in r and "publishing" in r for r in reasons
    ), f"Expected failure naming 'published' and 'publishing', got: {reasons}"


def test_consistency_unknown_state_fails(tmp_path: Path) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    example_file = schema_root / "catalog" / "examples" / "manifest-bars-two-files.json"
    data = json.loads(example_file.read_text())
    data["state"] = "unknown_state"
    example_file.write_text(json.dumps(data))

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    assert any("unknown_state" in p.reason for p in problems)


def test_consistency_tombstoned_with_null_tombstone_fails(tmp_path: Path) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    example_file = schema_root / "catalog" / "examples" / "manifest-bars-two-files.json"
    data = json.loads(example_file.read_text())
    data["state"] = "tombstoned"
    data["tombstone"] = None
    example_file.write_text(json.dumps(data))

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    assert any("tombstone" in p.reason.lower() for p in problems)


def test_consistency_published_with_non_null_tombstone_fails(tmp_path: Path) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    example_file = schema_root / "catalog" / "examples" / "manifest-bars-two-files.json"
    data = json.loads(example_file.read_text())
    data["state"] = "published"
    data["tombstone"] = {
        "tombstoned_at": "2026-09-12T10:00:00Z",
        "deletable_after": "2026-09-19T10:00:00Z",
    }
    example_file.write_text(json.dumps(data))

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    assert any("tombstone" in p.reason.lower() for p in problems)


def test_consistency_non_deleted_empty_files_fails(tmp_path: Path) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    example_file = schema_root / "catalog" / "examples" / "manifest-bars-two-files.json"
    data = json.loads(example_file.read_text())
    data["files"] = []
    example_file.write_text(json.dumps(data))

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    assert any("files" in p.reason.lower() for p in problems)


def test_consistency_arrow_schema_timestamp_without_tz_fails(
    tmp_path: Path,
) -> None:
    from tools.validate import check_catalog_consistency

    schema_root = create_minimal_catalog_tree(tmp_path)
    example_file = schema_root / "catalog" / "examples" / "manifest-bars-two-files.json"
    data = json.loads(example_file.read_text())
    data["arrow_schema"]["fields"][0] = {
        "name": "time",
        "type": "timestamp[us]",
        "nullable": False,
        # missing tz!
    }
    example_file.write_text(json.dumps(data))

    problems = check_catalog_consistency(schema_root)
    assert len(problems) >= 1
    assert any(
        "timestamp" in p.reason.lower() and "tz" in p.reason.lower() for p in problems
    )


def test_delivered_tree_catalog_consistency() -> None:
    from tools.validate import check_catalog_consistency

    schema_root = Path(__file__).parent.parent / "schema"
    problems = check_catalog_consistency(schema_root)
    assert problems == []
