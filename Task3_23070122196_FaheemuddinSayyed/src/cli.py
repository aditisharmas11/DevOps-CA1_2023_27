"""Command-line entrypoint: python -m src.cli <inspect|train|predict>."""

from __future__ import annotations

import argparse
import logging
import sys

import lightgbm as lgb

from src.config import load_config
from src.contract import run_inspect
from src.predict import run_predict
from src.train import run_train

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"
DEFAULT_CONFIG = "config/default.yaml"

LOGGER = logging.getLogger("src.cli")


def configure_logging(level: str) -> None:
    """Configure root logging once, with timestamps (CLAUDE.md §7a)."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )
    # Route LightGBM's per-iteration output through Python logging so it carries the same
    # timestamps as every other line (CLAUDE.md §7a).
    lgb.register_logger(logging.getLogger("lightgbm"))


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with one subcommand per pipeline stage."""
    parser = argparse.ArgumentParser(prog="python -m src.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("inspect", "derive the data contract and write a report"),
        ("train", "run cross-validated training"),
        ("predict", "write a submission from the trained fold models"),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--config", default=DEFAULT_CONFIG, help="path to a YAML config")
        sub.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch a subcommand; return 0 on success, 1 on a handled error."""
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    try:
        cfg = load_config(args.config)
        if args.command == "inspect":
            run_inspect(cfg)
        elif args.command == "train":
            run_train(cfg)
        elif args.command == "predict":
            run_predict(cfg)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
