from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from agent_action_contract.models import Finding


def _schema() -> dict[str, Any]:
    resource = files("agent_action_contract").joinpath("action-contract.schema.json")
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Bundled action contract schema is not an object")
    return value


def validate_contract(contract: dict[str, Any]) -> list[Finding]:
    """Validate a contract against the bundled JSON Schema."""

    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    findings = []
    for error in validator.iter_errors(contract):
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        findings.append(Finding("SCHEMA", "error", path, error.message))
    return sorted(findings, key=lambda finding: (finding.path, finding.message))
