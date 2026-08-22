"""Inference: fold-averaged, weight-blended predictions written to a submission file."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.config import ensure_dirs
from src.contract import DataContract, load_contract
from src.data import raw_path
from src.features import load_preprocessor, select_features
from src.metrics import BINARY_THRESHOLD
from src.models import enabled_models

LOGGER = logging.getLogger(__name__)

NO_MODELS_MESSAGE = "No trained models found in {models_dir}. Run `make train` first."


def _fold_index(path: Path, name: str) -> int | None:
    """Parse the fold index out of a `{name}_fold{k}.pkl` filename, or None if it is not one.

    Filenames that merely resemble the pattern are rejected rather than crashing. Docker
    Desktop bind mounts on macOS have been observed creating duplicates such as
    `lightgbm_fold0 2.pkl`, which the glob matches but `int()` cannot parse.
    """
    suffix = path.stem.removeprefix(f"{name}_fold")
    return int(suffix) if suffix.isdigit() else None


def _fold_model_paths(models_dir: Path, name: str) -> list[Path]:
    """Return one model's fold artifacts, ordered by fold index rather than lexically."""
    indexed = [
        (index, path)
        for path in models_dir.glob(f"{name}_fold*.pkl")
        if (index := _fold_index(path, name)) is not None
    ]
    if not indexed:
        raise FileNotFoundError(NO_MODELS_MESSAGE.format(models_dir=models_dir))
    skipped = len(list(models_dir.glob(f"{name}_fold*.pkl"))) - len(indexed)
    if skipped:
        LOGGER.warning(
            "ignored %d file(s) in %s matching '%s_fold*.pkl' but not '%s_fold<int>.pkl'",
            skipped,
            models_dir,
            name,
            name,
        )
    return [path for _, path in sorted(indexed)]


def _predict_one(model: Any, x_test: np.ndarray, contract: DataContract) -> np.ndarray:
    """Predict probabilities for classification (CLAUDE.md §5a) or raw values for regression."""
    if not contract.is_classification:
        return np.asarray(model.predict(x_test), dtype=float)
    proba = model.predict_proba(x_test)
    if contract.is_binary:
        return np.asarray(proba[:, 1], dtype=float)
    return np.asarray(proba, dtype=float)


def _average_folds(
    paths: list[Path], x_test: np.ndarray, contract: DataContract, progress: bool = True
) -> np.ndarray:
    """Average one model's predictions across its folds, loading one estimator at a time."""
    total: np.ndarray | None = None
    log = LOGGER.info if progress else LOGGER.debug
    for index, path in enumerate(paths, start=1):
        prediction = _predict_one(joblib.load(path), x_test, contract)
        total = prediction if total is None else total + prediction
        log("averaged fold %d/%d from %s", index, len(paths), path.name)
    return total / len(paths)  # type: ignore[operator]


def _blend(predictions: dict[str, np.ndarray], specs: list[dict[str, Any]]) -> np.ndarray:
    """Average probabilities across models by their normalised weights, never labels."""
    blended = np.zeros_like(predictions[specs[0]["name"]], dtype=float)
    for spec in specs:
        blended += predictions[spec["name"]] * float(spec["weight"])
    return blended


def _clip(values: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    """Clamp probabilities into output.clip_probabilities, logging how many were clipped."""
    low, high = (float(bound) for bound in cfg["output"]["clip_probabilities"])
    clipped = np.clip(values, low, high)
    changed = int(np.count_nonzero(clipped != values))
    if changed:
        LOGGER.info("clipped %d value(s) into [%s, %s]", changed, low, high)
    return clipped


def _as_label_values(
    blended: np.ndarray, contract: DataContract, label_classes: list[Any] | None
) -> np.ndarray:
    """Map blended probabilities back to the original label values (the rounding branch)."""
    if label_classes is None:
        raise ValueError(
            "output.round_predictions_to_labels is true but models/contract.json has no "
            "label_classes. Re-run `make train` on a classification target."
        )
    classes = np.asarray(label_classes)
    if blended.ndim == 1:
        indices = (blended >= BINARY_THRESHOLD).astype(int)
    else:
        indices = blended.argmax(axis=1)
    return classes[indices]


def _validate_ids(submission: pd.DataFrame, sample_sub: pd.DataFrame, id_column: str) -> None:
    """Raise ValueError when the submission's ID column drifts from the sample submission."""
    left = submission[id_column].to_numpy()
    right = sample_sub[id_column].to_numpy()
    if not np.array_equal(left, right):
        position = int(np.flatnonzero(left != right)[0])
        raise ValueError(
            f"Submission ID column does not match sample_submission elementwise; "
            f"first mismatch at row {position}."
        )


def _validate_probabilities(values: np.ndarray, target_column: str) -> None:
    """Enforce the CLAUDE.md §5a guarantees: values in [0, 1] and more than two distinct."""
    low, high = float(np.min(values)), float(np.max(values))
    if low < 0.0 or high > 1.0:
        raise ValueError(f"Submission target values fall outside [0, 1]: min={low}, max={high}.")
    n_distinct = int(pd.Series(values).nunique())
    if n_distinct <= 2:
        raise ValueError(
            f"Submission target column '{target_column}' has only {n_distinct} distinct "
            f"value(s); expected probabilities. This is the labels-instead-of-probabilities "
            f"bug described in CLAUDE.md §5a."
        )


def _validate_submission(
    submission: pd.DataFrame,
    sample_sub: pd.DataFrame,
    contract: DataContract,
    cfg: dict[str, Any],
) -> None:
    """Assert the submission matches the sample submission and holds the expected values."""
    if len(submission) != len(sample_sub):
        raise ValueError(
            f"Submission has {len(submission)} rows but sample_submission has {len(sample_sub)}."
        )
    if list(submission.columns) != list(sample_sub.columns):
        raise ValueError(
            f"Submission columns {list(submission.columns)} do not match "
            f"sample_submission columns {list(sample_sub.columns)}."
        )
    _validate_ids(submission, sample_sub, contract.id_column)

    values = submission[contract.target_column].to_numpy()
    non_finite = int(np.count_nonzero(~np.isfinite(values.astype(float))))
    if non_finite:
        raise ValueError(f"Submission target column has {non_finite} null or non-finite value(s).")
    if contract.is_binary and not bool(cfg["output"]["round_predictions_to_labels"]):
        _validate_probabilities(values, contract.target_column)


def _log_distribution(values: np.ndarray, target_column: str) -> None:
    """Log the count, range, mean, and distinct count of the written column (CLAUDE.md §7a)."""
    LOGGER.info(
        "submission %s: count=%d min=%.6f mean=%.6f max=%.6f distinct=%d",
        target_column,
        len(values),
        float(np.min(values)),
        float(np.mean(values)),
        float(np.max(values)),
        int(pd.Series(values).nunique()),
    )


def run_predict(cfg: dict[str, Any]) -> Path:
    """Blend fold-averaged predictions into submissions/submission.csv and validate it."""
    started = time.perf_counter()
    LOGGER.info("predict: start")
    ensure_dirs(cfg)
    progress = bool(cfg["runtime"]["progress"])
    models_dir = Path(cfg["paths"]["models_dir"])

    contract, label_classes = load_contract(models_dir / "contract.json")
    test = pd.read_csv(raw_path(cfg, "test_file"))
    sample_sub = pd.read_csv(raw_path(cfg, "sample_submission_file"))
    LOGGER.info("loaded test=%s sample_submission=%s", test.shape, sample_sub.shape)

    preprocessor = load_preprocessor(models_dir / "preprocessor.pkl")
    x_test = preprocessor.transform(select_features(test, contract))
    LOGGER.info("transformed test features: %s", x_test.shape)

    specs = enabled_models(cfg)
    predictions: dict[str, np.ndarray] = {}
    for spec in specs:
        paths = _fold_model_paths(models_dir, spec["name"])
        LOGGER.info(
            "%s | averaging %d fold(s) | weight=%.3f", spec["name"], len(paths), spec["weight"]
        )
        predictions[spec["name"]] = _average_folds(paths, x_test, contract, progress)

    blended = _blend(predictions, specs)
    rounding = bool(cfg["output"]["round_predictions_to_labels"])
    if contract.is_classification and not rounding:
        blended = _clip(blended, cfg)
    values = _as_label_values(blended, contract, label_classes) if rounding else blended

    submission = sample_sub.copy()
    submission[contract.target_column] = values
    _validate_submission(submission, sample_sub, contract, cfg)

    path = Path(cfg["paths"]["submissions_dir"]) / str(cfg["output"]["submission_filename"])
    submission.to_csv(path, index=False)
    _log_distribution(submission[contract.target_column].to_numpy(), contract.target_column)
    LOGGER.info("wrote %s", path)
    LOGGER.info("predict: done in %.1fs", time.perf_counter() - started)
    return path
