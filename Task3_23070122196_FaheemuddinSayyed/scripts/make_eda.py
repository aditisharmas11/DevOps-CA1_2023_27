"""Generate the four EDA figures into reports/figures/."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

# matplotlib.use must run before pyplot is imported, which forces these imports below it.
# E402 is suppressed only here, for that reason.
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.cli import configure_logging  # noqa: E402
from src.config import ensure_dirs, load_config  # noqa: E402
from src.contract import DataContract, derive_contract  # noqa: E402
from src.data import load_raw  # noqa: E402
from src.features import load_preprocessor  # noqa: E402

LOGGER = logging.getLogger("scripts.make_eda")
FIGURE_SIZE = (9, 6)
DPI = 120


def _save(fig: plt.Figure, path: Path) -> Path:
    """Write a figure and close it, so a long session does not leak handles."""
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    LOGGER.info("wrote %s", path)
    return path


def _plot_target_distribution(
    train: pd.DataFrame, contract: DataContract, figures_dir: Path
) -> Path:
    """Bar chart of class counts for classification, histogram for regression."""
    target = train[contract.target_column]
    fig, axes = plt.subplots(figsize=FIGURE_SIZE)
    if contract.is_classification:
        counts = target.value_counts().sort_index()
        total = int(counts.sum())
        bars = axes.bar([str(value) for value in counts.index], counts.to_numpy())
        for bar, count in zip(bars, counts.to_numpy(), strict=True):
            axes.annotate(
                f"{int(count):,}\n{100.0 * int(count) / total:.2f}%",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center",
                va="bottom",
            )
        axes.set_ylabel("rows")
        axes.set_ylim(0, counts.max() * 1.18)
        axes.set_title(f"Target distribution: {contract.target_column}")
    else:
        axes.hist(target.dropna(), bins=50)
        axes.set_ylabel("rows")
        axes.set_title(f"Target distribution: {contract.target_column}")
    axes.set_xlabel(contract.target_column)
    return _save(fig, figures_dir / "target_distribution.png")


def _plot_missing_values(train: pd.DataFrame, figures_dir: Path) -> Path:
    """Horizontal bars of per-column null counts, or an annotation when there are none."""
    nulls = train.isna().sum()
    nulls = nulls[nulls > 0].sort_values()
    fig, axes = plt.subplots(figsize=FIGURE_SIZE)
    if nulls.empty:
        axes.text(0.5, 0.5, "no missing values", ha="center", va="center", fontsize=14)
        axes.set_xticks([])
        axes.set_yticks([])
    else:
        total = len(train)
        axes.barh(list(nulls.index), nulls.to_numpy())
        for index, count in enumerate(nulls.to_numpy()):
            axes.annotate(
                f" {int(count):,} ({100.0 * int(count) / total:.1f}%)",
                (count, index),
                va="center",
            )
        axes.set_xlabel("missing rows")
        axes.set_xlim(0, nulls.max() * 1.25)
    axes.set_title("Missing values per column (train)")
    return _save(fig, figures_dir / "missing_values.png")


def _plot_numeric_correlations(
    train: pd.DataFrame, contract: DataContract, figures_dir: Path
) -> Path:
    """imshow heatmap of the numeric feature correlation matrix."""
    corr = train[contract.numeric_features].corr()
    fig, axes = plt.subplots(figsize=(8, 7))
    image = axes.imshow(corr.to_numpy(), cmap="coolwarm", vmin=-1.0, vmax=1.0)
    fig.colorbar(image, ax=axes, fraction=0.046, pad=0.04)
    axes.set_xticks(range(len(corr.columns)))
    axes.set_yticks(range(len(corr.columns)))
    axes.set_xticklabels(corr.columns, rotation=45, ha="right")
    axes.set_yticklabels(corr.columns)
    axes.set_title("Numeric feature correlations")
    return _save(fig, figures_dir / "numeric_correlations.png")


def _importance_names(models_dir: Path, n_importances: int) -> list[str]:
    """Name the transformed columns from the persisted preprocessor, or fall back to f0..fN."""
    preprocessor_path = models_dir / "preprocessor.pkl"
    names: list[str] = []
    if preprocessor_path.is_file():
        names = list(load_preprocessor(preprocessor_path).get_feature_names_out())
    if len(names) != n_importances:
        names = [f"f{index}" for index in range(n_importances)]
    return names


def _plot_feature_importance(models_dir: Path, figures_dir: Path) -> Path | None:
    """Fold-0 LightGBM gains, or None with a notice when the model is not on disk."""
    model_path = models_dir / "lightgbm_fold0.pkl"
    if not model_path.is_file():
        LOGGER.info(
            "%s not found; skipping feature_importance.png — run `make train` first",
            model_path,
        )
        return None
    import joblib

    importances = np.asarray(joblib.load(model_path).feature_importances_, dtype=float)
    names = _importance_names(models_dir, len(importances))
    order = np.argsort(importances)
    fig, axes = plt.subplots(figsize=(9, 7))
    axes.barh([names[index] for index in order], importances[order])
    axes.set_xlabel("LightGBM split gain")
    axes.set_title("Feature importance (lightgbm, fold 0)")
    return _save(fig, figures_dir / "feature_importance.png")


def main() -> int:
    """Generate every EDA figure and print the path of each one written."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    configure_logging(args.log_level)
    try:
        cfg = load_config(args.config)
        ensure_dirs(cfg)
        train, _, sample_sub = load_raw(cfg)
        contract = derive_contract(train, sample_sub, cfg)
        figures_dir = Path(cfg["paths"]["figures_dir"])
        models_dir = Path(cfg["paths"]["models_dir"])
        written = [
            _plot_target_distribution(train, contract, figures_dir),
            _plot_missing_values(train, figures_dir),
            _plot_numeric_correlations(train, contract, figures_dir),
            _plot_feature_importance(models_dir, figures_dir),
        ]
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        if path is not None:
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
