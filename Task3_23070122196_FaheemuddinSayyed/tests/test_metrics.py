"""Tests for the metric registry, auto resolution, and the roc_auc guard."""

from __future__ import annotations

import pytest

from src.contract import DataContract
from src.metrics import REGISTRY, resolve_metric

BINARY = DataContract("id", "target", "classification", 2, ["n1"], [])
MULTICLASS = DataContract("id", "target", "classification", 3, ["n1"], [])
REGRESSION = DataContract("id", "score", "regression", None, ["n1"], [])

LABEL_METRICS = ("accuracy", "balanced_accuracy", "f1_macro")
SCORE_METRICS = ("roc_auc", "rmse", "mae", "r2")


def _cfg(name: str, greater_is_better=None):
    """Wrap a metric selection in the minimal config shape resolve_metric reads."""
    return {"metric": {"name": name, "greater_is_better": greater_is_better}}


def test_auto_resolves_roc_auc_for_binary():
    """Binary classification resolves to the competition's official metric."""
    name, fn, greater = resolve_metric(_cfg("auto"), BINARY)
    assert name == "roc_auc"
    assert greater is True
    assert callable(fn)


def test_auto_resolves_accuracy_for_multiclass():
    """Multiclass falls to accuracy, since roc_auc is binary-only."""
    name, _, greater = resolve_metric(_cfg("auto"), MULTICLASS)
    assert name == "accuracy"
    assert greater is True


def test_auto_resolves_rmse_for_regression():
    """Regression resolves to rmse, which is minimised."""
    name, _, greater = resolve_metric(_cfg("auto"), REGRESSION)
    assert name == "rmse"
    assert greater is False


def test_explicit_roc_auc_on_binary_is_accepted():
    """The explicitly configured competition metric resolves unchanged."""
    assert resolve_metric(_cfg("roc_auc", True), BINARY)[0] == "roc_auc"


def test_rmse_matches_hand_computation():
    """rmse equals sqrt(mean_squared_error) on a hand-checked vector."""
    assert REGISTRY["rmse"].fn([1, 2, 3], [1, 2, 5]) == pytest.approx(1.1547005383792515)


def test_mae_matches_hand_computation():
    """mae equals the mean absolute error on the same vector."""
    assert REGISTRY["mae"].fn([1, 2, 3], [1, 2, 5]) == pytest.approx(2 / 3)


def test_r2_on_perfect_prediction():
    """A perfect fit scores 1.0."""
    assert REGISTRY["r2"].fn([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_roc_auc_on_perfect_ranking():
    """roc_auc reads the ranking, so a correctly ordered probability vector scores 1.0."""
    assert REGISTRY["roc_auc"].fn([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == pytest.approx(1.0)


def test_roc_auc_rewards_ranking_not_thresholding():
    """Probabilities all below 0.5 can still rank perfectly — why the artefact stays a float."""
    assert REGISTRY["roc_auc"].fn([0, 0, 1, 1], [0.01, 0.02, 0.03, 0.04]) == pytest.approx(1.0)


def test_accuracy_thresholds_probabilities_internally():
    """The caller passes probabilities; accuracy thresholds them at 0.5 itself."""
    assert REGISTRY["accuracy"].fn([0, 1, 1, 0], [0.2, 0.9, 0.4, 0.1]) == pytest.approx(0.75)


def test_f1_macro_accepts_probabilities():
    """f1_macro takes floats without complaining about non-integer targets."""
    score = REGISTRY["f1_macro"].fn([0, 1, 1, 0], [0.2, 0.9, 0.4, 0.1])
    assert 0.0 <= score <= 1.0


def test_balanced_accuracy_accepts_probabilities():
    """balanced_accuracy also thresholds internally."""
    score = REGISTRY["balanced_accuracy"].fn([0, 1, 1, 0], [0.2, 0.9, 0.4, 0.1])
    assert 0.0 <= score <= 1.0


def test_multiclass_label_metric_uses_argmax():
    """For a 2-D probability matrix, hard-label metrics take the argmax."""
    probabilities = [[0.8, 0.1, 0.1], [0.1, 0.7, 0.2], [0.2, 0.2, 0.6]]
    assert REGISTRY["accuracy"].fn([0, 1, 2], probabilities) == pytest.approx(1.0)


def test_needs_labels_flags():
    """Only the hard-label metrics declare needs_labels."""
    for name in LABEL_METRICS:
        assert REGISTRY[name].needs_labels is True, name
    for name in SCORE_METRICS:
        assert REGISTRY[name].needs_labels is False, name


def test_roc_auc_on_multiclass_raises():
    """Selecting roc_auc for a multiclass target names the actual task."""
    with pytest.raises(ValueError) as excinfo:
        resolve_metric(_cfg("roc_auc", True), MULTICLASS)
    assert str(excinfo.value).startswith(
        "roc_auc requires a binary classification target; got classification with 3 classes"
    )


def test_roc_auc_on_regression_raises():
    """Selecting roc_auc for a regression target is rejected the same way."""
    with pytest.raises(ValueError) as excinfo:
        resolve_metric(_cfg("roc_auc", True), REGRESSION)
    assert str(excinfo.value).endswith("got regression")


def test_unknown_metric_raises():
    """An unsupported metric name lists the supported ones."""
    with pytest.raises(ValueError, match="Unknown metric"):
        resolve_metric(_cfg("logloss"), BINARY)


def test_greater_is_better_conflict_raises():
    """A configured direction that contradicts the registry is a loud error, not a warning."""
    with pytest.raises(ValueError, match="minimised"):
        resolve_metric(_cfg("rmse", True), REGRESSION)


def test_greater_is_better_null_takes_registry_value():
    """null means take the registry's direction, which is what the test fixtures rely on."""
    assert resolve_metric(_cfg("rmse", None), REGRESSION)[2] is False
    assert resolve_metric(_cfg("accuracy", None), MULTICLASS)[2] is True
