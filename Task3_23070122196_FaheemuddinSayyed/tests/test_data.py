"""Tests for raw loading, train/test validation, and CV splitter selection."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import make_config
from sklearn.model_selection import KFold, StratifiedKFold

from src.contract import derive_contract
from src.data import get_cv_splitter, load_raw, validate


def _clf_frames(tmp_path):
    """Return (cfg, train, test, contract) for the binary fixture."""
    cfg = make_config(tmp_path, "clf")
    train, test, sample_sub = load_raw(cfg)
    return cfg, train, test, derive_contract(train, sample_sub, cfg)


def test_load_raw_shapes(tmp_path):
    """The committed fixture shapes are what every later phase assumes."""
    cfg = make_config(tmp_path, "clf")
    train, test, sample_sub = load_raw(cfg)
    assert train.shape == (60, 8)
    assert test.shape == (20, 7)
    assert sample_sub.shape == (20, 2)


def test_missing_file_raises_actionable_error(tmp_path):
    """A missing raw file names the file, the canonical directory, and the download URL."""
    cfg = make_config(tmp_path, "clf", paths={"raw_dir": str(tmp_path / "empty")})
    with pytest.raises(FileNotFoundError) as excinfo:
        load_raw(cfg)
    message = str(excinfo.value)
    assert "train.csv" in message
    assert "data/raw" in message
    assert "playground-series-s6e8" in message


def test_validate_accepts_clf_fixture(tmp_path):
    """A well-formed classification fixture passes validation."""
    _, train, test, contract = _clf_frames(tmp_path)
    assert validate(train, test, contract) is None


def test_validate_accepts_reg_fixture(tmp_path):
    """A well-formed regression fixture passes validation."""
    cfg = make_config(tmp_path, "reg")
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert validate(train, test, contract) is None


def test_validate_catches_missing_target(tmp_path):
    """Dropping the target from train is reported by name."""
    _, train, test, contract = _clf_frames(tmp_path)
    with pytest.raises(ValueError, match="target"):
        validate(train.drop(columns=["target"]), test, contract)


def test_validate_catches_target_leak_into_test(tmp_path):
    """A target column present in test aborts before any training happens."""
    _, train, test, contract = _clf_frames(tmp_path)
    leaked = test.copy()
    leaked["target"] = 0
    with pytest.raises(ValueError, match="test.csv"):
        validate(train, leaked, contract)


def test_validate_catches_column_mismatch(tmp_path):
    """A feature present in train but not test is named in the error."""
    _, train, test, contract = _clf_frames(tmp_path)
    with pytest.raises(ValueError, match="n2"):
        validate(train, test.drop(columns=["n2"]), contract)


def test_validate_catches_duplicate_ids(tmp_path):
    """A repeated ID value in train is counted and reported."""
    _, train, test, contract = _clf_frames(tmp_path)
    duped = train.copy()
    duped.loc[1, "id"] = duped.loc[0, "id"]
    with pytest.raises(ValueError, match="duplicate"):
        validate(duped, test, contract)


def test_splitter_is_stratified_for_classification(tmp_path):
    """Classification gets StratifiedKFold, seeded and with the configured split count."""
    cfg, _, _, contract = _clf_frames(tmp_path)
    splitter = get_cv_splitter(cfg, contract)
    assert isinstance(splitter, StratifiedKFold)
    assert splitter.n_splits == 2
    assert splitter.random_state == 42


def test_splitter_is_kfold_for_regression(tmp_path):
    """Regression gets a plain KFold, never a stratified one."""
    cfg = make_config(tmp_path, "reg")
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    splitter = get_cv_splitter(cfg, contract)
    assert isinstance(splitter, KFold)
    assert not isinstance(splitter, StratifiedKFold)


def test_splitter_unseeded_when_shuffle_disabled(tmp_path):
    """With shuffle off the splitter must carry no seed, or scikit-learn rejects it."""
    cfg = make_config(tmp_path, "clf", cv={"shuffle": False})
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    splitter = get_cv_splitter(cfg, contract)
    assert splitter.random_state is None
    assert splitter.shuffle is False


def test_splitter_is_reproducible(tmp_path):
    """Two splitters built from one config yield identical fold indices."""
    cfg, train, _, contract = _clf_frames(tmp_path)
    features = train[contract.feature_columns]
    target = train[contract.target_column]
    first = list(get_cv_splitter(cfg, contract).split(features, target))
    second = list(get_cv_splitter(cfg, contract).split(features, target))
    assert len(first) == 2
    for (train_a, val_a), (train_b, val_b) in zip(first, second, strict=True):
        assert np.array_equal(train_a, train_b)
        assert np.array_equal(val_a, val_b)
