"""Configuration loading, validation, and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOP_LEVEL_KEYS = (
    "project",
    "paths",
    "contract",
    "runtime",
    "cv",
    "metric",
    "features",
    "models",
    "output",
)

OUTPUT_DIR_KEYS = (
    "processed_dir",
    "models_dir",
    "reports_dir",
    "figures_dir",
    "submissions_dir",
)


def load_config(path: Path | str, root: Path | None = None) -> dict[str, Any]:
    """Read a YAML config, validate its top-level keys, and resolve its directories."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Missing config file {config_path}. Pass an existing path with --config."
        )
    with config_path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config {config_path} did not parse to a mapping of keys.")
    validate_config(cfg, config_path)
    return resolve_paths(cfg, root if root is not None else PROJECT_ROOT)


def validate_config(cfg: dict[str, Any], source: Path | str = "<config>") -> None:
    """Raise ValueError naming the first required top-level key that is missing."""
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in cfg:
            raise ValueError(f"Config {source} is missing required top-level key '{key}'.")


def resolve_paths(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    """Return a shallow copy of cfg with every paths.*_dir value an absolute Path."""
    resolved = dict(cfg)
    paths = dict(cfg["paths"])
    for key, value in paths.items():
        if key.endswith("_dir"):
            paths[key] = (Path(root) / str(value)).resolve()
    resolved["paths"] = paths
    return resolved


def ensure_dirs(cfg: dict[str, Any]) -> None:
    """Create every output directory named in the config."""
    for key in OUTPUT_DIR_KEYS:
        Path(cfg["paths"][key]).mkdir(parents=True, exist_ok=True)
