"""Tests for the model factory and enabled-model weight resolution."""

from __future__ import annotations

import copy
import logging

import pytest
from conftest import TINY_MODELS
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from src.contract import DataContract
from src.models import build_model, enabled_models

BINARY = DataContract("id", "target", "classification", 2, ["n1"], [])
REGRESSION = DataContract("id", "score", "regression", None, ["n1"], [])


def _cfg(models):
    """Wrap a model list in the minimal config shape enabled_models reads."""
    return {"models": copy.deepcopy(models)}


def test_build_lightgbm_classifier():
    """A classification contract yields an LGBMClassifier carrying the injected seed."""
    model = build_model("lightgbm", {"num_leaves": 7}, BINARY, 42, 1)
    assert isinstance(model, LGBMClassifier)
    assert model.get_params()["random_state"] == 42
    assert model.get_params()["n_jobs"] == 1
    assert model.get_params()["num_leaves"] == 7


def test_build_lightgbm_regressor():
    """A regression contract yields an LGBMRegressor."""
    assert isinstance(build_model("lightgbm", {}, REGRESSION, 42, 1), LGBMRegressor)


def test_build_hist_gbm_by_task():
    """hist_gbm dispatches on task type just as lightgbm does."""
    assert isinstance(build_model("hist_gbm", {}, BINARY, 42), HistGradientBoostingClassifier)
    assert isinstance(build_model("hist_gbm", {}, REGRESSION, 42), HistGradientBoostingRegressor)


def test_params_pass_through_verbatim():
    """device and verbose reach the estimator unmodified, and the caller's dict is untouched."""
    params = {"device": "cpu", "num_leaves": 7, "verbose": 1}
    original = dict(params)
    model = build_model("lightgbm", params, BINARY, 42, 1)
    assert model.get_params()["device"] == "cpu"
    assert model.get_params()["verbose"] == 1
    assert params == original


def test_unknown_model_raises():
    """An unsupported model name lists what is supported."""
    with pytest.raises(ValueError, match="lightgbm, hist_gbm"):
        build_model("xgboost", {}, BINARY, 42)


def test_enabled_models_keeps_already_normalised_weights():
    """Weights that already sum to 1 come back unchanged."""
    specs = enabled_models(_cfg(TINY_MODELS))
    assert [spec["name"] for spec in specs] == ["lightgbm", "hist_gbm"]
    assert specs[0]["weight"] == pytest.approx(0.7)
    assert specs[1]["weight"] == pytest.approx(0.3)


def test_enabled_models_normalises_weights():
    """Arbitrary weights are rescaled to sum to 1."""
    models = copy.deepcopy(TINY_MODELS)
    models[0]["weight"] = 3
    models[1]["weight"] = 1
    specs = enabled_models(_cfg(models))
    assert specs[0]["weight"] == pytest.approx(0.75)
    assert specs[1]["weight"] == pytest.approx(0.25)
    assert sum(spec["weight"] for spec in specs) == pytest.approx(1.0)


def test_enabled_models_skips_disabled():
    """A disabled entry is dropped and the survivor takes all the weight."""
    models = copy.deepcopy(TINY_MODELS)
    models[1]["enabled"] = False
    specs = enabled_models(_cfg(models))
    assert [spec["name"] for spec in specs] == ["lightgbm"]
    assert specs[0]["weight"] == pytest.approx(1.0)


def test_enabled_models_empty_raises():
    """Disabling everything is a configuration error, not an empty run."""
    models = copy.deepcopy(TINY_MODELS)
    for entry in models:
        entry["enabled"] = False
    with pytest.raises(ValueError, match="enabled"):
        enabled_models(_cfg(models))


def test_enabled_models_duplicate_name_raises():
    """Two entries sharing a name would overwrite each other's fold artifacts."""
    models = copy.deepcopy(TINY_MODELS)
    models[1]["name"] = "lightgbm"
    with pytest.raises(ValueError, match="Duplicate"):
        enabled_models(_cfg(models))


def test_enabled_models_unknown_name_raises():
    """An unknown model name fails before any data is loaded."""
    models = copy.deepcopy(TINY_MODELS)
    models[0]["name"] = "catboost"
    with pytest.raises(ValueError, match="Unknown model"):
        enabled_models(_cfg(models))


def test_enabled_models_zero_weights_are_equalised(caplog):
    """All-zero weights fall back to equal shares and say so."""
    models = copy.deepcopy(TINY_MODELS)
    for entry in models:
        entry["weight"] = 0
    with caplog.at_level(logging.WARNING, logger="src.models"):
        specs = enabled_models(_cfg(models))
    assert [spec["weight"] for spec in specs] == [pytest.approx(0.5), pytest.approx(0.5)]
    assert "equal weights" in caplog.text


def test_enabled_models_surfaces_early_stopping_rounds():
    """early_stopping_rounds is exposed beside params, never inside it."""
    models = copy.deepcopy(TINY_MODELS)
    models[0]["early_stopping_rounds"] = 100
    del models[1]["early_stopping_rounds"]
    specs = enabled_models(_cfg(models))
    assert specs[0]["early_stopping_rounds"] == 100
    assert specs[1]["early_stopping_rounds"] is None
    assert all("early_stopping_rounds" not in spec["params"] for spec in specs)
