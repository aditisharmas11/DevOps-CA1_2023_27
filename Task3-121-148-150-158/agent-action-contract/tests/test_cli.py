from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agent_action_contract.cli import main
from agent_action_contract.formatters import findings_github_actions
from agent_action_contract.models import Finding

def contract() -> dict[str, Any]:
    return {
        "version": "1",
        "id": "filesystem.write",
        "description": "Write a generated report",
        "actor": {"id": "report-agent", "type": "agent"},
        "delegation": {
            "principal": "user:bar",
            "expires_at": "2026-07-20T18:00:00Z",
        },
        "capability": "filesystem.write",
        "effect": "write",
        "resources": ["file:reports/output.md"],
        "risk": "medium",
        "approval": {"mode": "explicit"},
        "recovery": {"reversible": True, "undo": "git restore reports/output.md"},
        "notification": {"timing": "before"},
        "cost": {"kind": "free"},
        "evidence": {"outputs": ["sha256:output.md"]},
    }


def write_yaml(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "action.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_validate_accepts_structurally_valid_yaml(tmp_path: Path, capsys: Any) -> None:
    path = write_yaml(tmp_path, contract())
    assert main(["validate", str(path)]) == 0
    assert "VALID" in capsys.readouterr().out


def test_validate_reports_schema_error(tmp_path: Path, capsys: Any) -> None:
    data = contract()
    del data["actor"]
    path = write_yaml(tmp_path, data)
    assert main(["validate", str(path)]) == 1
    assert "actor" in capsys.readouterr().out


def test_lint_json_output_is_machine_readable(tmp_path: Path, capsys: Any) -> None:
    data = contract()
    data["risk"] = "high"
    data["approval"] = {"mode": "implicit"}
    path = write_yaml(tmp_path, data)
    assert main(["lint", str(path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["findings"][0]["rule_id"] == "AC001"


def test_explain_summarizes_authority_and_recovery(tmp_path: Path, capsys: Any) -> None:
    path = write_yaml(tmp_path, contract())
    assert main(["explain", str(path)]) == 0
    output = capsys.readouterr().out
    assert "report-agent" in output
    assert "user:bar" in output
    assert "filesystem.write" in output
    assert "reversible" in output


def test_malformed_yaml_returns_input_error(tmp_path: Path, capsys: Any) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("action: [", encoding="utf-8")
    assert main(["lint", str(path)]) == 2
    assert "could not parse" in capsys.readouterr().err.lower()

def test_github_actions_format_supports_multiple_findings() -> None:
    findings = [
        Finding(
            rule_id="AC001",
            severity="error",
            path="approval.mode",
            message="High risk requires explicit approval.",
        ),
        Finding(
            rule_id="AC002",
            severity="warning",
            path="resources",
            message="Resource should be reviewed.",
        ),
    ]

    output = findings_github_actions(findings=findings)

    assert output == (
        "::error file=approval.mode,title=AC001::High risk requires explicit approval.\n"
        "::error file=resources,title=AC002::Resource should be reviewed."
    )


def test_github_actions_format_escapes_special_characters() -> None:
    findings = [
        Finding(
            rule_id="AC:001",
            severity="error",
            path="resources,file\nname",
            message="Bad % value\nneeds review",
        )
    ]

    output = findings_github_actions(findings=findings)

    assert output == (
        "::error file=resources%2Cfile%0Aname,title=AC%3A001::"
        "Bad %25 value%0Aneeds review"
    )
def test_lint_github_actions_output(tmp_path: Path, capsys: Any) -> None:
    data = contract()
    data["risk"] = "high"
    data["approval"] = {"mode": "implicit"}
    path = write_yaml(tmp_path, data)

    assert main(["lint", str(path), "--format", "github-actions"]) == 1

    output = capsys.readouterr().out
    assert "::error" in output
    assert "approval.mode" in output
    assert "AC001" in output
