"""Preprocessing pipeline construction, target encoding, and preprocessor persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder, StandardScaler

if TYPE_CHECKING:
    from src.contract import DataContract

LOGGER = logging.getLogger(__name__)

UNKNOWN_CATEGORY_CODE = -1
VALID_ENCODINGS = ("ordinal", "onehot")


def select_features(frame: pd.DataFrame, contract: DataContract) -> pd.DataFrame:
    """Return the contract's feature columns, in the order the preprocessor expects."""
    missing = [column for column in contract.feature_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Columns missing from the frame: {sorted(missing)}.")
    return frame[contract.feature_columns]


def _numeric_pipeline(cfg: dict[str, Any]) -> Pipeline:
    """Impute numeric columns, optionally flag imputed values, optionally standardise."""
    steps: list[tuple[str, Any]] = [
        (
            "impute",
            SimpleImputer(
                strategy=str(cfg["features"]["numeric_imputation"]),
                add_indicator=bool(cfg["features"]["add_missing_indicators"]),
            ),
        ),
    ]
    if bool(cfg["features"]["scale_numeric"]):
        steps.append(("scale", StandardScaler()))
    return Pipeline(steps=steps)


def _categorical_pipeline(cfg: dict[str, Any], encoding: str) -> Pipeline:
    """Impute categorical columns then encode them as ordinal codes or one-hot columns."""
    imputer = SimpleImputer(strategy=str(cfg["features"]["categorical_imputation"]))
    if encoding == "onehot":
        encoder: Any = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    else:
        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=UNKNOWN_CATEGORY_CODE
        )
    return Pipeline(steps=[("impute", imputer), ("encode", encoder)])


def _plan_categorical_encoding(
    contract: DataContract, cfg: dict[str, Any], train: pd.DataFrame | None
) -> tuple[list[str], list[str]]:
    """Split categorical columns into (one-hot, ordinal) according to config and cardinality."""
    categorical = list(contract.categorical_features)
    if str(cfg["features"]["categorical_encoding"]) == "ordinal":
        return [], categorical
    if train is None:
        return categorical, []
    max_cardinality = int(cfg["features"]["max_onehot_cardinality"])
    onehot: list[str] = []
    ordinal: list[str] = []
    for column in categorical:
        cardinality = int(train[column].nunique(dropna=True))
        if cardinality > max_cardinality:
            LOGGER.warning(
                "column '%s' has cardinality %d > max_onehot_cardinality %d; "
                "falling back to ordinal",
                column,
                cardinality,
                max_cardinality,
            )
            ordinal.append(column)
        else:
            onehot.append(column)
    return onehot, ordinal


def build_preprocessor(
    contract: DataContract, cfg: dict[str, Any], train: pd.DataFrame | None = None
) -> ColumnTransformer:
    """Build the numeric/categorical ColumnTransformer described by the config."""
    encoding = str(cfg["features"]["categorical_encoding"])
    if encoding not in VALID_ENCODINGS:
        raise ValueError(
            f"features.categorical_encoding must be one of {VALID_ENCODINGS}; got '{encoding}'."
        )
    onehot_columns, ordinal_columns = _plan_categorical_encoding(contract, cfg, train)
    transformers: list[tuple[str, Any, list[str]]] = []
    if contract.numeric_features:
        transformers.append(("numeric", _numeric_pipeline(cfg), contract.numeric_features))
    if onehot_columns:
        transformers.append(
            ("categorical_onehot", _categorical_pipeline(cfg, "onehot"), onehot_columns)
        )
    if ordinal_columns:
        transformers.append(
            ("categorical_ordinal", _categorical_pipeline(cfg, "ordinal"), ordinal_columns)
        )
    return ColumnTransformer(
        transformers=transformers, remainder="drop", verbose_feature_names_out=False
    )


def encode_target(y: pd.Series, contract: DataContract) -> tuple[np.ndarray, LabelEncoder | None]:
    """Label-encode a classification target; pass a regression target through as floats."""
    if not contract.is_classification:
        return y.to_numpy(dtype=float), None
    encoder = LabelEncoder()
    return encoder.fit_transform(y), encoder


def save_preprocessor(preprocessor: ColumnTransformer, path: Path) -> None:
    """Persist a fitted preprocessor with joblib."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, path)


def load_preprocessor(path: Path) -> ColumnTransformer:
    """Load a preprocessor persisted by save_preprocessor."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run `make train` first.")
    return joblib.load(path)
