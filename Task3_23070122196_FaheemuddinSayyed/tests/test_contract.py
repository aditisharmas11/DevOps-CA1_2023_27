"""Tests for contract derivation, config overrides, persistence, and the report."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from conftest import make_config

from src.contract import (
    DataContract,
    contract_from_dict,
    contract_to_dict,
    contract_to_markdown,
    derive_contract,
    load_contract,
    save_contract,
)
from src.data import load_raw


def test_auto_detects_clf_contract(tmp_path):
    """The binary fixture's ID, target, task type, and feature split are all detected."""
    cfg = make_config(tmp_path, "clf")
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert contract.id_column == "id"
    assert contract.target_column == "target"
    assert contract.task_type == "classification"
    assert contract.n_classes == 2
    assert contract.is_binary
    assert contract.numeric_features == ["n1", "n2", "n3", "n4"]
    assert contract.categorical_features == ["c1", "c2"]
    assert contract.feature_columns == ["n1", "n2", "n3", "n4", "c1", "c2"]


def test_auto_detects_reg_contract(tmp_path):
    """The regression fixture resolves to regression with no class count."""
    cfg = make_config(tmp_path, "reg")
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert contract.id_column == "row_id"
    assert contract.target_column == "score"
    assert contract.task_type == "regression"
    assert contract.n_classes is None
    assert not contract.is_binary
    assert not contract.is_classification


def test_config_override_beats_autodetection(tmp_path):
    """An explicit target_column wins over the name read from sample_submission.csv."""
    cfg = make_config(tmp_path, "clf", contract={"target_column": "c1"})
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert contract.target_column == "c1"
    assert contract.task_type == "classification"
    assert contract.n_classes == 3
    assert "target" in contract.numeric_features
    assert "c1" not in contract.feature_columns


def test_task_type_override_forces_regression(tmp_path):
    """Overriding task_type discards the detected class count."""
    cfg = make_config(tmp_path, "clf", contract={"task_type": "regression"})
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert contract.task_type == "regression"
    assert contract.n_classes is None


def test_drop_columns_are_excluded(tmp_path):
    """Columns named in drop_columns never become features."""
    cfg = make_config(tmp_path, "clf", contract={"drop_columns": ["n3"]})
    train, _, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    assert "n3" not in contract.feature_columns
    assert len(contract.feature_columns) == 5


def test_single_column_sample_submission_raises(tmp_path):
    """A sample submission with one column is rejected with an explanation."""
    cfg = make_config(tmp_path, "clf")
    train, _, _ = load_raw(cfg)
    with pytest.raises(ValueError, match="expected at least 2"):
        derive_contract(train, pd.DataFrame({"id": [1, 2, 3]}), cfg)


def test_unknown_override_column_raises(tmp_path):
    """An override naming a column absent from train fails loudly."""
    cfg = make_config(tmp_path, "clf", contract={"target_column": "nope"})
    train, _, sample_sub = load_raw(cfg)
    with pytest.raises(ValueError, match="nope"):
        derive_contract(train, sample_sub, cfg)


def test_contract_json_roundtrip(tmp_path):
    """save_contract then load_contract returns an equal contract and its label classes."""
    contract = DataContract("id", "target", "classification", 2, ["n1", "n2"], ["c1"])
    path = tmp_path / "contract.json"
    save_contract(contract, path, label_classes=[np.int64(0), np.int64(1)])
    loaded, classes = load_contract(path)
    assert loaded == contract
    assert classes == [0, 1]
    assert all(isinstance(value, int) for value in classes)


def test_contract_dict_roundtrip():
    """contract_to_dict and contract_from_dict are inverses."""
    contract = DataContract("row_id", "score", "regression", None, ["n1"], [])
    assert contract_from_dict(contract_to_dict(contract)) == contract


def test_contract_from_dict_missing_key_raises():
    """A truncated contract payload is rejected by name."""
    with pytest.raises(ValueError, match="n_classes"):
        contract_from_dict({"id_column": "id", "target_column": "t", "task_type": "regression"})


def test_load_contract_missing_raises(tmp_path):
    """A missing contract file points the user at make train."""
    with pytest.raises(FileNotFoundError, match="make train"):
        load_contract(tmp_path / "absent.json")


def test_markdown_report_has_all_sections(tmp_path):
    """The generated report carries the checklist and all five data sections."""
    cfg = make_config(tmp_path, "clf")
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    report = contract_to_markdown(contract, train, test, sample_sub)
    for heading in (
        "## Manual checklist",
        "## Detected contract",
        "## Shapes",
        "## Columns",
        "## Target distribution",
        "## Missing values",
    ):
        assert heading in report, heading


def test_markdown_report_is_deterministic(tmp_path):
    """Two renders of the same inputs are byte-identical, so the committed file is stable."""
    cfg = make_config(tmp_path, "clf")
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    first = contract_to_markdown(contract, train, test, sample_sub)
    second = contract_to_markdown(contract, train, test, sample_sub)
    assert first == second


def test_markdown_report_handles_regression(tmp_path):
    """The regression branch renders describe() instead of value counts."""
    cfg = make_config(tmp_path, "reg")
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
    report = contract_to_markdown(contract, train, test, sample_sub)
    assert "## Target distribution" in report
    assert "`mean`" in report
