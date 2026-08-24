from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from agent_action_contract.models import Finding


def findings_json(*, valid: bool, findings: Sequence[Finding]) -> str:
    payload = {
        "valid": valid,
        "clean": valid and not findings,
        "findings": [finding.to_dict() for finding in findings],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def findings_human(*, label: str, findings: Sequence[Finding]) -> str:
    if not findings:
        return label
    lines = [label]
    for finding in findings:
        lines.append(f"  {finding.rule_id} [{finding.severity}] {finding.path}: {finding.message}")
    return "\n".join(lines)

def findings_github_actions(*, findings: Sequence[Finding]) -> str:
    def escape_property(value: str) -> str:
        return (
            value.replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
            .replace(":", "%3A")
            .replace(",", "%2C")
        )

    def escape_message(value: str) -> str:
        return (
            value.replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
        )

    return "\n".join(
        f"::error file={escape_property(finding.path)},"
        f"title={escape_property(finding.rule_id)}::"
        f"{escape_message(finding.message)}"
        for finding in findings
    )

def explain_human(contract: Mapping[str, Any]) -> str:
    actor = _mapping(contract.get("actor"))
    delegation = _mapping(contract.get("delegation"))
    recovery = _mapping(contract.get("recovery"))
    cost = _mapping(contract.get("cost"))
    evidence = _mapping(contract.get("evidence"))
    reversibility = "reversible" if recovery.get("reversible") is True else "irreversible"
    resources = ", ".join(str(item) for item in contract.get("resources", []))
    outputs = ", ".join(str(item) for item in evidence.get("outputs", []))
    approval_mode = _mapping(contract.get("approval")).get("mode")
    return "\n".join(
        [
            f"Action: {contract.get('id')}",
            f"Actor: {actor.get('id')} ({actor.get('type')})",
            f"Acts for: {delegation.get('principal')}",
            f"Capability: {contract.get('capability')} ({contract.get('effect')})",
            f"Resources: {resources}",
            f"Risk / approval: {contract.get('risk')} / {approval_mode}",
            f"Recovery: {reversibility}",
            f"Cost: {cost.get('kind')}",
            f"Evidence: {outputs}",
        ]
    )


def explain_json(contract: Mapping[str, Any]) -> str:
    return json.dumps(contract, indent=2, sort_keys=True)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
