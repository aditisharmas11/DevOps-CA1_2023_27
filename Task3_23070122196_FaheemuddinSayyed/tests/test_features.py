"""Tests for the preprocessing pipeline, target encoding, and preprocessor persistence."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest
from conftest import make_config

from src.contract import DataContract, derive_contract
from src.data import load_raw
from src.features import (
    build_preprocessor,
    encode_target,
    load_preprocessor,
    save_preprocessor,
    select_features,
)


def _fixture(tmp_path, name: str, **overrides):
    """Return (cfg, train, test, contract) for one fixture set."""
    cfg = make_config(tmp_path, name, **overrides)
    train, test, sample_sub = load_raw(cfg)
    return cfg, train, test, derive_contract(train, sample_sub, cfg)


def test_preprocessor_output_has_no_nans(tmp_path):
    """Imputation removes every NaN the fixture deliberately injects."""
    cfg, train, test, contract = _fixture(tmp_path, "clf")
    preprocessor = build_preprocessor(contract, cfg, train)
    transformed_train = preprocessor.fit_transform(select_features(train, contract))
    transformed_test = preprocessor.transform(select_features(test, contract))
    assert train[["n1", "n2", "c1"]].isna().sum().sum() > 0
    assert np.isnan(transformed_train).sum() == 0
    assert np.isnan(transformed_test).sum() == 0


def test_ordinal_output_shape(tmp_path):
    """Default config yields 4 imputed numeric, 2 missing indicators, then 2 ordinal codes."""
    cfg, train, test, contract = _fixture(tmp_path, "clf")
    preprocessor = build_preprocessor(contract, cfg, train)
    assert preprocessor.fit_transform(select_features(train, contract)).shape == (60, 8)
    assert preprocessor.transform(select_features(test, contract)).shape == (20, 8)


def test_missing_indicator_columns_are_named(tmp_path):
    """get_feature_names_out identifies the indicator columns, which phase 07 plots by name."""
    cfg, train, _, contract = _fixture(tmp_path, "clf")
    preprocessor = build_preprocessor(contract, cfg, train)
    preprocessor.fit(select_features(train, contract))
    names = list(preprocessor.get_feature_names_out())
    assert names == [
        "n1",
        "n2",
        "n3",
        "n4",
        "missingindicator_n1",
        "missingindicator_n2",
        "c1",
        "c2",
    ]


def test_missing_indicators_can_be_disabled(tmp_path):
    """Turning the indicators off narrows the matrix and moves c1 back to index 4."""
    cfg, train, test, contract = _fixture(
        tmp_path, "clf", features={"add_missing_indicators": False}
    )
    preprocessor = build_preprocessor(contract, cfg, train)
    preprocessor.fit(select_features(train, contract))
    transformed = preprocessor.transform(select_features(test, contract))
    assert transformed.shape == (20, 6)
    assert transformed[0, 4] == -1


def test_unseen_category_encodes_to_minus_one(tmp_path):
    """A category absent from train encodes to -1 instead of raising."""
    cfg, train, test, contract = _fixture(tmp_path, "clf")
    preprocessor = build_preprocessor(contract, cfg, train)
    preprocessor.fit(select_features(train, contract))
    transformed = preprocessor.transform(select_features(test, contract))
    assert test.loc[0, "c1"] == "z"
    assert transformed[0, 6] == -1


def test_onehot_high_cardinality_falls_back_to_ordinal(tmp_path, caplog):
    """c2's 18 levels exceed max_onehot_cardinality, so it is ordinal-encoded with a warning."""
    cfg, train, _, contract = _fixture(tmp_path, "clf", features={"categorical_encoding": "onehot"})
    with caplog.at_level(logging.WARNING, logger="src.features"):
        preprocessor = build_preprocessor(contract, cfg, train)
    transformed = preprocessor.fit_transform(select_features(train, contract))
    assert transformed.shape == (60, 10)
    assert "max_onehot_cardinality" in caplog.text
    assert "c2" in caplog.text


def test_onehot_without_train_onehots_everything(tmp_path):
    """Without training data the cardinality is unknown, so every categorical is one-hot."""
    cfg, train, _, contract = _fixture(tmp_path, "clf", features={"categorical_encoding": "onehot"})
    preprocessor = build_preprocessor(contract, cfg, None)
    assert preprocessor.fit_transform(select_features(train, contract)).shape == (60, 27)


def test_scale_numeric_standardises(tmp_path):
    """With scale_numeric on, the imputed numeric columns are centred and unit-scaled."""
    cfg, train, _, contract = _fixture(tmp_path, "clf", features={"scale_numeric": True})
    preprocessor = build_preprocessor(contract, cfg, train)
    transformed = preprocessor.fit_transform(select_features(train, contract))
    numeric = transformed[:, :4]
    assert np.allclose(numeric.mean(axis=0), 0.0, atol=1e-9)
    assert np.allclose(numeric.std(axis=0), 1.0, atol=1e-9)


def test_invalid_encoding_raises(tmp_path):
    """An unsupported encoding name is rejected and both valid options are named."""
    cfg, _, _, contract = _fixture(tmp_path, "clf", features={"categorical_encoding": "target"})
    with pytest.raises(ValueError, match="ordinal"):
        build_preprocessor(contract, cfg)


def test_select_features_orders_columns(tmp_path):
    """select_features is the single source of column order for fit and transform."""
    _, train, _, contract = _fixture(tmp_path, "clf")
    selected = select_features(train, contract)
    assert list(selected.columns) == contract.feature_columns
    assert list(selected.columns) == ["n1", "n2", "n3", "n4", "c1", "c2"]


def test_select_features_missing_column_raises(tmp_path):
    """A frame lacking a contract feature fails loudly and names the column."""
    _, train, _, contract = _fixture(tmp_path, "clf")
    with pytest.raises(ValueError, match="n2"):
        select_features(train.drop(columns=["n2"]), contract)


def test_encode_target_classification(tmp_path):
    """A classification target is label-encoded and its encoder returned."""
    _, train, _, contract = _fixture(tmp_path, "clf")
    encoded, encoder = encode_target(train[contract.target_column], contract)
    assert sorted(set(encoded.tolist())) == [0, 1]
    assert encoder is not None
    assert len(encoder.classes_) == 2


def test_encode_target_regression(tmp_path):
    """A regression target passes through as floats with no encoder."""
    _, train, _, contract = _fixture(tmp_path, "reg")
    encoded, encoder = encode_target(train[contract.target_column], contract)
    assert encoder is None
    assert encoded.dtype.kind == "f"
    assert len(encoded) == 60


def test_encode_target_string_labels():
    """String class labels encode to indices while the original values stay recoverable."""
    contract = DataContract("id", "target", "classification", 2, [], [])
    encoded, encoder = encode_target(pd.Series(["no", "yes", "no"]), contract)
    assert list(encoded) == [0, 1, 0]
    assert list(encoder.classes_) == ["no", "yes"]


def test_preprocessor_roundtrip(tmp_path):
    """A persisted preprocessor transforms identically after being reloaded."""
    cfg, train, test, contract = _fixture(tmp_path, "clf")
    preprocessor = build_preprocessor(contract, cfg, train)
    preprocessor.fit(select_features(train, contract))
    before = preprocessor.transform(select_features(test, contract))
    path = tmp_path / "models" / "preprocessor.pkl"
    save_preprocessor(preprocessor, path)
    after = load_preprocessor(path).transform(select_features(test, contract))
    np.testing.assert_allclose(before, after)


def test_load_preprocessor_missing_raises(tmp_path):
    """A missing preprocessor points the user at make train."""
    with pytest.raises(FileNotFoundError, match="make train"):
        load_preprocessor(tmp_path / "absent.pkl")
