"""End-to-end train then predict on the committed fixtures, with the §5a probability guards."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from conftest import FIXTURES_DIR, make_config

from src.predict import _fold_model_paths, run_predict
from src.train import run_train


def _sample_submission(fixture: str) -> pd.DataFrame:
    """Read the fixture's own sample submission, the thing the output must match."""
    return pd.read_csv(FIXTURES_DIR / fixture / "sample_submission.csv")


def _run_pipeline(cfg: dict) -> Path:
    """Train then predict, returning the submission path."""
    run_train(cfg)
    return run_predict(cfg)


def test_clf_smoke_writes_probability_submission(tmp_path):
    """The whole pipeline on the binary fixture writes float probabilities, never labels."""
    cfg = make_config(tmp_path, "clf")
    path = _run_pipeline(cfg)
    assert path.is_file()

    sub = pd.read_csv(path)
    sample = _sample_submission("clf")
    target = sample.columns[1]
    assert sub.shape == sample.shape
    assert list(sub.columns) == list(sample.columns)
    assert np.array_equal(sub[sample.columns[0]].to_numpy(), sample[sample.columns[0]].to_numpy())
    assert sub[target].notna().all()
    assert sub[target].dtype.kind == "f"
    assert sub[target].between(0.0, 1.0).all()
    assert sub[target].nunique() > 2, "labels leaked in where probabilities belong (CLAUDE.md §5a)"


def test_clf_smoke_metrics_json(tmp_path):
    """metrics.json records the auto-resolved metric and a plausible blended score."""
    cfg = make_config(tmp_path, "clf")
    _run_pipeline(cfg)
    metrics = json.loads((tmp_path / "reports" / "metrics.json").read_text())

    assert metrics["metric"] == "roc_auc"
    assert metrics["greater_is_better"] is True
    assert metrics["task_type"] == "classification"
    assert metrics["n_splits"] == 2
    for entry in metrics["per_model"].values():
        assert len(entry["folds"]) == 2
        assert all(0.0 <= score <= 1.0 for score in entry["folds"])
    score = metrics["blend"]["score"]
    assert isinstance(score, float) and math.isfinite(score)
    assert 0.0 <= score <= 1.0
    assert sum(metrics["blend"]["weights"].values()) == pytest.approx(1.0)


def test_clf_smoke_writes_expected_artifacts(tmp_path):
    """Every artifact predict depends on is persisted under the configured directories."""
    cfg = make_config(tmp_path, "clf")
    _run_pipeline(cfg)
    models = tmp_path / "models"
    expected = {
        "preprocessor.pkl",
        "contract.json",
        "lightgbm_fold0.pkl",
        "lightgbm_fold1.pkl",
        "hist_gbm_fold0.pkl",
        "hist_gbm_fold1.pkl",
    }
    assert expected <= {path.name for path in models.iterdir()}
    oof = pd.read_csv(tmp_path / "reports" / "oof_predictions.csv")
    assert len(oof) == 60


def test_oof_predictions_are_probabilities(tmp_path):
    """The blended OOF column is a probability, which is what metrics.json scored."""
    cfg = make_config(tmp_path, "clf")
    _run_pipeline(cfg)
    oof = pd.read_csv(tmp_path / "reports" / "oof_predictions.csv")
    assert oof["oof_blend"].between(0.0, 1.0).all()
    assert oof["oof_blend"].nunique() > 2


def test_clf_smoke_is_deterministic(tmp_path):
    """Two runs of the same config produce byte-identical submissions (CLAUDE.md §2)."""
    cfg = make_config(tmp_path, "clf")
    first = _run_pipeline(cfg).read_bytes()
    second = _run_pipeline(cfg).read_bytes()
    assert first == second


def test_reg_smoke_writes_continuous_submission(tmp_path):
    """The regression path writes unclipped continuous values and scores with rmse."""
    cfg = make_config(tmp_path, "reg")
    path = _run_pipeline(cfg)

    sub = pd.read_csv(path)
    sample = _sample_submission("reg")
    target = sample.columns[1]
    assert sub.shape == sample.shape
    assert list(sub.columns) == list(sample.columns)
    assert np.array_equal(sub[sample.columns[0]].to_numpy(), sample[sample.columns[0]].to_numpy())
    assert sub[target].notna().all()
    assert np.isfinite(sub[target].to_numpy()).all()

    metrics = json.loads((tmp_path / "reports" / "metrics.json").read_text())
    assert metrics["metric"] == "rmse"
    assert metrics["greater_is_better"] is False
    assert math.isfinite(metrics["blend"]["score"])
    assert metrics["blend"]["score"] > 0.0


def test_round_predictions_to_labels_writes_labels(tmp_path):
    """The hard-label branch S6E8 does not use still works and is covered."""
    cfg = make_config(tmp_path, "clf", output={"round_predictions_to_labels": True})
    path = _run_pipeline(cfg)
    sub = pd.read_csv(path)
    target = _sample_submission("clf").columns[1]
    assert set(sub[target].unique()).issubset({0, 1})
    assert sub[target].nunique() <= 2


def test_predict_without_models_raises(tmp_path):
    """Predicting before training points the user at make train instead of crashing."""
    cfg = make_config(tmp_path, "clf")
    with pytest.raises(FileNotFoundError, match="make train"):
        run_predict(cfg)


def test_fold_paths_ignore_lookalike_filenames(tmp_path):
    """A stray `name_fold0 2.pkl` (macOS/Docker duplicate) is skipped, not crashed on."""
    cfg = make_config(tmp_path, "clf")
    _run_pipeline(cfg)
    models = tmp_path / "models"
    (models / "lightgbm_fold0 2.pkl").write_bytes((models / "lightgbm_fold0.pkl").read_bytes())
    (models / "lightgbm_foldX.pkl").write_bytes(b"not a model")

    paths = _fold_model_paths(models, "lightgbm")
    assert [path.name for path in paths] == ["lightgbm_fold0.pkl", "lightgbm_fold1.pkl"]
    # and the pipeline still runs end to end with the strays present
    assert run_predict(cfg).is_file()


def test_fold_paths_missing_raises(tmp_path):
    """An empty models directory still raises the actionable message."""
    with pytest.raises(FileNotFoundError, match="make train"):
        _fold_model_paths(tmp_path, "lightgbm")
