"""Write reports/data_contract.md from the CSVs in data/raw/."""

from __future__ import annotations

import argparse
import sys

from src.cli import configure_logging
from src.config import load_config
from src.contract import run_inspect


def main() -> int:
    """Derive the data contract and print the path of the report written."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    configure_logging(args.log_level)
    try:
        report_path = run_inspect(load_config(args.config))
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
