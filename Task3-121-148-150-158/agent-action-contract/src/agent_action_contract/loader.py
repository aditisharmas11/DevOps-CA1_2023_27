from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class InputError(ValueError):
    """Raised when an action contract cannot be loaded."""


def load_contract(path: Path) -> dict[str, Any]:
    """Load a YAML or JSON action contract without constructing custom objects."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"Could not read {path}: {exc}") from exc

    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise InputError(f"Could not parse {path}: {exc}") from exc

    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise InputError(f"Could not parse {path}: document root must be an object")
    return value
