from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from agent_action_contract.formatters import (
    explain_human,
    explain_json,
    findings_github_actions,
    findings_human,
    findings_json,
)
from agent_action_contract.loader import InputError, load_contract
from agent_action_contract.policies import lint_contract
from agent_action_contract.schema import validate_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="action-contract",
        description="Validate and lint deterministic safety contracts for AI agent actions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("validate", "Validate a contract against the bundled JSON Schema."),
        ("lint", "Validate structure and apply semantic safety rules."),
        ("explain", "Summarize the authority and safety boundary."),
    ):
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.add_argument("file", type=Path)
        subparser.add_argument(
    "--format",
    choices=("human", "json", "github-actions"),
    default="human",
)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        contract = load_contract(args.file)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    schema_findings = validate_contract(contract)
    if args.command == "validate":
        if args.format == "json":
            print(findings_json(valid=not schema_findings, findings=schema_findings))
        elif args.format == "github-actions":
            print(findings_github_actions(findings=schema_findings))
        else:
            label = (
                f"INVALID {contract.get('id', args.file.name)}"
                if schema_findings
                else f"VALID {contract.get('id')}"
            )
            print(findings_human(label=label, findings=schema_findings))
        return 1 if schema_findings else 0

    if schema_findings:
        if args.format == "json":
            print(findings_json(valid=not schema_findings, findings=schema_findings))
        elif args.format == "github-actions":
            print(findings_github_actions(findings=schema_findings))
        else:
            label = f"INVALID {contract.get('id', args.file.name)}"
            print(findings_human(label=label, findings=schema_findings))
        return 1

    if args.command == "lint":
        findings = lint_contract(contract)
        if args.format == "json":
            print(findings_json(valid=True, findings=findings))
        elif args.format == "github-actions":
            print(findings_github_actions(findings=findings))
        else:
            label = f"FAIL {contract['id']}" if findings else f"PASS {contract['id']}"
            print(findings_human(label=label, findings=findings))
        return 1 if findings else 0
    if args.command == "explain":
        print(explain_json(contract) if args.format == "json" else explain_human(contract))
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
