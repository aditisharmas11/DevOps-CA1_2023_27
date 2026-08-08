# Phase 02 — Data contract and loading

## Objective

Teach the pipeline to read `data/raw/`, derive the ID / target / task-type contract from
the data itself, validate that train and test agree, and write
`reports/data_contract.md`. Also create the committed test fixtures and the first two
test files, so every later phase has a green test suite to protect it. This is the phase
where the plan's assumptions meet the real CSVs.

> **This phase has a hard stop condition.** If the auto-detected contract is not
> `id` / `addicted_label` / binary classification with 2 classes, do not work around it.
> Stop and report what was found.

## Preconditions

Phase 01 is complete and committed. Specifically:

- `.venv/` on Python 3.11 with `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `pyyaml`,
  `matplotlib`, `joblib`, `pytest`, `ruff` installed.
- `config/default.yaml` complete, with all nine required top-level keys including
  `runtime`.
- `src/__init__.py` and `src/config.py`, the latter exporting `PROJECT_ROOT`,
  `REQUIRED_TOP_LEVEL_KEYS`, `OUTPUT_DIR_KEYS`, `load_config`, `validate_config`,
  `resolve_paths`, `ensure_dirs`.
- `Makefile` with all targets; `make inspect` already runs
  `$(PY) -m src.cli inspect --config config/default.yaml`. **Do not edit the Makefile.**
- `pyproject.toml`, `requirements.txt`, `.gitignore`, `README.md` skeleton.
- Directories `config/ src/ scripts/ tests/fixtures/ data/raw/ data/processed/ models/
  reports/figures/ submissions/ .github/workflows/` all exist.
- `data/raw/{train,test,sample_submission}.csv` present and gitignored.
- `make lint` passes. There are no test files yet.

## Context recap

### The schema-discovery rule (CLAUDE.md §5) — verbatim consequences

The contract is known and written into `config/default.yaml`, but **do not hardcode the
strings `"id"` or `"addicted_label"` anywhere in `src/`.** The code derives the contract
at runtime and treats config as an override. The derivation:

1. Read `data/raw/sample_submission.csv`.
2. Column 0 → the **ID column** name.
3. Column 1 → the **target column** name.
4. Inspect `data/raw/train.csv[target]`:
   - non-numeric dtype, or numeric with `nunique <= 20` → **classification**
     (binary if `nunique == 2`, else multiclass)
   - otherwise → **regression**
5. Everything in `train.csv` except ID and target → features. Split into numeric vs
   categorical by dtype.

The user may override any of these in `config/default.yaml`. **Config always wins over
auto-detection.**

If `data/raw/` is empty, code must fail with a clear, actionable message telling the user
which files to download and where to put them — never with a traceback and never by
fabricating data.

### Relevant config keys

```yaml
paths:
  raw_dir: data/raw
  reports_dir: reports
  train_file: train.csv
  test_file: test.csv
  sample_submission_file: sample_submission.csv

contract:
  id_column: id
  target_column: addicted_label
  task_type: classification
  drop_columns: []

project:
  seed: 42

cv:
  n_splits: 5
  shuffle: true
```

Remember from phase 01: only `paths.*_dir` values are `Path` objects. `paths.train_file`
and friends are plain filename strings, joined against `raw_dir` by the consumer.
`ensure_dirs` deliberately does **not** create `raw_dir`.

### `src/contract.py` specification (Implementation Plan §3.2)

- `@dataclass DataContract`: `id_column: str`, `target_column: str`, `task_type: str`,
  `n_classes: int | None`, `numeric_features: list[str]`, `categorical_features:
  list[str]`.
- `derive_contract(train, sample_sub, cfg) -> DataContract` implementing CLAUDE.md §5
  with config overrides applied last.
- `contract_to_markdown(contract, train, test) -> str` — shapes, dtypes table, target
  distribution (value counts for classification, `describe()` for regression),
  missing-value counts per column.
- Guard: if `sample_submission.csv` has fewer than 2 columns, raise `ValueError`
  explaining the file looks wrong.

### `src/data.py` specification (Implementation Plan §3.3)

- `load_raw(cfg) -> tuple[DataFrame, DataFrame, DataFrame]` returning
  `(train, test, sample_submission)`.
- Before reading, check each file exists. If any is missing, raise `FileNotFoundError`
  with **this exact style of message**:
  ```
  Missing data/raw/train.csv.
  Download the competition data from
  https://www.kaggle.com/competitions/playground-series-s6e8/data
  and place train.csv, test.csv and sample_submission.csv in data/raw/.
  ```
- `validate(train, test, contract) -> None` — assert the target exists in train and is
  absent from test; assert the feature sets match between train and test; assert the ID
  column is unique in both. Raise `ValueError` describing the mismatch.
- `get_cv_splitter(cfg, contract)` → `StratifiedKFold` for classification, `KFold` for
  regression, both seeded from `project.seed`.

### `scripts/inspect_data.py` specification (Implementation Plan §3.10)

Thin wrapper: load data, derive contract, write `reports/data_contract.md` via
`contract_to_markdown`, print the path. The generated markdown also carries a **manual
checklist** at the top listing the five items from CLAUDE.md §10 for the student to tick
off by hand.

### `src/cli.py` specification (Implementation Plan §3.9, CLAUDE.md §7a)

- `argparse` with subcommands `inspect`, `train`, `predict`, each taking `--config`
  (default `config/default.yaml`) and `--log-level` (default `INFO`).
- Configures `logging.basicConfig` **once**, with format
  `%(asctime)s %(levelname)-8s %(name)s: %(message)s` and `datefmt="%H:%M:%S"`.
- Exit code 0 on success, 1 on a handled error — log the message, no traceback.

**This phase creates `src/cli.py` with the `inspect` subcommand only.** Phase 04 adds
`train`, phase 05 adds `predict`. Registering a subcommand whose handler does not exist
yet is a forward dependency and is not allowed.

### The five things to confirm (CLAUDE.md §10)

Record in `reports/data_contract.md`:

1. Auto-detected contract equals `id` / `addicted_label` / binary classification. **If it
   does not, stop and report** — something is wrong with the download.
2. Row counts of train and test; feature count; numeric vs categorical split.
3. Class balance of `addicted_label`. If heavily imbalanced, note it — but do **not** add
   resampling or `scale_pos_weight` without instruction. ROC AUC is threshold-free.
4. Missing-value counts per column.
5. Whether `sample_submission.csv` header is exactly `id,addicted_label`.

### Already-measured ground truth for the real files

These were read off the actual downloaded CSVs. Use them to cross-check; if what you
observe differs, that is the stop condition.

| Property | Expected value |
|---|---|
| `train.csv` | 691,369 rows × 14 columns, 43 MB |
| `test.csv` | 296,302 rows × 13 columns, 18 MB |
| `sample_submission.csv` | 296,302 rows × 2 columns, header exactly `id,addicted_label` |
| Feature count | 12 — 9 numeric, 3 categorical |
| Numeric features | `age`, `daily_screen_time_hours`, `social_media_hours`, `gaming_hours`, `work_study_hours`, `sleep_hours`, `notifications_per_day`, `app_opens_per_day`, `weekend_screen_time` |
| Categorical features | `gender`, `stress_level`, `academic_work_impact` |
| Target | `addicted_label`, integer, 2 distinct values |
| Class balance | 490,474 positive / 200,895 negative — 70.9 % positive |
| Missing values | present across the numeric columns |
| `id` ranges | train 0–691,368; test 691,369–987,670 |
| `sample_submission` target column | constant 0.7094243450313797 — exactly the positive base rate, confirming the column is a probability |

The 70.9 % / 29.1 % split is mild imbalance. **Do not add resampling, SMOTE, or
`scale_pos_weight`** (Implementation Plan §9). Note it in the report and move on.

### Test fixture specification (Implementation Plan §4.1)

Two fixture sets under `tests/fixtures/`, tiny (~60 train rows, ~20 test rows, 4 numeric
+ 2 categorical features, some deliberate NaNs), generated by a seeded script and
committed:

- `clf/` — binary target named `target`, ID column `id`
- `reg/` — continuous target named `score`, ID column `row_id`

Each set has `train.csv`, `test.csv`, `sample_submission.csv`. All tests must pass with
**no real competition data present**.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `src/contract.py` | create | `DataContract`, derivation, JSON round-trip, markdown report, `run_inspect`. |
| `src/data.py` | create | Raw loading with actionable errors, validation, CV splitter. |
| `src/cli.py` | create | argparse dispatch and logging setup; `inspect` subcommand only. |
| `scripts/inspect_data.py` | create | Standalone wrapper around `run_inspect`. |
| `tests/fixtures/make_fixtures.py` | create | Seeded, deterministic fixture generator. |
| `tests/fixtures/clf/{train,test,sample_submission}.csv` | create | Binary-classification fixture set. |
| `tests/fixtures/reg/{train,test,sample_submission}.csv` | create | Regression fixture set. |
| `tests/conftest.py` | create | `make_config()` helper building fixture-backed configs. |
| `tests/test_contract.py` | create | Contract derivation, overrides, guards, round-trip. |
| `tests/test_data.py` | create | Loading errors, validation, splitter selection. |
| `reports/data_contract.md` | create (generated) | Output of `make inspect`. |

## Detailed steps

### 1. Write `src/contract.py`

```python
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
```

Then these functions:

**`_infer_task_type(target: pd.Series) -> tuple[str, int | None]`**

```python
n_unique = int(target.nunique(dropna=True))
if not pd.api.types.is_numeric_dtype(target) or n_unique <= MAX_CLASSIFICATION_CARDINALITY:
    return "classification", n_unique
return "regression", None
```

**`derive_contract(train: pd.DataFrame, sample_sub: pd.DataFrame, cfg: dict) -> DataContract`**

In order:

1. If `sample_sub.shape[1] < 2`, raise:
   ```python
   raise ValueError(
       f"sample_submission.csv has {sample_sub.shape[1]} column(s); expected at least 2 "
       f"(an ID column then a target column). The file looks wrong — re-download it from "
       f"{COMPETITION_DATA_URL}."
   )
   ```
2. `overrides = cfg["contract"]`;
   `id_column = overrides.get("id_column") or sample_sub.columns[0]`;
   `target_column = overrides.get("target_column") or sample_sub.columns[1]`.
   Using `or` means an explicit `null` in YAML falls back to auto-detection, which is
   exactly what the config comment promises.
3. For each of `id_column` and `target_column`, if it is not in `train.columns`, raise
   `ValueError(f"Column '{column}' ({role}) is not in train.csv. Columns present: {list(train.columns)}.")`
   where `role` is `"contract.id_column"` or `"contract.target_column"`.
4. `task_type, n_classes = _infer_task_type(train[target_column])`. Then apply the
   override:
   ```python
   override_task = overrides.get("task_type")
   if override_task and override_task != task_type:
       task_type = override_task
       n_classes = int(train[target_column].nunique()) if task_type == "classification" else None
   ```
5. Features: everything in `train.columns` that is not the ID, not the target, and not
   in `overrides.get("drop_columns") or []`. Split with
   `pd.api.types.is_numeric_dtype(train[column])` — numeric goes to `numeric_features`,
   everything else to `categorical_features`. Preserve the column order from
   `train.columns` within each group.
6. Return the `DataContract`.

**`contract_to_dict(contract) -> dict[str, Any]`** — the six fields as plain JSON types.

**`contract_from_dict(payload: dict) -> DataContract`** — inverse; raise
`ValueError(f"Contract JSON is missing key '{key}'.")` for any missing field.

**`save_contract(contract, path: Path, label_classes: list | None = None) -> None`** —
writes `contract_to_dict(contract)` plus a `"label_classes"` key, JSON, `indent=2`.
Convert numpy scalars to Python ints/floats/strs first — `json.dump` cannot serialise
`numpy.int64`, and phase 04 will hand this function a `LabelEncoder.classes_` array.

**`load_contract(path: Path) -> tuple[DataContract, list | None]`** — reads it back. If
the file is absent, raise
``FileNotFoundError(f"Missing {path}. Run `make train` first.")``.

**`contract_to_markdown(contract, train, test) -> str`** — assemble from small private
helpers so no function exceeds ~40 lines (CLAUDE.md §7). Sections, in order:

1. `# Data contract` heading and a generated-by note.
2. `MANUAL_CHECKLIST`.
3. `## Detected contract` — a table of ID column, target column, task type, `n_classes`,
   feature count, numeric count, categorical count.
4. `## Shapes` — train and test rows × columns, and the sample submission row count.
5. `## Columns` — a table of column | role (id / target / numeric / categorical) | dtype |
   nulls in train | nulls in test (`—` where the column is absent from test).
6. `## Target distribution` — for classification, `train[target].value_counts()` with
   counts and percentages; for regression, `train[target].describe()`.
7. `## Missing values` — per-column null counts for train, highest first, omitting zeros;
   if there are none, state "No missing values."

Render tables as GitHub-flavoured markdown pipe tables. Keep it deterministic: no
timestamps, no absolute paths — the file is committed in phase 07 and a churning diff is
noise.

**`run_inspect(cfg: dict) -> Path`**

```python
def run_inspect(cfg: dict[str, Any]) -> Path:
    """Derive the contract from data/raw and write reports/data_contract.md."""
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
    report_path.write_text(contract_to_markdown(contract, train, test), encoding="utf-8")
    LOGGER.info("wrote %s", report_path)
    return report_path
```

**Import direction matters.** `src/contract.py` imports `load_raw` from `src/data.py` at
module level. `src/data.py` must therefore **not** import `src/contract.py` at runtime —
it needs `DataContract` only for type hints, so it uses
`from typing import TYPE_CHECKING` plus `from __future__ import annotations`. Reversing
this creates a circular import.

### 2. Write `src/data.py`

```python
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
```

Note the message keeps the literal string `data/raw/` in its instruction block even when
`raw_dir` points elsewhere. That is intentional: the first line names the real resolved
path, and the instruction block always tells the user about the canonical location. The
test asserts on both.

**`validate(train, test, contract) -> None`** — raise `ValueError` on the first problem
found, in this order:

1. Target missing from train:
   `f"Target column '{contract.target_column}' is missing from train.csv."`
2. Target present in test:
   `f"Target column '{contract.target_column}' must not be present in test.csv."`
3. Feature sets differ. Compute
   `train_features = set(train.columns) - {id_column, target_column}` and
   `test_features = set(test.columns) - {id_column}`. If unequal:
   `f"train.csv and test.csv feature sets differ. Only in train: {only_train}. Only in test: {only_test}."`
   with both lists sorted.
4. Any contract feature missing from test:
   `f"Contract features missing from test.csv: {sorted(missing)}."`
5. Duplicate IDs, checked in train then test:
   `f"ID column '{contract.id_column}' has {n} duplicate value(s) in {filename}."`

**`get_cv_splitter(cfg, contract)`**

```python
def get_cv_splitter(cfg: dict[str, Any], contract: DataContract) -> KFold | StratifiedKFold:
    """StratifiedKFold for classification, KFold for regression, seeded from config."""
    shuffle = bool(cfg["cv"]["shuffle"])
    splitter_cls = StratifiedKFold if contract.is_classification else KFold
    return splitter_cls(
        n_splits=int(cfg["cv"]["n_splits"]),
        shuffle=shuffle,
        random_state=int(cfg["project"]["seed"]) if shuffle else None,
    )
```

`random_state` must be `None` when `shuffle` is false — scikit-learn raises otherwise.

### 3. Write `src/cli.py`

```python
"""Command-line entrypoint: python -m src.cli <inspect|train|predict>."""

from __future__ import annotations

import argparse
import logging
import sys

from src.config import load_config
from src.contract import run_inspect

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"
DEFAULT_CONFIG = "config/default.yaml"

LOGGER = logging.getLogger("src.cli")


def configure_logging(level: str) -> None:
    """Configure root logging once, with timestamps (CLAUDE.md §7a)."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with one subcommand per pipeline stage."""
    parser = argparse.ArgumentParser(prog="python -m src.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("inspect", "derive the data contract and write a report"),):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--config", default=DEFAULT_CONFIG, help="path to a YAML config")
        sub.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch a subcommand; return 0 on success, 1 on a handled error."""
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    try:
        cfg = load_config(args.config)
        if args.command == "inspect":
            run_inspect(cfg)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`stream=sys.stdout` and `force=True` matter: stdout so `make train | tee` works, and
`force=True` so a second `configure_logging` call in a test session actually takes
effect. The `for name, help_text in (...)` loop over a one-element tuple looks odd now
but is what phases 04 and 05 extend — they add tuple entries, not new blocks.

### 4. Write `scripts/inspect_data.py`

Run as `PYTHONPATH=. .venv/bin/python scripts/inspect_data.py`. `print()` is allowed
here (CLAUDE.md §7).

```python
"""Write reports/data_contract.md from the CSVs in data/raw/."""

from __future__ import annotations

import argparse
import sys

from src.cli import configure_logging
from src.config import load_config
from src.contract import run_inspect


def main() -> int:
    """Derive the data contract and print the path of the report written."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    configure_logging(args.log_level)
    try:
        report_path = run_inspect(load_config(args.config))
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 5. Write `tests/fixtures/make_fixtures.py` and generate the fixtures

Complete contents:

```python
"""Generate the tiny committed CSV fixtures used by the test suite.

Run from the repo root:
    PYTHONPATH=. .venv/bin/python tests/fixtures/make_fixtures.py

Regeneration is deterministic. The committed CSVs are the fixture contract — if a change
here alters them, review the diff.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).resolve().parent
N_TRAIN = 60
N_TEST = 20
SEED = 7
HIGH_CARD_LEVELS = [f"L{index:02d}" for index in range(18)]


def _features(rng: np.random.Generator, n: int) -> pd.DataFrame:
    """Build the shared 4-numeric / 2-categorical feature frame."""
    return pd.DataFrame(
        {
            "n1": rng.normal(0.0, 1.0, n).round(3),
            "n2": rng.normal(5.0, 2.0, n).round(3),
            "n3": rng.integers(0, 50, n).astype(float),
            "n4": rng.uniform(0.0, 1.0, n).round(3),
            "c1": rng.choice(["a", "b", "c"], n),
            "c2": [HIGH_CARD_LEVELS[i % len(HIGH_CARD_LEVELS)] for i in range(n)],
        }
    )


def _inject_nans(frame: pd.DataFrame) -> pd.DataFrame:
    """Put NaNs at fixed positions so imputation is always exercised."""
    frame = frame.copy()
    frame.loc[frame.index[0:3], "n1"] = np.nan
    frame.loc[frame.index[4:6], "n2"] = np.nan
    frame.loc[frame.index[7], "c1"] = np.nan
    return frame


def _signal(frame: pd.DataFrame) -> pd.Series:
    """A learnable function of the features, so trees find splits on tiny data."""
    return (
        1.8 * frame["n1"].fillna(0.0)
        - 0.9 * (frame["n2"].fillna(5.0) - 5.0)
        + 0.7 * (frame["c1"] == "a").astype(float)
        + 0.02 * frame["n3"]
    )


def _write(directory: Path, frames: dict[str, pd.DataFrame]) -> None:
    """Write each frame as <name>.csv into directory."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(directory / f"{name}.csv", index=False)


def build_clf() -> None:
    """Binary-classification fixture: ID `id`, target `target`."""
    rng = np.random.default_rng(SEED)
    train = _inject_nans(_features(rng, N_TRAIN))
    test = _inject_nans(_features(rng, N_TEST))
    test.loc[test.index[0], "c1"] = "z"
    score = _signal(train)
    train.insert(0, "id", range(N_TRAIN))
    train["target"] = (score > score.median()).astype(int).to_numpy()
    test.insert(0, "id", range(100, 100 + N_TEST))
    submission = pd.DataFrame({"id": test["id"].to_numpy(), "target": 0.5})
    _write(FIXTURES_DIR / "clf", {"train": train, "test": test, "sample_submission": submission})


def build_reg() -> None:
    """Regression fixture: ID `row_id`, target `score`."""
    rng = np.random.default_rng(SEED + 1)
    train = _inject_nans(_features(rng, N_TRAIN))
    test = _inject_nans(_features(rng, N_TEST))
    test.loc[test.index[0], "c1"] = "z"
    values = (_signal(train) + rng.normal(0.0, 0.5, N_TRAIN)).round(4)
    train.insert(0, "row_id", range(N_TRAIN))
    train["score"] = values.to_numpy()
    test.insert(0, "row_id", range(100, 100 + N_TEST))
    submission = pd.DataFrame({"row_id": test["row_id"].to_numpy(), "score": 0.0})
    _write(FIXTURES_DIR / "reg", {"train": train, "test": test, "sample_submission": submission})


if __name__ == "__main__":
    build_clf()
    build_reg()
    print(f"fixtures written to {FIXTURES_DIR}")
```

Four properties of this design that later phases depend on — do not lose them:

- **`c2` is assigned by cycling, not randomly.** All 18 levels are guaranteed present, so
  phase 03's one-hot high-cardinality fallback test (threshold 15) is deterministic. A
  random draw could yield only 15 distinct levels and make that test flaky.
- **`test.c1` row 0 is `"z"`**, a category unseen in train. Phase 03 asserts it encodes to
  `-1` rather than raising.
- **The target is a learnable function of the features.** Phase 06's smoke test asserts
  the submission column has more than two distinct values; a pure-noise target on 30 rows
  per fold could produce a constant prediction and fail that assertion for the wrong
  reason.
- **`score > score.median()`** over 60 distinct values gives exactly 30/30, so
  `StratifiedKFold(n_splits=2)` always works.

Run it, then confirm the fixtures are committable (they are not gitignored).

### 6. Write `tests/conftest.py`

```python
"""Shared pytest helpers: configs backed by the committed CSV fixtures."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from src.config import load_config

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "default.yaml"

TINY_MODELS = [
    {
        "name": "lightgbm",
        "enabled": True,
        "weight": 0.7,
        "early_stopping_rounds": None,
        "params": {
            "n_estimators": 30,
            "learning_rate": 0.2,
            "num_leaves": 7,
            "min_child_samples": 2,
            "verbose": -1,
        },
    },
    {
        "name": "hist_gbm",
        "enabled": True,
        "weight": 0.3,
        "early_stopping_rounds": None,
        "params": {
            "max_iter": 30,
            "learning_rate": 0.2,
            "max_leaf_nodes": 7,
            "min_samples_leaf": 2,
            "early_stopping": False,
            "verbose": 0,
        },
    },
]


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge updates into base, returning base."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def make_config(tmp_path: Path, fixture: str, **overrides: Any) -> dict[str, Any]:
    """Build a config pointing at tests/fixtures/<fixture> with tmp_path output dirs."""
    raw = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    cfg = copy.deepcopy(raw)
    cfg["paths"]["raw_dir"] = str(FIXTURES_DIR / fixture)
    cfg["contract"] = {
        "id_column": None,
        "target_column": None,
        "task_type": None,
        "drop_columns": [],
    }
    cfg["runtime"] = {"n_jobs": 1, "progress": False, "log_every_n_iterations": 0}
    cfg["cv"]["n_splits"] = 2
    cfg["metric"] = {"name": "auto", "greater_is_better": None}
    cfg["models"] = copy.deepcopy(TINY_MODELS)
    _deep_update(cfg, overrides)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return load_config(config_path, root=tmp_path)
```

Why this shape:

- `contract` values are `null` so auto-detection runs — the fixtures use `target` /
  `score`, not the real `addicted_label`, and the default config's explicit values would
  point at columns that do not exist.
- `raw_dir` is set to an **absolute** fixture path. `resolve_paths` does
  `Path(root) / value`, and joining an absolute path discards the left operand, so the
  fixture directory survives while every other `*_dir` lands under `tmp_path`.
- `runtime.progress` is false and `n_jobs` is 1: quiet, and single-threaded for
  determinism.
- `metric.name: auto` with `greater_is_better: null` exercises the auto-resolution path
  that phase 03 builds. Nothing in phase 02 reads these keys — they are here so phases
  03–06 do not have to touch `conftest.py`.
- `TINY_MODELS` sets `min_child_samples`/`min_samples_leaf` to 2 and drops `subsample`,
  so trees actually split on 30 rows per fold. `verbose: -1` / `0` keeps pytest output
  clean. Unused until phase 04.

### 7. Write `tests/test_contract.py`

Cover, one assertion-focused test each:

| Test | Asserts |
|---|---|
| `test_auto_detects_clf_contract` | For `clf`: `id_column == "id"`, `target_column == "target"`, `task_type == "classification"`, `n_classes == 2`, `is_binary`, `numeric_features == ["n1","n2","n3","n4"]`, `categorical_features == ["c1","c2"]`. |
| `test_auto_detects_reg_contract` | For `reg`: `id_column == "row_id"`, `target_column == "score"`, `task_type == "regression"`, `n_classes is None`, `not is_binary`. |
| `test_config_override_beats_autodetection` | With `contract={"target_column": "c1", ...}` on `clf`: `target_column == "c1"`, `task_type == "classification"`, `n_classes == 3`, and `"target"` now appears in `numeric_features`. |
| `test_task_type_override_forces_regression` | `contract={"task_type": "regression"}` on `clf`: `task_type == "regression"` and `n_classes is None`. |
| `test_drop_columns_are_excluded` | `contract={"drop_columns": ["n3"]}`: `"n3"` not in `feature_columns`, and the count drops by one. |
| `test_single_column_sample_submission_raises` | A one-column frame raises `ValueError` whose message contains `"expected at least 2"`. |
| `test_unknown_override_column_raises` | `contract={"target_column": "nope"}` raises `ValueError` mentioning `nope`. |
| `test_contract_json_roundtrip` | `save_contract` then `load_contract` returns an equal `DataContract` and the `label_classes` list passed in; passing `numpy.int64` classes serialises without error. |
| `test_markdown_report_has_all_sections` | `contract_to_markdown` output contains `"## Manual checklist"`, `"## Detected contract"`, `"## Shapes"`, `"## Columns"`, `"## Target distribution"`, `"## Missing values"`. |
| `test_markdown_report_is_deterministic` | Two calls with the same inputs return identical strings. |

Load fixture frames with `load_raw(make_config(tmp_path, "clf"))`.

### 8. Write `tests/test_data.py`

| Test | Asserts |
|---|---|
| `test_load_raw_shapes` | `clf`: train `(60, 8)`, test `(20, 7)`, sample submission `(20, 2)`. |
| `test_missing_file_raises_actionable_error` | With `raw_dir` pointed at an empty `tmp_path` subdirectory, `load_raw` raises `FileNotFoundError` whose message contains `"train.csv"`, `"data/raw"`, and the competition URL. |
| `test_validate_accepts_fixtures` | `validate` returns `None` for both fixture sets. |
| `test_validate_catches_missing_target` | Dropping the target from train raises `ValueError` mentioning the target name. |
| `test_validate_catches_target_leak_into_test` | Adding the target column to test raises `ValueError` mentioning `test.csv`. |
| `test_validate_catches_column_mismatch` | Dropping `n2` from test raises `ValueError` whose message contains `"n2"`. |
| `test_validate_catches_duplicate_ids` | Duplicating an ID in train raises `ValueError` mentioning the ID column and `train.csv`. |
| `test_splitter_is_stratified_for_classification` | `isinstance(get_cv_splitter(...), StratifiedKFold)`, `n_splits == 2`. |
| `test_splitter_is_kfold_for_regression` | `isinstance(..., KFold)` and **not** `StratifiedKFold`. |
| `test_splitter_unseeded_when_shuffle_disabled` | `cv={"shuffle": False}` gives `random_state is None` and constructing it does not raise. |
| `test_splitter_is_reproducible` | Two splitters built from the same config yield identical fold index arrays. |

`KFold` is a superclass concern: `StratifiedKFold` is not a subclass of `KFold`, so a
plain `isinstance` check is sufficient — but assert `not isinstance(splitter,
StratifiedKFold)` in the regression test anyway to make the intent explicit.

### 9. Format, lint, and run

```bash
make fmt
make lint
make test
```

### 10. Generate the real report and check the stop condition

```bash
make inspect
```

Then read `reports/data_contract.md` and compare against the ground-truth table in the
Context recap. **If the detected contract is not `id` / `addicted_label` /
`classification` with `n_classes == 2`, stop. Report what was detected and do not
continue to phase 03.**

## Verification

```bash
# 1. Lint clean.
make lint
# expect: exit 0, zero findings

# 2. Both test files pass, with no real data involved.
make test
# expect: all tests pass, 0 failures

# 3. Fixtures exist, are committable, and hold the invariants later phases rely on.
ls tests/fixtures/clf tests/fixtures/reg
# expect: sample_submission.csv  test.csv  train.csv  in each
git check-ignore -q tests/fixtures/clf/train.csv; echo "fixture ignored? exit=$?"
# expect: exit=1  (NOT ignored — fixtures must be committed)
.venv/bin/python -c "
import pandas as pd
tr = pd.read_csv('tests/fixtures/clf/train.csv')
te = pd.read_csv('tests/fixtures/clf/test.csv')
assert tr.shape == (60, 8), tr.shape
assert te.shape == (20, 7), te.shape
assert tr['target'].nunique() == 2, tr['target'].nunique()
assert sorted(tr['target'].value_counts().tolist()) == [30, 30]
assert tr['c2'].nunique() == 18, tr['c2'].nunique()
assert 'z' in set(te['c1']), 'unseen category missing from test fixture'
assert tr[['n1','n2','c1']].isna().sum().sum() > 0, 'no NaNs to impute'
rg = pd.read_csv('tests/fixtures/reg/train.csv')
assert rg['score'].nunique() > 20, rg['score'].nunique()
print('fixture invariants ok')
"
# expect: fixture invariants ok

# 4. Regeneration is deterministic — the committed CSVs must not change.
PYTHONPATH=. .venv/bin/python tests/fixtures/make_fixtures.py && git diff --stat tests/fixtures
# expect: the script prints its output path and git diff --stat shows NOTHING
#         (run this after committing the fixtures once, or compare checksums instead)

# 5. The real-data contract report is generated.
make inspect
ls -l reports/data_contract.md
# expect: file exists, non-empty

# 6. THE STOP CONDITION — the detected contract must match the competition.
.venv/bin/python -c "
from src.config import load_config
from src.contract import derive_contract
from src.data import load_raw, validate
cfg = load_config('config/default.yaml')
train, test, sub = load_raw(cfg)
c = derive_contract(train, sub, cfg)
validate(train, test, c)
print('id_column       :', c.id_column)
print('target_column   :', c.target_column)
print('task_type       :', c.task_type)
print('n_classes       :', c.n_classes)
print('is_binary       :', c.is_binary)
print('numeric   (%2d)  :' % len(c.numeric_features), c.numeric_features)
print('categorical (%d) :' % len(c.categorical_features), c.categorical_features)
print('train / test    :', train.shape, test.shape)
print('sample_sub hdr  :', list(sub.columns))
print('class balance   :')
print(train[c.target_column].value_counts().to_string())
assert c.id_column == 'id', c.id_column
assert c.target_column == 'addicted_label', c.target_column
assert c.task_type == 'classification', c.task_type
assert c.n_classes == 2, c.n_classes
assert len(c.numeric_features) == 9, len(c.numeric_features)
assert len(c.categorical_features) == 3, len(c.categorical_features)
assert list(sub.columns) == ['id', 'addicted_label'], list(sub.columns)
assert train.shape == (691369, 14), train.shape
assert test.shape == (296302, 13), test.shape
print()
print('CONTRACT CONFIRMED — matches the competition specification')
"
# expect: every value as in the ground-truth table, ending with CONTRACT CONFIRMED.
# If ANY assertion fails: STOP. Report what was detected. Do not start phase 03.

# 7. Auto-detection alone (config overrides nulled) reaches the same answer.
.venv/bin/python -c "
from src.config import load_config
from src.contract import derive_contract
from src.data import load_raw
cfg = load_config('config/default.yaml')
cfg['contract'] = {'id_column': None, 'target_column': None, 'task_type': None, 'drop_columns': []}
train, test, sub = load_raw(cfg)
c = derive_contract(train, sub, cfg)
assert (c.id_column, c.target_column, c.task_type, c.n_classes) == ('id', 'addicted_label', 'classification', 2)
print('auto-detection agrees with config:', c.id_column, c.target_column, c.task_type, c.n_classes)
"
# expect: auto-detection agrees with config: id addicted_label classification 2

# 8. The missing-data path is actionable, not a traceback.
.venv/bin/python -c "
from src.config import load_config
from src.data import load_raw
cfg = load_config('config/default.yaml')
cfg['paths']['raw_dir'] = cfg['paths']['raw_dir'] / 'does-not-exist'
try:
    load_raw(cfg)
except FileNotFoundError as exc:
    print(exc)
"
# expect the four-line message naming train.csv, the competition URL, and data/raw/

# 9. No hardcoded competition strings leaked into src/ (CLAUDE.md §5).
grep -rn "addicted_label" src/ || echo "OK: no 'addicted_label' literal in src/"
# expect: OK: no 'addicted_label' literal in src/
grep -rnE "[\"']id[\"']" src/ || echo "OK: no bare 'id' literal in src/"
# expect: OK — or, if it matches, every hit must be an unrelated dict key, not a column name

# 10. The Makefile was not modified.
git diff --stat Makefile
# expect: no output
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0; `tests/test_contract.py` and `tests/test_data.py` both run and
      pass with no file under `data/raw/` being read.
- [ ] `src/contract.py`, `src/data.py`, `src/cli.py`, `scripts/inspect_data.py` exist.
- [ ] `tests/conftest.py`, `tests/fixtures/make_fixtures.py`, and six fixture CSVs under
      `tests/fixtures/clf/` and `tests/fixtures/reg/` exist and are **not** gitignored.
- [ ] Fixture invariants hold: clf train `(60, 8)`, test `(20, 7)`, target `nunique == 2`
      split 30/30, `c2` has 18 distinct levels, `"z"` present in test `c1`, NaNs present;
      reg target `nunique > 20`.
- [ ] Re-running `make_fixtures.py` leaves `git diff tests/fixtures` empty.
- [ ] `make inspect` exits 0 and writes a non-empty `reports/data_contract.md` containing
      all six section headings plus the manual checklist.
- [ ] `derive_contract` on the real data returns `id` / `addicted_label` /
      `classification` / `n_classes == 2`, with 9 numeric and 3 categorical features.
- [ ] The same result is reached with all `contract` config values set to `null`.
- [ ] `validate(train, test, contract)` on the real data returns without raising.
- [ ] `load_raw` on a nonexistent `raw_dir` raises `FileNotFoundError` whose message
      names the missing filename, the competition URL, and `data/raw/` — and no traceback
      reaches the user through `python -m src.cli inspect`.
- [ ] `python -m src.cli inspect --config config/default.yaml` exits 0;
      `python -m src.cli inspect --config nope.yaml` exits 1 and prints one log line, no
      traceback.
- [ ] `grep -rn "addicted_label" src/` finds nothing.
- [ ] `git diff --stat Makefile` is empty.
- [ ] `src/features.py`, `src/models.py`, `src/metrics.py`, `src/train.py`,
      `src/predict.py`, `scripts/make_eda.py`, `Dockerfile`, `config/ci.yaml` were **not**
      created.

## Handoff notes

What phase 03 may assume exists:

- `src/contract.py` exporting `DataContract` (with `feature_columns`,
  `is_classification`, `is_binary` properties), `derive_contract`, `contract_to_dict`,
  `contract_from_dict`, `save_contract`, `load_contract`, `contract_to_markdown`,
  `run_inspect`, and the constants `MAX_CLASSIFICATION_CARDINALITY`,
  `COMPETITION_DATA_URL`, `MANUAL_CHECKLIST`.
- `src/data.py` exporting `raw_path`, `load_raw`, `validate`, `get_cv_splitter`.
- `src/cli.py` exporting `configure_logging`, `build_parser`, `main`, and the constants
  `LOG_FORMAT`, `DATE_FORMAT`, `DEFAULT_CONFIG`.
- `tests/conftest.py` exporting `FIXTURES_DIR`, `DEFAULT_CONFIG_PATH`, `TINY_MODELS`,
  `make_config`.
- Six committed fixture CSVs.
- A confirmed contract: `id` / `addicted_label` / binary classification, 9 numeric + 3
  categorical features.

Decisions later phases must stay consistent with:

1. **`contract.feature_columns` is numeric-then-categorical.** Phase 03's
   `ColumnTransformer` must use the same order, and phase 05 must select test columns the
   same way, or the persisted preprocessor will be fed columns in the wrong order.
2. **Import direction: `contract.py` imports `data.py`, never the reverse.** `data.py`
   type-hints `DataContract` under `TYPE_CHECKING` only. Phase 03 onward must not add a
   runtime `import src.contract` to `data.py`.
3. **`save_contract` / `load_contract` already carry `label_classes`.** Phase 04 persists
   the fitted `LabelEncoder.classes_` through this key; phase 05 reads it back for the
   `round_predictions_to_labels: true` branch. Do not invent a second artifact for it.
4. **`build_parser` iterates a tuple of subcommands.** Phases 04 and 05 add `("train",
   ...)` and `("predict", ...)` entries to that tuple and one `elif` in `main`. They do
   not restructure the parser.
5. **`configure_logging` uses `force=True` and `stream=sys.stdout`.** Phase 04's
   LightGBM logger routing depends on the root handler already being configured this way.
6. **`conftest.make_config` nulls the contract and sets `metric.name: auto`.** Phase 03's
   metric tests and phase 06's smoke tests are written against that; do not switch the
   fixtures to explicit contract values.
7. **The fixture CSVs are frozen.** Phases 03 and 06 assert on their exact contents
   (18 `c2` levels, the `"z"` category, 30/30 class split). Regenerating them with
   different constants breaks those tests.
8. **Mild class imbalance (70.9 % positive) is recorded and ignored.** No resampling, no
   `scale_pos_weight` (Implementation Plan §9).

Commit before moving on:

```bash
git add -A && git commit -m "phase 02: data contract, loading, and fixtures"
```
