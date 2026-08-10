from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agent_action_contract.models import Finding

Contract = Mapping[str, Any]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def lint_contract(contract: Contract) -> list[Finding]:
    """Apply deterministic semantic rules to a structurally valid contract."""

    findings: list[Finding] = []
    risk = contract.get("risk")
    effect = contract.get("effect")
    approval = _mapping(contract.get("approval"))
    delegation = _mapping(contract.get("delegation"))
    recovery = _mapping(contract.get("recovery"))
    notification = _mapping(contract.get("notification"))
    cost = _mapping(contract.get("cost"))
    evidence = _mapping(contract.get("evidence"))

    if risk in {"high", "critical"} and approval.get("mode") != "explicit":
        findings.append(
            Finding(
                "AC001",
                "error",
                "approval.mode",
                "High and critical risk actions require explicit approval.",
            )
        )

    if effect in {"write", "destructive"} and not delegation.get("expires_at"):
        findings.append(
            Finding(
                "AC002",
                "error",
                "delegation.expires_at",
                "Write and destructive actions require an expiring delegation.",
            )
        )

    reversible = recovery.get("reversible")
    if reversible is True and not recovery.get("undo"):
        findings.append(
            Finding(
                "AC003",
                "error",
                "recovery.undo",
                "Reversible actions must declare how to undo them.",
            )
        )

    if reversible is False and approval.get("mode") != "explicit":
        findings.append(
            Finding(
                "AC004",
                "error",
                "approval.mode",
                "Irreversible actions require explicit approval.",
            )
        )

    if reversible is False and notification.get("timing") != "before":
        findings.append(
            Finding(
                "AC005",
                "error",
                "notification.timing",
                "Irreversible actions require notification before execution.",
            )
        )

    if cost.get("kind") == "paid":
        amount = cost.get("max_amount")
        currency = cost.get("currency")
        if not isinstance(amount, (int, float)) or amount < 0 or not currency:
            findings.append(
                Finding(
                    "AC006",
                    "error",
                    "cost",
                    "Paid actions require a non-negative max_amount and currency.",
                )
            )

    outputs = evidence.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        findings.append(
            Finding(
                "AC007",
                "error",
                "evidence.outputs",
                "Every action must declare at least one evidence output.",
            )
        )

    return sorted(findings, key=lambda finding: (finding.rule_id, finding.path))
