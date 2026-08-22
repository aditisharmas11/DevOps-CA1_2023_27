"""Shared pytest helpers: configs backed by the committed CSV fixtures."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from src.config import load_config

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "default.yaml"

TINY_MODELS = [
    {
        "name": "lightgbm",
        "enabled": True,
        "weight": 0.7,
        "early_stopping_rounds": None,
        "params": {
            "n_estimators": 30,
            "learning_rate": 0.2,
            "num_leaves": 7,
            "min_child_samples": 2,
            "verbose": -1,
        },
    },
    {
        "name": "hist_gbm",
        "enabled": True,
        "weight": 0.3,
        "early_stopping_rounds": None,
        "params": {
            "max_iter": 30,
            "learning_rate": 0.2,
            "max_leaf_nodes": 7,
            "min_samples_leaf": 2,
            "early_stopping": False,
            "verbose": 0,
        },
    },
]


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge updates into base, returning base."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def make_config(tmp_path: Path, fixture: str, **overrides: Any) -> dict[str, Any]:
    """Build a config pointing at tests/fixtures/<fixture> with tmp_path output dirs."""
    raw = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    cfg = copy.deepcopy(raw)
    cfg["paths"]["raw_dir"] = str(FIXTURES_DIR / fixture)
    cfg["contract"] = {
        "id_column": None,
        "target_column": None,
        "task_type": None,
        "drop_columns": [],
    }
    cfg["runtime"] = {"n_jobs": 1, "progress": False, "log_every_n_iterations": 0}
    cfg["cv"]["n_splits"] = 2
    cfg["metric"] = {"name": "auto", "greater_is_better": None}
    cfg["models"] = copy.deepcopy(TINY_MODELS)
    _deep_update(cfg, overrides)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return load_config(config_path, root=tmp_path)
