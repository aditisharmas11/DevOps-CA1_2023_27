"""Derive, persist, and describe the dataset's column contract."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ensure_dirs
from src.data import load_raw

LOGGER = logging.getLogger(__name__)

MAX_CLASSIFICATION_CARDINALITY = 20
COMPETITION_DATA_URL = "https://www.kaggle.com/competitions/playground-series-s6e8/data"

CONTRACT_FIELDS = (
    "id_column",
    "target_column",
    "task_type",
    "n_classes",
    "numeric_features",
    "categorical_features",
)

MANUAL_CHECKLIST = """\
## Manual checklist

Confirm each item against the competition page and tick it off by hand.

- [ ] Auto-detected contract matches the competition: ID, target, and binary
      classification.
- [ ] Train and test row counts and the feature count look right.
- [ ] Class balance is recorded below. No resampling is to be added — the metric is
      threshold-free.
- [ ] Missing-value counts per column are recorded below.
- [ ] The sample submission header matches the competition's stated submission format.
"""


@dataclass(frozen=True)
class DataContract:
    """Column roles and task type for one dataset."""

    id_column: str
    target_column: str
    task_type: str
    n_classes: int | None
    numeric_features: list[str]
    categorical_features: list[str]

    @property
    def feature_columns(self) -> list[str]:
        """Numeric then categorical features, in the order the preprocessor expects."""
        return [*self.numeric_features, *self.categorical_features]

    @property
    def is_classification(self) -> bool:
        """True when the task is classification of any arity."""
        return self.task_type == "classification"

    @property
    def is_binary(self) -> bool:
        """True when the task is two-class classification."""
        return self.is_classification and self.n_classes == 2


def _infer_task_type(target: pd.Series) -> tuple[str, int | None]:
    """Classification for non-numeric targets or numeric ones with few distinct values."""
    n_unique = int(target.nunique(dropna=True))
    if not pd.api.types.is_numeric_dtype(target) or n_unique <= MAX_CLASSIFICATION_CARDINALITY:
        return "classification", n_unique
    return "regression", None


def derive_contract(
    train: pd.DataFrame, sample_sub: pd.DataFrame, cfg: dict[str, Any]
) -> DataContract:
    """Derive column roles from the data, then let config overrides win (CLAUDE.md §5)."""
    if sample_sub.shape[1] < 2:
        raise ValueError(
            f"sample_submission.csv has {sample_sub.shape[1]} column(s); expected at least 2 "
            f"(an ID column then a target column). The file looks wrong — re-download it from "
            f"{COMPETITION_DATA_URL}."
        )
    overrides = cfg["contract"]
    id_column = overrides.get("id_column") or sample_sub.columns[0]
    target_column = overrides.get("target_column") or sample_sub.columns[1]
    for role, column in (
        ("contract.id_column", id_column),
        ("contract.target_column", target_column),
    ):
        if column not in train.columns:
            raise ValueError(
                f"Column '{column}' ({role}) is not in train.csv. "
                f"Columns present: {list(train.columns)}."
            )

    task_type, n_classes = _infer_task_type(train[target_column])
    override_task = overrides.get("task_type")
    if override_task and override_task != task_type:
        task_type = override_task
        n_classes = int(train[target_column].nunique()) if task_type == "classification" else None

    dropped = set(overrides.get("drop_columns") or [])
    feature_names = [
        column
        for column in train.columns
        if column not in {id_column, target_column} and column not in dropped
    ]
    numeric = [column for column in feature_names if pd.api.types.is_numeric_dtype(train[column])]
    categorical = [column for column in feature_names if column not in set(numeric)]
    return DataContract(
        id_column=str(id_column),
        target_column=str(target_column),
        task_type=task_type,
        n_classes=n_classes,
        numeric_features=numeric,
        categorical_features=categorical,
    )


def contract_to_dict(contract: DataContract) -> dict[str, Any]:
    """Return the contract's six fields as plain JSON-serialisable types."""
    return {
        "id_column": str(contract.id_column),
        "target_column": str(contract.target_column),
        "task_type": str(contract.task_type),
        "n_classes": None if contract.n_classes is None else int(contract.n_classes),
        "numeric_features": [str(column) for column in contract.numeric_features],
        "categorical_features": [str(column) for column in contract.categorical_features],
    }


def contract_from_dict(payload: dict[str, Any]) -> DataContract:
    """Rebuild a DataContract from contract_to_dict output."""
    for key in CONTRACT_FIELDS:
        if key not in payload:
            raise ValueError(f"Contract JSON is missing key '{key}'.")
    return DataContract(
        id_column=payload["id_column"],
        target_column=payload["target_column"],
        task_type=payload["task_type"],
        n_classes=payload["n_classes"],
        numeric_features=list(payload["numeric_features"]),
        categorical_features=list(payload["categorical_features"]),
    )


def _plain(value: Any) -> Any:
    """Convert a numpy scalar to the closest built-in type; pass anything else through."""
    return value.item() if hasattr(value, "item") else value


def save_contract(
    contract: DataContract, path: Path, label_classes: list[Any] | None = None
) -> None:
    """Write the contract plus its optional label classes to a JSON file."""
    payload = contract_to_dict(contract)
    payload["label_classes"] = (
        None if label_classes is None else [_plain(value) for value in label_classes]
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_contract(path: Path) -> tuple[DataContract, list[Any] | None]:
    """Read back a contract JSON written by save_contract."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run `make train` first.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return contract_from_dict(payload), payload.get("label_classes")


def _table(header: list[str], rows: list[list[str]]) -> str:
    """Render rows as a GitHub-flavoured markdown pipe table."""
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _contract_section(contract: DataContract) -> str:
    """Render the detected contract as a property table."""
    rows = [
        ["ID column", f"`{contract.id_column}`"],
        ["Target column", f"`{contract.target_column}`"],
        ["Task type", contract.task_type],
        ["Classes", "—" if contract.n_classes is None else str(contract.n_classes)],
        ["Features", str(len(contract.feature_columns))],
        ["Numeric features", str(len(contract.numeric_features))],
        ["Categorical features", str(len(contract.categorical_features))],
    ]
    return "## Detected contract\n\n" + _table(["Property", "Value"], rows)


def _shapes_section(
    train: pd.DataFrame, test: pd.DataFrame, sample_sub: pd.DataFrame | None
) -> str:
    """Render row and column counts for each input file."""
    rows = [
        ["train.csv", f"{len(train):,}", str(train.shape[1])],
        ["test.csv", f"{len(test):,}", str(test.shape[1])],
    ]
    if sample_sub is not None:
        rows.append(["sample_submission.csv", f"{len(sample_sub):,}", str(sample_sub.shape[1])])
    section = "## Shapes\n\n" + _table(["File", "Rows", "Columns"], rows)
    if sample_sub is not None:
        header = ",".join(str(column) for column in sample_sub.columns)
        section += f"\n\nSample submission header: `{header}`"
    return section


def _role(column: str, contract: DataContract) -> str:
    """Name the role the contract assigns to one column."""
    if column == contract.id_column:
        return "ID"
    if column == contract.target_column:
        return "target"
    if column in contract.numeric_features:
        return "numeric"
    if column in contract.categorical_features:
        return "categorical"
    return "dropped"


def _columns_section(contract: DataContract, train: pd.DataFrame, test: pd.DataFrame) -> str:
    """Render a per-column table of role, dtype, and null counts."""
    train_nulls = train.isna().sum()
    test_nulls = test.isna().sum()
    rows = [
        [
            f"`{column}`",
            _role(column, contract),
            str(train[column].dtype),
            f"{int(train_nulls[column]):,}",
            f"{int(test_nulls[column]):,}" if column in test.columns else "—",
        ]
        for column in train.columns
    ]
    header = ["Column", "Role", "dtype", "Nulls (train)", "Nulls (test)"]
    return "## Columns\n\n" + _table(header, rows)


def _target_section(contract: DataContract, train: pd.DataFrame) -> str:
    """Render the target distribution: value counts for classification, describe() otherwise."""
    target = train[contract.target_column]
    if not contract.is_classification:
        stats = target.describe()
        rows = [[f"`{name}`", f"{float(value):.4f}"] for name, value in stats.items()]
        return "## Target distribution\n\n" + _table(["Statistic", "Value"], rows)
    counts = target.value_counts(dropna=False).sort_index()
    total = int(counts.sum())
    rows = [
        [f"`{value}`", f"{int(count):,}", f"{100.0 * int(count) / total:.2f} %"]
        for value, count in counts.items()
    ]
    section = "## Target distribution\n\n" + _table(["Class", "Count", "Share"], rows)
    if len(counts) == 2:
        share = 100.0 * int(counts.iloc[-1]) / total
        section += (
            f"\n\nMajority share {max(share, 100.0 - share):.2f} %. Recorded only — no "
            f"resampling or class weighting is applied, because the evaluation metric is "
            f"threshold-free."
        )
    return section


def _missing_section(train: pd.DataFrame) -> str:
    """Render non-zero null counts per training column, highest first."""
    nulls = train.isna().sum()
    nulls = nulls[nulls > 0].sort_values(ascending=False)
    if nulls.empty:
        return "## Missing values\n\nNo missing values."
    total = len(train)
    rows = [
        [f"`{column}`", f"{int(count):,}", f"{100.0 * int(count) / total:.2f} %"]
        for column, count in nulls.items()
    ]
    return "## Missing values\n\n" + _table(["Column", "Nulls", "Share"], rows)


def contract_to_markdown(
    contract: DataContract,
    train: pd.DataFrame,
    test: pd.DataFrame,
    sample_sub: pd.DataFrame | None = None,
) -> str:
    """Render a human-readable report of the contract and the data behind it."""
    sections = [
        "# Data contract",
        "Generated by `make inspect`. Do not edit by hand — re-run the command instead.",
        MANUAL_CHECKLIST.strip(),
        _contract_section(contract),
        _shapes_section(train, test, sample_sub),
        _columns_section(contract, train, test),
        _target_section(contract, train),
        _missing_section(train),
    ]
    return "\n\n".join(section.strip() for section in sections) + "\n"


def run_inspect(cfg: dict[str, Any]) -> Path:
    """Derive the contract from the raw data and write reports/data_contract.md."""
    ensure_dirs(cfg)
    train, test, sample_sub = load_raw(cfg)
    contract = derive_contract(train, sample_sub, cfg)
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
    report_path = Path(cfg["paths"]["reports_dir"]) / "data_contract.md"
    report_path.write_text(
        contract_to_markdown(contract, train, test, sample_sub), encoding="utf-8"
    )
    LOGGER.info("wrote %s", report_path)
    return report_path
