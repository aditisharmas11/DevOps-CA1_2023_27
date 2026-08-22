"""Load, validate, and split the raw competition CSVs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold

if TYPE_CHECKING:
    from src.contract import DataContract

LOGGER = logging.getLogger(__name__)

COMPETITION_DATA_URL = "https://www.kaggle.com/competitions/playground-series-s6e8/data"
RAW_FILE_KEYS = ("train_file", "test_file", "sample_submission_file")


def raw_path(cfg: dict[str, Any], file_key: str) -> Path:
    """Join paths.raw_dir with the filename stored under paths.<file_key>."""
    return Path(cfg["paths"]["raw_dir"]) / str(cfg["paths"][file_key])


def _require(path: Path) -> None:
    """Raise an actionable FileNotFoundError when a required raw file is absent."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}.\n"
            f"Download the competition data from\n"
            f"{COMPETITION_DATA_URL}\n"
            f"and place train.csv, test.csv and sample_submission.csv in data/raw/."
        )


def load_raw(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (train, test, sample_submission), checking every file exists first."""
    paths = [raw_path(cfg, key) for key in RAW_FILE_KEYS]
    for path in paths:
        _require(path)
    train, test, sample_sub = (pd.read_csv(path) for path in paths)
    LOGGER.info(
        "loaded train=%s test=%s sample_submission=%s", train.shape, test.shape, sample_sub.shape
    )
    return train, test, sample_sub


def _validate_feature_sets(train: pd.DataFrame, test: pd.DataFrame, contract: DataContract) -> None:
    """Raise ValueError when train and test do not carry the same feature columns."""
    train_features = set(train.columns) - {contract.id_column, contract.target_column}
    test_features = set(test.columns) - {contract.id_column}
    if train_features != test_features:
        raise ValueError(
            f"train.csv and test.csv feature sets differ. "
            f"Only in train: {sorted(train_features - test_features)}. "
            f"Only in test: {sorted(test_features - train_features)}."
        )
    missing = set(contract.feature_columns) - test_features
    if missing:
        raise ValueError(f"Contract features missing from test.csv: {sorted(missing)}.")


def _validate_unique_ids(train: pd.DataFrame, test: pd.DataFrame, contract: DataContract) -> None:
    """Raise ValueError when the ID column repeats a value in either frame."""
    for filename, frame in (("train.csv", train), ("test.csv", test)):
        duplicated = frame[contract.id_column].duplicated()
        if bool(duplicated.any()):
            raise ValueError(
                f"ID column '{contract.id_column}' has {int(duplicated.sum())} "
                f"duplicate value(s) in {filename}."
            )


def validate(train: pd.DataFrame, test: pd.DataFrame, contract: DataContract) -> None:
    """Assert train and test agree with the contract, raising ValueError on any mismatch."""
    if contract.target_column not in train.columns:
        raise ValueError(f"Target column '{contract.target_column}' is missing from train.csv.")
    if contract.target_column in test.columns:
        raise ValueError(
            f"Target column '{contract.target_column}' must not be present in test.csv."
        )
    _validate_feature_sets(train, test, contract)
    _validate_unique_ids(train, test, contract)
    LOGGER.info("validated train/test against the contract")


def get_cv_splitter(cfg: dict[str, Any], contract: DataContract) -> KFold | StratifiedKFold:
    """StratifiedKFold for classification, KFold for regression, seeded from config."""
    shuffle = bool(cfg["cv"]["shuffle"])
    splitter_cls = StratifiedKFold if contract.is_classification else KFold
    return splitter_cls(
        n_splits=int(cfg["cv"]["n_splits"]),
        shuffle=shuffle,
        random_state=int(cfg["project"]["seed"]) if shuffle else None,
    )
