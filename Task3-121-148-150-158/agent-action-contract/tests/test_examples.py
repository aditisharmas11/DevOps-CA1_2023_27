from __future__ import annotations

from pathlib import Path

import pytest

from agent_action_contract.loader import load_contract
from agent_action_contract.policies import lint_contract
from agent_action_contract.schema import validate_contract

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.mark.parametrize(
    "name",
    ["safe-read.yaml", "reversible-write.yaml", "irreversible-deploy.yaml"],
)
def test_safe_examples_are_schema_valid_and_policy_clean(name: str) -> None:
    contract = load_contract(EXAMPLES / name)
    assert validate_contract(contract) == []
    assert lint_contract(contract) == []


def test_unsafe_example_exercises_expected_rules() -> None:
    contract = load_contract(EXAMPLES / "unsafe-deploy.yaml")
    assert validate_contract(contract) == []
    assert [finding.rule_id for finding in lint_contract(contract)] == [
        "AC001",
        "AC002",
        "AC004",
        "AC005",
        "AC007",
    ]
