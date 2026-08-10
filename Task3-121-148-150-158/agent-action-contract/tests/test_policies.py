from __future__ import annotations

from typing import Any

from agent_action_contract.policies import lint_contract


def valid_contract() -> dict[str, Any]:
    return {
        "version": "1",
        "id": "repo.search",
        "description": "Search public repositories",
        "actor": {"id": "research-agent", "type": "agent"},
        "delegation": {
            "principal": "user:bar",
            "expires_at": "2026-07-20T18:00:00Z",
        },
        "capability": "github.repositories.search",
        "effect": "read",
        "resources": ["github:public-repositories"],
        "risk": "low",
        "approval": {"mode": "implicit"},
        "recovery": {"reversible": True, "undo": "No state changes"},
        "notification": {"timing": "after"},
        "cost": {"kind": "free"},
        "evidence": {"outputs": ["search-results.json"]},
    }


def rule_ids(contract: dict[str, Any]) -> list[str]:
    return [finding.rule_id for finding in lint_contract(contract)]


def test_valid_read_action_has_no_findings() -> None:
    assert lint_contract(valid_contract()) == []


def test_high_risk_action_requires_explicit_approval() -> None:
    contract = valid_contract()
    contract["risk"] = "high"
    assert "AC001" in rule_ids(contract)


def test_write_action_requires_expiring_delegation() -> None:
    contract = valid_contract()
    contract["effect"] = "write"
    del contract["delegation"]["expires_at"]
    assert "AC002" in rule_ids(contract)


def test_reversible_action_requires_undo_instructions() -> None:
    contract = valid_contract()
    contract["recovery"] = {"reversible": True}
    assert "AC003" in rule_ids(contract)


def test_irreversible_action_requires_approval_and_prior_notification() -> None:
    contract = valid_contract()
    contract["recovery"] = {"reversible": False}
    ids = rule_ids(contract)
    assert "AC004" in ids
    assert "AC005" in ids


def test_paid_action_requires_bounded_amount_and_currency() -> None:
    contract = valid_contract()
    contract["cost"] = {"kind": "paid"}
    assert "AC006" in rule_ids(contract)


def test_evidence_outputs_cannot_be_empty() -> None:
    contract = valid_contract()
    contract["evidence"] = {"outputs": []}
    assert "AC007" in rule_ids(contract)


def test_findings_are_stably_sorted() -> None:
    contract = valid_contract()
    contract["risk"] = "critical"
    contract["effect"] = "destructive"
    contract["delegation"] = {"principal": "user:bar"}
    contract["recovery"] = {"reversible": False}
    contract["notification"] = {"timing": "after"}
    contract["evidence"] = {"outputs": []}
    ids = rule_ids(contract)
    assert ids == sorted(ids)
