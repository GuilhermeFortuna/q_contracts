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
