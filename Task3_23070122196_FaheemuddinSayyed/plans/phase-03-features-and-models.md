# Phase 03 — Features, models, and metrics

## Objective

Build the three stateless building blocks the training loop needs: the preprocessing
`ColumnTransformer`, the model factory, and the metric registry. This phase adds no
pipeline stage and touches no real data — it exists so phase 04 can assemble a training
loop out of pieces that are already unit-tested.

## Preconditions

Phases 01 and 02 are complete and committed. Specifically:

- `.venv/` on Python 3.11 with all dependencies; `make lint` and `make test` both pass.
- `config/default.yaml` with all nine top-level keys.
- `src/config.py`: `PROJECT_ROOT`, `load_config(path, root=None)`, `validate_config`,
  `resolve_paths`, `ensure_dirs`.
- `src/contract.py`: `DataContract` (fields `id_column`, `target_column`, `task_type`,
  `n_classes`, `numeric_features`, `categorical_features`; properties `feature_columns`,
  `is_classification`, `is_binary`), `derive_contract`, `contract_to_dict`,
  `contract_from_dict`, `save_contract`, `load_contract`, `contract_to_markdown`,
  `run_inspect`.
- `src/data.py`: `raw_path`, `load_raw`, `validate`, `get_cv_splitter`.
- `src/cli.py`: `configure_logging`, `build_parser`, `main` — `inspect` subcommand only.
- `tests/conftest.py`: `FIXTURES_DIR`, `DEFAULT_CONFIG_PATH`, `TINY_MODELS`,
  `make_config(tmp_path, fixture, **overrides)`.
- Committed fixtures at `tests/fixtures/clf/` and `tests/fixtures/reg/`.
- `tests/test_contract.py`, `tests/test_data.py` passing.
- The real-data contract is confirmed: `id` / `addicted_label` / binary classification,
  9 numeric + 3 categorical features.

Not yet existing: `src/features.py`, `src/models.py`, `src/metrics.py`, `src/train.py`,
`src/predict.py`.

## Context recap

### The probability rule (CLAUDE.md §5a) — why the metric registry is shaped this way

The competition is scored on **ROC AUC against predicted probabilities**. One consequence
lands squarely in this phase:

> Any metric in the registry that needs hard labels (accuracy, f1_macro) must threshold
> the stored probabilities at 0.5 internally. The stored artefact stays a probability.

So: **the caller always passes probabilities; the metric adapts.** There is exactly one
canonical prediction representation in this pipeline, and it is a float. No caller ever
thresholds before calling a metric.

### `src/features.py` specification (Implementation Plan §3.4)

- `build_preprocessor(contract, cfg) -> ColumnTransformer` using sklearn `Pipeline`s:
  - numeric branch: `SimpleImputer(strategy=cfg.features.numeric_imputation,
    add_indicator=cfg.features.add_missing_indicators)`, plus `StandardScaler` only if
    `scale_numeric` is true.

    **`add_missing_indicators` is new since the plan was first written.** Phase 02 measured
    the real data and found *every* feature carries 4.2 %–19.4 % missing values. Median
    imputation at that scale maps "unknown" onto "typical" and throws away a pattern that is
    plausibly predictive. `add_indicator=True` appends one binary column per numeric feature
    that had missing values at fit time — sklearn's `features="missing-only"` behaviour, so
    the count depends on the fit data, not on the feature count. It adds no dependency and
    introduces no leakage. The categorical branch is unchanged.

    Consequence for shapes, which the tests below assert: the `clf` fixture has NaNs in `n1`
    and `n2` only, so its numeric branch emits 4 imputed + **2 indicator** = 6 columns, and
    the default ordinal output is **8** columns, not 6. On the real data it is 9 + 9 + 3 =
    **21** columns.
  - categorical branch: `SimpleImputer(strategy=...)` then either
    `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)` or
    `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` per config. If
    `categorical_encoding: onehot` and a column's cardinality exceeds
    `max_onehot_cardinality`, fall back to ordinal for that column and log a warning.
- `encode_target(y, contract) -> tuple[ndarray, LabelEncoder | None]` — label-encode for
  classification, pass through for regression.
- Fit the preprocessor **once on the full training set** (imputation and ordinal encoding
  are low-leakage) and reuse it across folds. Persist it to `models/preprocessor.pkl`.
  Document this choice in the README.

Fitting and persisting happen in phase 04; this phase provides `build_preprocessor`,
`save_preprocessor` and `load_preprocessor` so phase 04 has nothing left to invent.

### `src/models.py` specification (Implementation Plan §3.5)

- `build_model(name: str, params: dict, contract, seed: int, n_jobs: int = -1)` returning
  an unfitted estimator. Supported names: `lightgbm`, `hist_gbm`. Any other name raises
  `ValueError` listing the supported names.
- LightGBM: `LGBMClassifier` or `LGBMRegressor` by task type; inject `random_state=seed`
  and `n_jobs=n_jobs`. `params` passes through verbatim, so `device` and `verbose` reach
  the estimator unmodified.
- hist_gbm: `HistGradientBoostingClassifier` / `...Regressor`; inject
  `random_state=seed`. It has no `n_jobs`; it uses OpenMP threads via `OMP_NUM_THREADS`,
  which the pipeline does not set.
- `enabled_models(cfg) -> list[dict]` — filters on `enabled`, raises if the list is empty,
  and normalises weights to sum to 1. Each returned dict carries `name`, `weight`,
  `params`, and `early_stopping_rounds` (defaulting to `None` when the key is absent).

### `src/metrics.py` specification (Implementation Plan §3.6)

- `resolve_metric(cfg, contract) -> tuple[str, Callable, bool]` returning
  `(name, fn, greater_is_better)`, applying the auto-resolution table below.
- Registry mapping each supported name to a callable `(y_true, y_pred) -> float`, where
  `y_pred` is a **probability** for binary classification and a raw value otherwise.
  `rmse` = `sqrt(mean_squared_error(...))`.
- Each entry declares `needs_labels: bool`. Metrics with `needs_labels=True` (accuracy,
  balanced_accuracy, f1_macro) threshold the incoming probabilities at 0.5 *inside the
  metric function*.
- `roc_auc` is binary-only. If selected when `task_type` is multiclass or regression,
  raise `ValueError("roc_auc requires a binary classification target; got {task}")`.

**`metric.name: auto` resolution table (Implementation Plan §2)**

| task_type | auto metric | greater_is_better |
|---|---|---|
| classification (binary) | roc_auc | true |
| multiclass | accuracy | true |
| regression | rmse | false |

> **Note a contradiction in the source documents, already resolved.** Implementation Plan
> §4.2 says the test for auto resolution should assert "accuracy for clf and rmse for
> reg". That is wrong for this fixture set: §4.1 defines the `clf` fixture as a **binary**
> target, and the §2 table above resolves binary classification to `roc_auc`, not
> accuracy. §2 is the behavioural spec and wins. The test therefore asserts `roc_auc` for
> the binary `clf` fixture, `rmse` for `reg`, and `accuracy` for a synthetic
> three-class contract. Do not "fix" the code to match §4.2's wording.

### Relevant config keys

```yaml
project:
  seed: 42

runtime:
  n_jobs: -1

features:
  numeric_imputation: median
  categorical_imputation: most_frequent
  categorical_encoding: ordinal    # ordinal | onehot
  scale_numeric: false             # tree models don't need it
  max_onehot_cardinality: 15
  add_missing_indicators: true     # one binary column per numeric feature with NaNs at fit

metric:
  name: roc_auc
  greater_is_better: true

models:
  - name: lightgbm
    enabled: true
    weight: 0.7
    early_stopping_rounds: 100
    params: {n_estimators: 3000, learning_rate: 0.03, num_leaves: 63,
             min_child_samples: 50, subsample: 0.9, subsample_freq: 1,
             colsample_bytree: 0.9, reg_lambda: 1.0, device: cpu, verbose: 1}
  - name: hist_gbm
    enabled: true
    weight: 0.3
    early_stopping_rounds: null
    params: {max_iter: 1000, learning_rate: 0.04, max_leaf_nodes: 63,
             min_samples_leaf: 50, l2_regularization: 1.0, early_stopping: true,
             n_iter_no_change: 50, validation_fraction: 0.1, verbose: 1}
```

`early_stopping_rounds` sits **beside** `params`, not inside it — it is read by phase 04's
training loop and passed as a LightGBM callback, never handed to the estimator
constructor. `enabled_models` surfaces it as a separate key for that reason.

### Hardware note (CLAUDE.md §3a)

CPU only. `runtime.n_jobs` reaches LightGBM as `n_jobs`. `device: cpu` passes through
`params` untouched — the factory must not inspect or rewrite it. Apple MPS is not
reachable from either library; do not add `torch`.

### Test specification for this phase (Implementation Plan §4.2)

- `test_features.py` — preprocessor output has no NaNs; unseen categorical values in test
  encode to `-1` rather than raising; one-hot high-cardinality fallback triggers.
- `test_metrics.py` — auto resolution; `rmse` on a known small vector equals a
  hand-computed value; `roc_auc` on a multiclass task raises.

### Fixture facts this phase asserts against

From `tests/fixtures/clf/`: train is `(60, 8)` — `id`, `n1`–`n4`, `c1`, `c2`, `target`.
`n1`–`n4` are numeric, `c1` has 3 levels plus NaNs, `c2` has **exactly 18** levels. Test
is `(20, 7)` and its **row 0 `c1` is `"z"`**, a category unseen in train. Deliberate NaNs
sit in `n1` (rows 0–2), `n2` (rows 4–5), and `c1` (row 7). The `reg` fixture is identical
in structure with ID `row_id` and continuous target `score`.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `src/features.py` | create | Preprocessor construction, target encoding, preprocessor persistence. |
| `src/models.py` | create | Model factory and enabled-model weight normalisation. |
| `src/metrics.py` | create | Metric registry and `resolve_metric`. |
| `tests/test_features.py` | create | Imputation, unseen categories, one-hot fallback, scaling, round-trip. |
| `tests/test_models.py` | create | Factory dispatch, unknown-name error, weight normalisation. |
| `tests/test_metrics.py` | create | Auto resolution, hand-computed values, threshold-inside-metric, guards. |

`tests/test_models.py` is an addition to the file list in CLAUDE.md §4 — the layout there
does not enumerate a model test, but `build_model`'s dispatch and `enabled_models`'
weight normalisation are exactly the logic that should fail loudly in a unit test rather
than three phases later inside a training run.

## Detailed steps

### 1. Write `src/features.py`

Module header and constants:

```python
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
```

`src/features.py` must not import `src/contract.py` at runtime — same rule as
`src/data.py`. `DataContract` is a type hint only.

**`select_features(frame: pd.DataFrame, contract: DataContract) -> pd.DataFrame`**

Returns `frame[contract.feature_columns]`. If any contract feature is absent, raise
`ValueError(f"Columns missing from the frame: {sorted(missing)}.")`. Both phase 04 and
phase 05 select feature columns through this one function, which is what guarantees the
persisted preprocessor sees identical column order at fit and transform time.

**`_numeric_pipeline(cfg: dict) -> Pipeline`**

```python
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
```

**`_categorical_pipeline(cfg: dict, encoding: str) -> Pipeline`**

```python
imputer = SimpleImputer(strategy=str(cfg["features"]["categorical_imputation"]))
if encoding == "onehot":
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
else:
    encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value", unknown_value=UNKNOWN_CATEGORY_CODE
    )
return Pipeline(steps=[("impute", imputer), ("encode", encoder)])
```

**`_plan_categorical_encoding(contract, cfg, train) -> tuple[list[str], list[str]]`**

Returns `(onehot_columns, ordinal_columns)`.

- If `cfg["features"]["categorical_encoding"] == "ordinal"`: return
  `([], list(contract.categorical_features))`.
- Otherwise the request is one-hot. If `train is None`, cardinality is unknown, so return
  `(list(contract.categorical_features), [])`.
- With `train` available, for each categorical column compare
  `int(train[column].nunique(dropna=True))` against
  `int(cfg["features"]["max_onehot_cardinality"])`. Columns at or below the threshold go
  one-hot; columns above it go ordinal and each logs
  ```python
  LOGGER.warning(
      "column '%s' has cardinality %d > max_onehot_cardinality %d; falling back to ordinal",
      column,
      cardinality,
      max_cardinality,
  )
  ```

**`build_preprocessor(contract, cfg, train: pd.DataFrame | None = None) -> ColumnTransformer`**

1. Validate the encoding name; raise
   `ValueError(f"features.categorical_encoding must be one of {VALID_ENCODINGS}; got '{encoding}'.")`
2. `onehot_columns, ordinal_columns = _plan_categorical_encoding(contract, cfg, train)`
3. Assemble transformers in this fixed order, skipping any with an empty column list:
   `("numeric", _numeric_pipeline(cfg), contract.numeric_features)`,
   `("categorical_onehot", _categorical_pipeline(cfg, "onehot"), onehot_columns)`,
   `("categorical_ordinal", _categorical_pipeline(cfg, "ordinal"), ordinal_columns)`
4. Return `ColumnTransformer(transformers=transformers, remainder="drop",
   verbose_feature_names_out=False)`

The `train` parameter is an extension to the Implementation Plan §3.4 signature. It is
required: the plan asks for a cardinality-based fallback, and cardinality cannot be known
from the contract alone. It is optional and defaults to `None` so callers that do not care
(the default `ordinal` path, which is what S6E8 uses) need not pass data.

**`encode_target(y: pd.Series, contract) -> tuple[np.ndarray, LabelEncoder | None]`**

```python
if not contract.is_classification:
    return y.to_numpy(dtype=float), None
encoder = LabelEncoder()
return encoder.fit_transform(y), encoder
```

**`save_preprocessor(preprocessor: ColumnTransformer, path: Path) -> None`** — `mkdir` the
parent, then `joblib.dump`.

**`load_preprocessor(path: Path) -> ColumnTransformer`** — if absent, raise
``FileNotFoundError(f"Missing {path}. Run `make train` first.")``; otherwise
`joblib.load`.

### 2. Write `src/models.py`

```python
"""Model factory and enabled-model resolution."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

if TYPE_CHECKING:
    from src.contract import DataContract

LOGGER = logging.getLogger(__name__)

SUPPORTED_MODELS = ("lightgbm", "hist_gbm")
```

**`build_model(name, params, contract, seed, n_jobs=-1) -> Any`**

```python
def build_model(
    name: str,
    params: dict[str, Any],
    contract: DataContract,
    seed: int,
    n_jobs: int = -1,
) -> Any:
    """Return an unfitted estimator for the named model and the contract's task type."""
    if name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unknown model '{name}'. Supported models: {', '.join(SUPPORTED_MODELS)}."
        )
    kwargs = dict(params or {})
    if name == "lightgbm":
        estimator_cls = LGBMClassifier if contract.is_classification else LGBMRegressor
        return estimator_cls(random_state=int(seed), n_jobs=int(n_jobs), **kwargs)
    estimator_cls = (
        HistGradientBoostingClassifier
        if contract.is_classification
        else HistGradientBoostingRegressor
    )
    return estimator_cls(random_state=int(seed), **kwargs)
```

`params` is copied before use so a caller's config dict is never mutated, and passed
through verbatim — `device`, `verbose`, `early_stopping` and everything else reach the
estimator exactly as written in YAML.

**`enabled_models(cfg) -> list[dict[str, Any]]`**

1. `specs = [entry for entry in cfg["models"] if entry.get("enabled", False)]`
2. If empty, raise
   `ValueError("No models are enabled in config. Set at least one models[].enabled to true.")`
3. Reject unknown names with the same message as `build_model`, so a typo fails before any
   data is loaded.
4. Reject duplicate names:
   `ValueError(f"Duplicate model name '{name}' in config; fold artifact paths would collide.")`
   Phase 04 writes `models/{name}_fold{k}.pkl`, so two entries sharing a name would
   silently overwrite each other.
5. Normalise weights: `total = sum(float(entry.get("weight", 0.0)) for entry in specs)`.
   If `total > 0`, each weight becomes `weight / total`; otherwise every model gets
   `1 / len(specs)` and the function logs a warning that weights were all zero.
6. Return dicts with exactly the keys `name`, `weight`, `params` (a copy), and
   `early_stopping_rounds` (from `entry.get("early_stopping_rounds")`, so a missing key
   yields `None`).

With the default config this returns weights `0.7` and `0.3` unchanged, since they already
sum to 1.

### 3. Write `src/metrics.py`

```python
"""Metric registry and metric resolution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)

if TYPE_CHECKING:
    from src.contract import DataContract

BINARY_THRESHOLD = 0.5


@dataclass(frozen=True)
class MetricSpec:
    """One metric: its callable, its direction, and whether it needs hard labels."""

    fn: Callable[[Any, Any], float]
    greater_is_better: bool
    needs_labels: bool


def _as_labels(y_pred: Any) -> np.ndarray:
    """Threshold probabilities at 0.5 (1-D) or take the argmax (2-D)."""
    array = np.asarray(y_pred)
    if array.ndim == 1:
        return (array >= BINARY_THRESHOLD).astype(int)
    return array.argmax(axis=1)


REGISTRY: dict[str, MetricSpec] = {
    "accuracy": MetricSpec(
        lambda true, pred: float(accuracy_score(true, _as_labels(pred))), True, True
    ),
    "balanced_accuracy": MetricSpec(
        lambda true, pred: float(balanced_accuracy_score(true, _as_labels(pred))), True, True
    ),
    "f1_macro": MetricSpec(
        lambda true, pred: float(f1_score(true, _as_labels(pred), average="macro")), True, True
    ),
    "roc_auc": MetricSpec(lambda true, pred: float(roc_auc_score(true, pred)), True, False),
    "rmse": MetricSpec(
        lambda true, pred: float(np.sqrt(mean_squared_error(true, pred))), False, False
    ),
    "mae": MetricSpec(lambda true, pred: float(mean_absolute_error(true, pred)), False, False),
    "r2": MetricSpec(lambda true, pred: float(r2_score(true, pred)), True, False),
}
```

**`_task_label(contract) -> str`** — used only in error messages:
`"regression"` when not classification; `"binary classification"` when `is_binary`;
otherwise `f"classification with {contract.n_classes} classes"`.

**`_auto_metric(contract) -> str`** — the §2 table:

```python
if not contract.is_classification:
    return "rmse"
return "roc_auc" if contract.is_binary else "accuracy"
```

**`resolve_metric(cfg, contract) -> tuple[str, Callable[[Any, Any], float], bool]`**

1. `requested = str(cfg["metric"]["name"]).strip().lower()`
2. `name = _auto_metric(contract) if requested == "auto" else requested`
3. Unknown name →
   `ValueError(f"Unknown metric '{name}'. Supported: {', '.join(sorted(REGISTRY))}, auto.")`
4. `roc_auc` on a non-binary task →
   ```python
   raise ValueError(f"roc_auc requires a binary classification target; got {_task_label(contract)}")
   ```
   Keep that wording, including the absent full stop — Implementation Plan §3.6 specifies
   it and the test asserts on the prefix.
5. Honour `metric.greater_is_better`: read `cfg["metric"].get("greater_is_better")`. If it
   is `None`, use the registry's value. If it is set and disagrees with the registry,
   raise
   ```python
   raise ValueError(
       f"metric.greater_is_better is {bool(configured)} but '{name}' is "
       f"{'maximised' if spec.greater_is_better else 'minimised'}. Set "
       f"metric.greater_is_better to {spec.greater_is_better} or change metric.name."
   )
   ```
   This is how the key is *honoured* rather than ignored (Implementation Plan §2: "Every
   key must be honoured by the code; none may be ignored") without letting a contradictory
   value silently invert model selection. `null` is the documented way to say "take the
   registry's direction", which is what `tests/conftest.py` does.
6. Return `(name, spec.fn, spec.greater_is_better)`.

### 4. Write `tests/test_features.py`

| Test | Asserts |
|---|---|
| `test_preprocessor_output_has_no_nans` | Fit-transform the `clf` train features: output has zero NaNs despite the injected ones. |
| `test_ordinal_output_shape` | Default config (`ordinal`): output has 8 columns — 4 imputed numeric, 2 missing indicators (`n1`, `n2`), then `c1`, `c2`. |
| `test_unseen_category_encodes_to_minus_one` | Fit on train, transform test: `transformed[0, 6] == -1` (row 0's `c1` is `"z"`; index 6 because two indicator columns precede the categoricals), and transforming does not raise. |
| `test_onehot_high_cardinality_falls_back_to_ordinal` | `features={"categorical_encoding": "onehot"}` with `train` passed: output has 10 columns (4 numeric + 2 indicators + 3 one-hot `c1` + 1 ordinal `c2`), and `caplog` contains `max_onehot_cardinality`. |
| `test_onehot_without_train_onehots_everything` | Same config but `train=None`: 27 columns (4 + 2 + 3 + 18). |
| `test_scale_numeric_standardises` | `features={"scale_numeric": True}`: the first four output columns have mean ≈ 0 and std ≈ 1. The scaler sits after the imputer, so it also scales the indicator columns; that is harmless and untested. |
| `test_missing_indicators_can_be_disabled` | `features={"add_missing_indicators": False}`: output is 6 columns and `c1` returns to index 4. |
| `test_invalid_encoding_raises` | `features={"categorical_encoding": "target"}` raises `ValueError` naming both valid options. |
| `test_select_features_orders_columns` | `select_features` returns exactly `contract.feature_columns`, in that order. |
| `test_select_features_missing_column_raises` | Dropping `n2` from the frame raises `ValueError` mentioning `n2`. |
| `test_encode_target_classification` | `clf`: returns an integer array with values `{0, 1}` and a `LabelEncoder` whose `classes_` has length 2. |
| `test_encode_target_regression` | `reg`: returns a float array and `None`. |
| `test_encode_target_string_labels` | A `pd.Series(["no","yes","no"])` target with a binary contract encodes to `[0,1,0]` and `classes_ == ["no","yes"]`. |
| `test_preprocessor_roundtrip` | `save_preprocessor` then `load_preprocessor` transforms the test frame to an array identical to the pre-save one (`np.testing.assert_allclose`). |
| `test_load_preprocessor_missing_raises` | A nonexistent path raises `FileNotFoundError` whose message contains `make train`. |

Build contracts with `derive_contract(train, sample_sub, cfg)` from real fixture frames
via `load_raw(make_config(tmp_path, "clf"))`.

### 5. Write `tests/test_models.py`

| Test | Asserts |
|---|---|
| `test_build_lightgbm_classifier` | `clf` contract yields an `LGBMClassifier` with `random_state == 42` and `n_jobs == 1`. |
| `test_build_lightgbm_regressor` | `reg` contract yields an `LGBMRegressor`. |
| `test_build_hist_gbm_by_task` | `HistGradientBoostingClassifier` / `...Regressor` per contract. |
| `test_params_pass_through_verbatim` | `params={"device": "cpu", "num_leaves": 7}` reaches `get_params()` unchanged, and the caller's dict is not mutated. |
| `test_unknown_model_raises` | `build_model("xgboost", ...)` raises `ValueError` listing `lightgbm, hist_gbm`. |
| `test_enabled_models_filters_and_normalises` | Weights `0.7`/`0.3` come back as `0.7`/`0.3`; weights `3`/`1` come back as `0.75`/`0.25`; sum is 1.0 within tolerance. |
| `test_enabled_models_skips_disabled` | One entry with `enabled: false` is excluded and the survivor's weight is 1.0. |
| `test_enabled_models_empty_raises` | All disabled raises `ValueError` mentioning `enabled`. |
| `test_enabled_models_duplicate_name_raises` | Two `lightgbm` entries raise `ValueError` mentioning `Duplicate`. |
| `test_enabled_models_zero_weights_are_equalised` | Both weights `0` yields `0.5`/`0.5` and logs a warning. |
| `test_enabled_models_surfaces_early_stopping_rounds` | An entry without the key yields `None`; an entry with `100` yields `100`; the key is never inside `params`. |

### 6. Write `tests/test_metrics.py`

| Test | Asserts |
|---|---|
| `test_auto_resolves_roc_auc_for_binary` | Binary `clf` contract with `metric.name: auto` → `("roc_auc", fn, True)`. |
| `test_auto_resolves_rmse_for_regression` | `reg` contract → `("rmse", fn, False)`. |
| `test_auto_resolves_accuracy_for_multiclass` | A hand-built contract with `n_classes=3` → `("accuracy", fn, True)`. |
| `test_rmse_matches_hand_computation` | `y_true=[1,2,3]`, `y_pred=[1,2,5]` → `sqrt(4/3) == pytest.approx(1.1547005383792515)`. |
| `test_mae_matches_hand_computation` | Same vectors → `pytest.approx(2/3)`. |
| `test_r2_on_perfect_prediction` | Identical vectors → `1.0`. |
| `test_roc_auc_on_perfect_ranking` | `y_true=[0,0,1,1]`, `y_pred=[0.1,0.2,0.8,0.9]` → `1.0`. |
| `test_accuracy_thresholds_probabilities_internally` | `y_true=[0,1,1,0]`, `y_pred=[0.2,0.9,0.4,0.1]` → `0.75`. The caller passes floats, never labels. |
| `test_f1_macro_accepts_probabilities` | Same inputs return a float in `[0, 1]` without raising on non-integer input. |
| `test_needs_labels_flags` | `REGISTRY` marks `accuracy`, `balanced_accuracy`, `f1_macro` as `needs_labels=True` and the other four as `False`. |
| `test_roc_auc_on_multiclass_raises` | Message starts `"roc_auc requires a binary classification target; got classification with 3 classes"`. |
| `test_roc_auc_on_regression_raises` | Message ends `"got regression"`. |
| `test_unknown_metric_raises` | `metric.name: "logloss"` raises `ValueError` listing the supported names. |
| `test_greater_is_better_conflict_raises` | `metric={"name": "rmse", "greater_is_better": True}` on the `reg` contract raises `ValueError` mentioning `minimised`. |
| `test_greater_is_better_null_takes_registry_value` | `metric={"name": "rmse", "greater_is_better": None}` returns `False`. |
| `test_explicit_roc_auc_on_binary_is_accepted` | `metric={"name": "roc_auc", "greater_is_better": True}` returns `("roc_auc", fn, True)`. |

Multiclass and string-label contracts can be constructed directly:

```python
DataContract("id", "target", "classification", 3, ["n1"], [])
```

No data file is needed for the metric tests.

### 7. Format, lint, test

```bash
make fmt
make lint
make test
```

## Verification

```bash
# 1. Lint clean.
make lint
# expect: exit 0, zero findings

# 2. Whole suite green — five test files now.
make test
# expect: 0 failures; tests from test_contract, test_data, test_features, test_models,
#         test_metrics all collected

# 3. The two tests the Implementation Plan calls out by name.
.venv/bin/python -m pytest -q tests/test_features.py tests/test_metrics.py
# expect: exit 0

# 4. Preprocessor behaviour on the fixtures, end to end.
.venv/bin/python -c "
import numpy as np, pandas as pd
from src.config import load_config
from src.contract import derive_contract
from src.data import load_raw
from src.features import build_preprocessor, encode_target, select_features
cfg = load_config('config/default.yaml')
cfg['paths']['raw_dir'] = cfg['paths']['raw_dir'].parent.parent / 'tests' / 'fixtures' / 'clf'
cfg['contract'] = {'id_column': None, 'target_column': None, 'task_type': None, 'drop_columns': []}
train, test, sub = load_raw(cfg)
c = derive_contract(train, sub, cfg)
pre = build_preprocessor(c, cfg, train)
xt = pre.fit_transform(select_features(train, c))
xs = pre.transform(select_features(test, c))
y, enc = encode_target(train[c.target_column], c)
print('train X shape :', xt.shape, '| NaNs:', int(np.isnan(xt).sum()))
print('feature names :', list(pre.get_feature_names_out()))
print('test  X shape :', xs.shape, '| NaNs:', int(np.isnan(xs).sum()))
print('unseen c1 code:', xs[0, 6])
print('y values      :', sorted(set(y.tolist())), '| classes:', list(enc.classes_))
assert xt.shape == (60, 8), xt.shape
assert np.isnan(xt).sum() == 0 and np.isnan(xs).sum() == 0
assert xs[0, 6] == -1, xs[0, 6]
assert sorted(set(y.tolist())) == [0, 1]
print('preprocessor ok')
"
# expect: shapes (60,6) and (20,6), zero NaNs, unseen c1 code: -1.0, y values [0,1]
# expect: preprocessor ok

# 5. The one-hot high-cardinality fallback fires and warns.
.venv/bin/python -c "
import logging; logging.basicConfig(level=logging.WARNING)
from src.config import load_config
from src.contract import derive_contract
from src.data import load_raw
from src.features import build_preprocessor, select_features
cfg = load_config('config/default.yaml')
cfg['paths']['raw_dir'] = cfg['paths']['raw_dir'].parent.parent / 'tests' / 'fixtures' / 'clf'
cfg['contract'] = {'id_column': None, 'target_column': None, 'task_type': None, 'drop_columns': []}
cfg['features']['categorical_encoding'] = 'onehot'
train, _, sub = load_raw(cfg)
c = derive_contract(train, sub, cfg)
out = build_preprocessor(c, cfg, train).fit_transform(select_features(train, c))
print('onehot+fallback shape:', out.shape)
assert out.shape == (60, 10), out.shape
print('fallback ok')
"
# expect: a WARNING line naming c2, cardinality 18 and max_onehot_cardinality 15
# expect: onehot+fallback shape: (60, 10)  then  fallback ok

# 6. Metric resolution on the real contract, and the roc_auc guard.
.venv/bin/python -c "
from src.contract import DataContract
from src.metrics import REGISTRY, resolve_metric
binary = DataContract('id', 't', 'classification', 2, ['n1'], [])
multi  = DataContract('id', 't', 'classification', 3, ['n1'], [])
reg    = DataContract('id', 't', 'regression', None, ['n1'], [])
print('explicit roc_auc :', resolve_metric({'metric': {'name': 'roc_auc', 'greater_is_better': True}}, binary)[0::2])
print('auto binary      :', resolve_metric({'metric': {'name': 'auto', 'greater_is_better': None}}, binary)[0::2])
print('auto multiclass  :', resolve_metric({'metric': {'name': 'auto', 'greater_is_better': None}}, multi)[0::2])
print('auto regression  :', resolve_metric({'metric': {'name': 'auto', 'greater_is_better': None}}, reg)[0::2])
for contract in (multi, reg):
    try:
        resolve_metric({'metric': {'name': 'roc_auc', 'greater_is_better': True}}, contract)
        raise AssertionError('roc_auc guard did not fire')
    except ValueError as exc:
        print('guard:', exc)
print('needs_labels:', {k: v.needs_labels for k, v in sorted(REGISTRY.items())})
"
# expect: explicit roc_auc : ('roc_auc', True)
#         auto binary      : ('roc_auc', True)
#         auto multiclass  : ('accuracy', True)
#         auto regression  : ('rmse', False)
#         two guard lines starting "roc_auc requires a binary classification target; got"
#         needs_labels: accuracy/balanced_accuracy/f1_macro True, mae/r2/rmse/roc_auc False

# 7. Metrics take probabilities, and threshold internally.
.venv/bin/python -c "
from src.metrics import REGISTRY
probs = [0.2, 0.9, 0.4, 0.1]; true = [0, 1, 1, 0]
print('accuracy on probs:', REGISTRY['accuracy'].fn(true, probs))
print('roc_auc  on probs:', REGISTRY['roc_auc'].fn(true, probs))
print('rmse hand-check  :', REGISTRY['rmse'].fn([1, 2, 3], [1, 2, 5]))
assert abs(REGISTRY['accuracy'].fn(true, probs) - 0.75) < 1e-12
assert abs(REGISTRY['rmse'].fn([1, 2, 3], [1, 2, 5]) - 1.1547005383792515) < 1e-12
print('metric values ok')
"
# expect: accuracy 0.75, rmse 1.1547005383792515, then metric values ok

# 8. Model factory dispatch and weight normalisation.
.venv/bin/python -c "
from src.contract import DataContract
from src.models import build_model, enabled_models
from src.config import load_config
binary = DataContract('id', 't', 'classification', 2, ['n1'], [])
reg = DataContract('id', 't', 'regression', None, ['n1'], [])
print(type(build_model('lightgbm', {'num_leaves': 7}, binary, 42, 1)).__name__)
print(type(build_model('lightgbm', {}, reg, 42, 1)).__name__)
print(type(build_model('hist_gbm', {}, binary, 42)).__name__)
try:
    build_model('xgboost', {}, binary, 42)
except ValueError as exc:
    print('guard:', exc)
cfg = load_config('config/default.yaml')
specs = enabled_models(cfg)
print([(s['name'], round(s['weight'], 3), s['early_stopping_rounds']) for s in specs])
assert abs(sum(s['weight'] for s in specs) - 1.0) < 1e-9
assert all('early_stopping_rounds' not in s['params'] for s in specs)
print('models ok')
"
# expect: LGBMClassifier / LGBMRegressor / HistGradientBoostingClassifier
#         guard: Unknown model 'xgboost'. Supported models: lightgbm, hist_gbm.
#         [('lightgbm', 0.7, 100), ('hist_gbm', 0.3, None)]
#         models ok

# 9. No torch, no GPU framework crept in (CLAUDE.md §3a).
grep -rniE "torch|mps|cuda|optuna|xgboost|catboost|seaborn" src/ requirements.txt || echo "OK: no excluded dependency referenced"
# expect: OK: no excluded dependency referenced

# 10. Still no forward-phase files.
ls src/
# expect: __init__.py cli.py config.py contract.py data.py features.py metrics.py models.py
#         (no train.py, no predict.py)
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0; `test_contract.py`, `test_data.py`, `test_features.py`,
      `test_models.py`, `test_metrics.py` all collected and passing.
- [ ] `src/features.py`, `src/models.py`, `src/metrics.py`, `tests/test_features.py`,
      `tests/test_models.py`, `tests/test_metrics.py` exist.
- [ ] Fitting the default (`ordinal`) preprocessor on the `clf` fixture gives a `(60, 8)`
      array with zero NaNs — 4 imputed numeric, 2 missing indicators, 2 ordinal categoricals
      — and transforming the test fixture gives `(20, 8)` with zero NaNs.
- [ ] `features={"add_missing_indicators": False}` narrows that to `(60, 6)`.
- [ ] The unseen category `"z"` transforms to `-1`, not an exception.
- [ ] `categorical_encoding: onehot` with `max_onehot_cardinality: 15` produces `(60, 10)`
      and logs a warning naming `c2`.
- [ ] `resolve_metric` returns `roc_auc` for a binary contract under both `auto` and the
      explicit name, `accuracy` for `n_classes == 3`, and `rmse` for regression.
- [ ] `resolve_metric` raises `ValueError` whose message starts `"roc_auc requires a
      binary classification target; got "` for both multiclass and regression contracts.
- [ ] `REGISTRY["accuracy"].fn([0,1,1,0], [0.2,0.9,0.4,0.1]) == 0.75` — proving hard-label
      metrics threshold probabilities internally.
- [ ] `REGISTRY["rmse"].fn([1,2,3], [1,2,5]) == pytest.approx(1.1547005383792515)`.
- [ ] `build_model` returns the classifier/regressor variant matching the contract for
      both `lightgbm` and `hist_gbm`, and raises `ValueError` listing both supported names
      for anything else.
- [ ] `enabled_models(load_config('config/default.yaml'))` returns two specs with weights
      summing to 1.0, `early_stopping_rounds` of `100` and `None`, and no
      `early_stopping_rounds` key inside either `params`.
- [ ] `grep -rniE "torch|mps|cuda|optuna|xgboost|catboost|seaborn" src/ requirements.txt`
      finds nothing.
- [ ] `src/train.py` and `src/predict.py` were **not** created.
- [ ] `git diff --stat Makefile config/default.yaml` is empty.

## Handoff notes

What phase 04 may assume exists:

- `src/features.py`: `select_features`, `build_preprocessor(contract, cfg, train=None)`,
  `encode_target`, `save_preprocessor`, `load_preprocessor`, and the constants
  `UNKNOWN_CATEGORY_CODE`, `VALID_ENCODINGS`.
- `src/models.py`: `SUPPORTED_MODELS`, `build_model(name, params, contract, seed,
  n_jobs=-1)`, `enabled_models(cfg)`.
- `src/metrics.py`: `MetricSpec`, `REGISTRY`, `BINARY_THRESHOLD`, `resolve_metric(cfg,
  contract)`.

Decisions later phases must stay consistent with:

1. **`select_features` is the only way to pick feature columns.** Phase 04 fits the
   preprocessor on `select_features(train, contract)`; phase 05 must transform
   `select_features(test, contract)`. Selecting columns any other way risks a different
   order and a silently wrong transform.
2. **Transformer order is numeric → one-hot → ordinal.** Output column positions follow
   from it (the fixture tests hard-code index 4 for `c1`). Do not reorder.
3. **Metrics always receive probabilities.** Phase 04 must pass
   `predict_proba(X)[:, 1]` straight into the metric callable and must never threshold
   before calling it. Thresholding lives inside the metric, once (CLAUDE.md §5a).
4. **`greater_is_better: null` means "use the registry".** A non-null value that
   contradicts the registry raises. Phase 06's `config/ci.yaml` must therefore either omit
   the value or match the registry.
5. **`early_stopping_rounds` lives beside `params`, never inside it.** Phase 04 reads it
   from the spec dict and turns it into a LightGBM callback. Putting it in `params` would
   make `build_model` pass it to the constructor, where LightGBM no longer accepts it.
6. **`build_model` never inspects `params`.** `device: cpu` and `verbose: 1` are the
   config author's business. Phase 04 must not strip or rewrite them either.
7. **`load_preprocessor` raises `FileNotFoundError` mentioning `make train`.** Phase 05's
   missing-artifact handling should let that message through rather than wrapping it.
8. **`build_preprocessor`'s third argument is optional.** Phase 04 passes the training
   frame so the cardinality fallback can work; phase 05 never calls it at all, because it
   loads the fitted object from disk.

Commit before moving on:

```bash
git add -A && git commit -m "phase 03: features, models, and metrics"
```
