"""Metric registry and metric resolution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)

if TYPE_CHECKING:
    from src.contract import DataContract

BINARY_THRESHOLD = 0.5


@dataclass(frozen=True)
class MetricSpec:
    """One metric: its callable, its direction, and whether it needs hard labels."""

    fn: Callable[[Any, Any], float]
    greater_is_better: bool
    needs_labels: bool


def _as_labels(y_pred: Any) -> np.ndarray:
    """Threshold probabilities at 0.5 (1-D) or take the argmax (2-D)."""
    array = np.asarray(y_pred)
    if array.ndim == 1:
        return (array >= BINARY_THRESHOLD).astype(int)
    return array.argmax(axis=1)


REGISTRY: dict[str, MetricSpec] = {
    "accuracy": MetricSpec(
        lambda true, pred: float(accuracy_score(true, _as_labels(pred))), True, True
    ),
    "balanced_accuracy": MetricSpec(
        lambda true, pred: float(balanced_accuracy_score(true, _as_labels(pred))), True, True
    ),
    "f1_macro": MetricSpec(
        lambda true, pred: float(f1_score(true, _as_labels(pred), average="macro")), True, True
    ),
    "roc_auc": MetricSpec(lambda true, pred: float(roc_auc_score(true, pred)), True, False),
    "rmse": MetricSpec(
        lambda true, pred: float(np.sqrt(mean_squared_error(true, pred))), False, False
    ),
    "mae": MetricSpec(lambda true, pred: float(mean_absolute_error(true, pred)), False, False),
    "r2": MetricSpec(lambda true, pred: float(r2_score(true, pred)), True, False),
}


def _task_label(contract: DataContract) -> str:
    """Describe the contract's task in words, for error messages."""
    if not contract.is_classification:
        return "regression"
    if contract.is_binary:
        return "binary classification"
    return f"classification with {contract.n_classes} classes"


def _auto_metric(contract: DataContract) -> str:
    """Resolve metric.name: auto using the Implementation Plan §2 table."""
    if not contract.is_classification:
        return "rmse"
    return "roc_auc" if contract.is_binary else "accuracy"


def resolve_metric(
    cfg: dict[str, Any], contract: DataContract
) -> tuple[str, Callable[[Any, Any], float], bool]:
    """Resolve the configured metric to (name, callable, greater_is_better)."""
    requested = str(cfg["metric"]["name"]).strip().lower()
    name = _auto_metric(contract) if requested == "auto" else requested
    if name not in REGISTRY:
        raise ValueError(
            f"Unknown metric '{name}'. Supported: {', '.join(sorted(REGISTRY))}, auto."
        )
    if name == "roc_auc" and not contract.is_binary:
        raise ValueError(
            f"roc_auc requires a binary classification target; got {_task_label(contract)}"
        )
    spec = REGISTRY[name]
    configured = cfg["metric"].get("greater_is_better")
    if configured is not None and bool(configured) != spec.greater_is_better:
        direction = "maximised" if spec.greater_is_better else "minimised"
        raise ValueError(
            f"metric.greater_is_better is {bool(configured)} but '{name}' is {direction}. "
            f"Set metric.greater_is_better to {spec.greater_is_better} or change metric.name."
        )
    return name, spec.fn, spec.greater_is_better
