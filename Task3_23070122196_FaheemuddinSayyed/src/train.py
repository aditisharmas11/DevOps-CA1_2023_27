"""Cross-validated training: fits fold models and writes metrics and OOF predictions."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src.config import ensure_dirs
from src.contract import DataContract, derive_contract, save_contract
from src.data import get_cv_splitter, load_raw, validate
from src.features import build_preprocessor, encode_target, save_preprocessor, select_features
from src.metrics import resolve_metric
from src.models import build_model, enabled_models

LOGGER = logging.getLogger(__name__)

LGBM_EVAL_METRIC = {"roc_auc": "auc", "rmse": "rmse", "mae": "l1"}
LOW_AUC_INVERTED = 0.5
LOW_AUC_SUSPICIOUS = 0.6


def _jsonable(value: Any) -> Any:
    """Recursively convert Paths and numpy scalars so json.dump can serialise the value."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value


def _log_progress(done: int, total: int, elapsed: float, progress: bool = True) -> None:
    """Log cumulative elapsed time and an ETA derived from mean fold time so far."""
    mean = elapsed / done
    log = LOGGER.info if progress else LOGGER.debug
    log(
        "progress %d/%d model-folds | elapsed %.1fs | mean %.1fs/fold | est. remaining %.1fs",
        done,
        total,
        elapsed,
        mean,
        mean * (total - done),
    )


def _prepare(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, DataContract, np.ndarray, np.ndarray, Any]:
    """Load data, derive and validate the contract, then fit and persist the preprocessor."""
    ensure_dirs(cfg)
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    validate(train, test, contract)
    LOGGER.info(
        "contract: id=%s target=%s task=%s n_classes=%s | %d features (%d numeric, %d categorical)",
        contract.id_column,
        contract.target_column,
        contract.task_type,
        contract.n_classes,
        len(contract.feature_columns),
        len(contract.numeric_features),
        len(contract.categorical_features),
    )
    LOGGER.info("shapes: train=%s test=%s", train.shape, test.shape)

    models_dir = Path(cfg["paths"]["models_dir"])
    preprocessor = build_preprocessor(contract, cfg, train)
    x_all = preprocessor.fit_transform(select_features(train, contract))
    y_all, label_encoder = encode_target(train[contract.target_column], contract)
    LOGGER.info(
        "preprocessor fitted once on the full training set: X=%s (%d columns from %d features)",
        x_all.shape,
        x_all.shape[1],
        len(contract.feature_columns),
    )
    save_preprocessor(preprocessor, models_dir / "preprocessor.pkl")
    save_contract(
        contract,
        models_dir / "contract.json",
        label_classes=None if label_encoder is None else list(label_encoder.classes_),
    )
    return train, contract, x_all, y_all, label_encoder


def _lgbm_fit_kwargs(
    spec: dict[str, Any],
    cfg: dict[str, Any],
    x_val: np.ndarray,
    y_val: np.ndarray,
    metric_name: str,
) -> dict[str, Any]:
    """Build LightGBM fit kwargs: the fold's eval set, progress logging, early stopping."""
    progress = bool(cfg["runtime"]["progress"])
    period = int(cfg["runtime"]["log_every_n_iterations"])
    callbacks: list[Any] = []
    if progress and period > 0:
        callbacks.append(lgb.log_evaluation(period=period))
    rounds = spec.get("early_stopping_rounds")
    if rounds:
        callbacks.append(lgb.early_stopping(stopping_rounds=int(rounds), verbose=progress))
    # eval_X/eval_y, not the eval_set=[(X, y)] form: LightGBM 4.7 deprecates eval_set and
    # warns on every fit, which would pollute the progress output §7a asks to keep readable.
    kwargs: dict[str, Any] = {"eval_X": x_val, "eval_y": y_val}
    eval_metric = LGBM_EVAL_METRIC.get(metric_name)
    if eval_metric:
        kwargs["eval_metric"] = eval_metric
    if callbacks:
        kwargs["callbacks"] = callbacks
    return kwargs


def _oof_predict(model: Any, x_val: np.ndarray, contract: DataContract) -> np.ndarray:
    """Predict probabilities for classification (CLAUDE.md §5a) or raw values for regression."""
    if not contract.is_classification:
        return np.asarray(model.predict(x_val), dtype=float)
    proba = model.predict_proba(x_val)
    if contract.is_binary:
        return np.asarray(proba[:, 1], dtype=float)
    return np.asarray(proba, dtype=float)


def _fit_fold(
    spec: dict[str, Any],
    cfg: dict[str, Any],
    contract: DataContract,
    split: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    metric_name: str,
) -> tuple[Any, np.ndarray, int | None]:
    """Fit one fold and return (model, validation predictions, best iteration if any)."""
    x_tr, y_tr, x_val, y_val = split
    model = build_model(
        spec["name"],
        spec["params"],
        contract,
        int(cfg["project"]["seed"]),
        int(cfg["runtime"]["n_jobs"]),
    )
    if spec["name"] == "lightgbm":
        model.fit(x_tr, y_tr, **_lgbm_fit_kwargs(spec, cfg, x_val, y_val, metric_name))
    else:
        model.fit(x_tr, y_tr)
    best_iteration = getattr(model, "best_iteration_", None) or None
    return model, _oof_predict(model, x_val, contract), best_iteration


def _allocate_oof(contract: DataContract, n_rows: int) -> np.ndarray:
    """Allocate the OOF array: one column for binary/regression, one per class otherwise."""
    if contract.is_classification and not contract.is_binary:
        return np.zeros((n_rows, int(contract.n_classes or 0)))
    return np.zeros(n_rows)


def _train_one_model(
    spec: dict[str, Any],
    cfg: dict[str, Any],
    contract: DataContract,
    x_all: np.ndarray,
    y_all: np.ndarray,
    splitter: Any,
    metric_fn: Callable[[Any, Any], float],
    metric_name: str,
    on_fold_done: Callable[[], None],
) -> dict[str, Any]:
    """Fit every fold for one model, accumulating OOF predictions, scores, and timings."""
    models_dir = Path(cfg["paths"]["models_dir"])
    n_splits = int(cfg["cv"]["n_splits"])
    # CLAUDE.md §7a: progress false means stage-level logging only, so the per-fold lines
    # drop to DEBUG. Nothing downstream may depend on progress being true.
    log = LOGGER.info if bool(cfg["runtime"]["progress"]) else LOGGER.debug
    oof = _allocate_oof(contract, len(y_all))
    scores: list[float] = []
    seconds: list[float] = []
    best_iterations: list[int | None] = []

    for fold, (train_idx, val_idx) in enumerate(splitter.split(x_all, y_all)):
        log(
            "%s | fold %d/%d | fit rows=%d val rows=%d",
            spec["name"],
            fold + 1,
            n_splits,
            len(train_idx),
            len(val_idx),
        )
        fold_started = time.perf_counter()
        split = (x_all[train_idx], y_all[train_idx], x_all[val_idx], y_all[val_idx])
        model, predictions, best_iteration = _fit_fold(spec, cfg, contract, split, metric_name)
        oof[val_idx] = predictions
        joblib.dump(model, models_dir / f"{spec['name']}_fold{fold}.pkl")

        score = float(metric_fn(y_all[val_idx], oof[val_idx]))
        fold_seconds = time.perf_counter() - fold_started
        scores.append(score)
        seconds.append(fold_seconds)
        best_iterations.append(best_iteration)
        log(
            "%s | fold %d/%d | %s=%.6f | %.1fs%s",
            spec["name"],
            fold + 1,
            n_splits,
            metric_name,
            score,
            fold_seconds,
            "" if best_iteration is None else f" | best_iteration={best_iteration}",
        )
        on_fold_done()

    return {"oof": oof, "folds": scores, "seconds": seconds, "best_iterations": best_iterations}


def _blend(oof_by_model: dict[str, np.ndarray], specs: list[dict[str, Any]]) -> np.ndarray:
    """Average probabilities across models by their normalised weights, never labels."""
    blended = np.zeros_like(oof_by_model[specs[0]["name"]], dtype=float)
    for spec in specs:
        blended += oof_by_model[spec["name"]] * float(spec["weight"])
    return blended


def _oof_columns(name: str, values: np.ndarray) -> dict[str, np.ndarray]:
    """Name the OOF column(s) for one model: one column, or one per class for multiclass."""
    if values.ndim == 1:
        return {f"oof_{name}": values}
    return {f"oof_{name}_class{index}": values[:, index] for index in range(values.shape[1])}


def _write_oof_csv(
    path: Path,
    train: pd.DataFrame,
    contract: DataContract,
    oof_by_model: dict[str, np.ndarray],
    blended: np.ndarray,
) -> None:
    """Write ID, the original target, each model's OOF predictions, and the blend."""
    columns: dict[str, Any] = {
        contract.id_column: train[contract.id_column].to_numpy(),
        contract.target_column: train[contract.target_column].to_numpy(),
    }
    for name, values in oof_by_model.items():
        columns.update(_oof_columns(name, values))
    columns.update(_oof_columns("blend", blended))
    pd.DataFrame(columns).to_csv(path, index=False)
    LOGGER.info("wrote %s", path)


def _warn_on_implausible_score(metric_name: str, score: float) -> None:
    """Warn, never raise, when a blended ROC AUC suggests inverted or misaligned labels."""
    if metric_name != "roc_auc":
        return
    if score < LOW_AUC_INVERTED:
        LOGGER.warning(
            "blended %s is %.4f (< 0.5): the probability column is probably inverted or "
            "labels are misaligned",
            metric_name,
            score,
        )
    elif score < LOW_AUC_SUSPICIOUS:
        LOGGER.warning(
            "blended %s is %.4f (< 0.6): suspiciously low for this dataset — check preprocessing",
            metric_name,
            score,
        )


def _build_metrics(
    cfg: dict[str, Any],
    contract: DataContract,
    metric_name: str,
    greater_is_better: bool,
    specs: list[dict[str, Any]],
    results: dict[str, dict[str, Any]],
    blend_score: float,
    runtime_seconds: float,
) -> dict[str, Any]:
    """Assemble the reports/metrics.json payload."""
    per_model = {
        name: {
            "folds": [float(score) for score in result["folds"]],
            "mean": float(np.mean(result["folds"])),
            "std": float(np.std(result["folds"])),
        }
        for name, result in results.items()
    }
    best_iterations = {
        name: [int(value) for value in result["best_iterations"] if value is not None]
        for name, result in results.items()
        if any(value is not None for value in result["best_iterations"])
    }
    return {
        "metric": metric_name,
        "greater_is_better": bool(greater_is_better),
        "task_type": contract.task_type,
        "n_splits": int(cfg["cv"]["n_splits"]),
        "per_model": per_model,
        "blend": {
            "weights": {spec["name"]: float(spec["weight"]) for spec in specs},
            "score": float(blend_score),
        },
        "runtime_seconds": float(runtime_seconds),
        "fold_seconds": {
            name: [float(value) for value in result["seconds"]] for name, result in results.items()
        },
        "best_iterations": best_iterations,
        "config_snapshot": _jsonable(cfg),
    }


def run_train(cfg: dict[str, Any]) -> dict[str, Any]:
    """Run K-fold cross-validated training and write models, metrics, and OOF predictions."""
    started = time.perf_counter()
    LOGGER.info("train: start")
    train, contract, x_all, y_all, _ = _prepare(cfg)
    metric_name, metric_fn, greater_is_better = resolve_metric(cfg, contract)
    specs = enabled_models(cfg)
    LOGGER.info(
        "metric=%s (greater_is_better=%s) | models: %s",
        metric_name,
        greater_is_better,
        ", ".join(f"{spec['name']} w={spec['weight']:.3f}" for spec in specs),
    )

    splitter = get_cv_splitter(cfg, contract)
    total = len(specs) * int(cfg["cv"]["n_splits"])
    done = 0

    progress = bool(cfg["runtime"]["progress"])

    def on_fold_done() -> None:
        nonlocal done
        done += 1
        _log_progress(done, total, time.perf_counter() - started, progress)

    results: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(specs, start=1):
        LOGGER.info("model %d/%d: %s", index, len(specs), spec["name"])
        results[spec["name"]] = _train_one_model(
            spec, cfg, contract, x_all, y_all, splitter, metric_fn, metric_name, on_fold_done
        )

    oof_by_model = {name: result["oof"] for name, result in results.items()}
    blended = _blend(oof_by_model, specs)
    blend_score = float(metric_fn(y_all, blended))
    _warn_on_implausible_score(metric_name, blend_score)

    runtime_seconds = time.perf_counter() - started
    metrics = _build_metrics(
        cfg,
        contract,
        metric_name,
        greater_is_better,
        specs,
        results,
        blend_score,
        runtime_seconds,
    )

    reports_dir = Path(cfg["paths"]["reports_dir"])
    metrics_path = reports_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("wrote %s", metrics_path)
    _write_oof_csv(reports_dir / "oof_predictions.csv", train, contract, oof_by_model, blended)

    for name, entry in metrics["per_model"].items():
        LOGGER.info(
            "summary | %-9s %s mean=%.6f std=%.6f folds=%s",
            name,
            metric_name,
            entry["mean"],
            entry["std"],
            [round(score, 6) for score in entry["folds"]],
        )
    LOGGER.info("summary | blend     %s=%.6f", metric_name, blend_score)
    LOGGER.info("train: done in %.1fs", runtime_seconds)
    return metrics
