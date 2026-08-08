"""Model factory and enabled-model resolution."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

if TYPE_CHECKING:
    from src.contract import DataContract

LOGGER = logging.getLogger(__name__)

SUPPORTED_MODELS = ("lightgbm", "hist_gbm")


def _unknown_model_error(name: str) -> ValueError:
    """Build the ValueError raised for a model name that is not in the registry."""
    return ValueError(f"Unknown model '{name}'. Supported models: {', '.join(SUPPORTED_MODELS)}.")


def build_model(
    name: str,
    params: dict[str, Any],
    contract: DataContract,
    seed: int,
    n_jobs: int = -1,
) -> Any:
    """Return an unfitted estimator for the named model and the contract's task type."""
    if name not in SUPPORTED_MODELS:
        raise _unknown_model_error(name)
    kwargs = dict(params or {})
    if name == "lightgbm":
        estimator_cls = LGBMClassifier if contract.is_classification else LGBMRegressor
        return estimator_cls(random_state=int(seed), n_jobs=int(n_jobs), **kwargs)
    hist_cls = (
        HistGradientBoostingClassifier
        if contract.is_classification
        else HistGradientBoostingRegressor
    )
    return hist_cls(random_state=int(seed), **kwargs)


def enabled_models(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Return enabled model specs, weights normalised to sum to 1."""
    specs = [entry for entry in cfg["models"] if entry.get("enabled", False)]
    if not specs:
        raise ValueError(
            "No models are enabled in config. Set at least one models[].enabled to true."
        )
    seen: set[str] = set()
    for entry in specs:
        name = entry["name"]
        if name not in SUPPORTED_MODELS:
            raise _unknown_model_error(name)
        if name in seen:
            raise ValueError(
                f"Duplicate model name '{name}' in config; fold artifact paths would collide."
            )
        seen.add(name)

    total = float(sum(float(entry.get("weight", 0.0)) for entry in specs))
    if total <= 0.0:
        LOGGER.warning("all model weights are zero; falling back to equal weights")
    return [
        {
            "name": entry["name"],
            "weight": (
                float(entry.get("weight", 0.0)) / total if total > 0.0 else 1.0 / len(specs)
            ),
            "params": dict(entry.get("params") or {}),
            "early_stopping_rounds": entry.get("early_stopping_rounds"),
        }
        for entry in specs
    ]
