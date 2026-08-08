# Implementation Plan

Project: **Kaggle Playground Series S6E8 — Predicting Smartphone Addiction**
Repository: `smartphone-addiction-s6e8`
Purpose: DevOps course CA deliverable.

Read alongside `CLAUDE.md`. Where the two conflict, `CLAUDE.md` wins on constraints
and conventions; this file wins on *what to build*.

---

## 0. Context you need before starting

### 0.1 What the CA requires

The college assignment asks the student to pick a public challenge and fill a table:

| Field | Value for this project |
|---|---|
| Problem Statement with online link | https://www.kaggle.com/competitions/playground-series-s6e8 |
| Submission date | **31 August 2026** (final submission deadline, 23:59 UTC) |
| Issue Repository | The student's own GitHub repo for this project |
| Github name/email id | The student's GitHub handle and email |
| Github assigned repo | The path of this project's folder inside the college repo |

The work is then pushed **as a folder inside a college-created repository**.

> **Critical packaging note:** GitHub Actions only executes workflows located at
> `.github/workflows/` in the **repository root**. Once this project is copied into
> the college repo as a subfolder, its CI will *not* run there. Therefore the
> standalone repo is the canonical one — CI runs there, and that is where the green
> build badge and Actions screenshots come from. The college repo receives a copy.
> Phase 07 handles this explicitly.

### 0.2 Confirmed competition specification

Verified directly from the competition Overview and Data tabs:

- **Timeline:** starts 1 August 2026, final submission deadline **31 August 2026**.
  All deadlines are 23:59 UTC.
- **Task:** binary classification.
- **Target:** `addicted_label`. **ID:** `id`.
- **Metric:** area under the ROC curve between the predicted probability and the
  observed target.
- **Submission format:** header `id,addicted_label`, one row per test `id`, value is a
  **probability** — the sample rows shown on the page are `0.2`, `0.3`, `0.1`.
- **Files:** `train.csv` (with target), `test.csv` (without), `sample_submission.csv`.
- **Data:** synthetically generated, inspired by the Smartphone Addiction Prediction
  Dataset on Kaggle. **Measured from the downloaded files** (not lightweight):
  `train.csv` is 43 MB / 691,369 rows × 14 columns; `test.csv` is 18 MB / 296,302 rows
  × 13 columns; `sample_submission.csv` is 296,302 rows. That leaves 12 features —
  9 numeric (`age`, `daily_screen_time_hours`, `social_media_hours`, `gaming_hours`,
  `work_study_hours`, `sleep_hours`, `notifications_per_day`, `app_opens_per_day`,
  `weekend_screen_time`) and 3 categorical (`gender`, `stress_level`,
  `academic_work_impact`). Missing values are present across the numeric columns.
  Class balance is 490,474 positive / 200,895 negative (70.9% positive). Every
  `sample_submission.csv` row holds the constant 0.7094243450313797, which is exactly
  that base rate — further confirmation that the column is a probability.
- **Prizes:** Kaggle merchandise for the top three. No cash, no medals.

### 0.3 The one thing that must not be got wrong

**The submission holds probabilities, not labels.** A file of 0s and 1s is
syntactically valid, uploads without error, and scores far below what the same model
would score with probabilities — because ROC AUC needs the ranking information that
thresholding destroys. Every stage of the pipeline therefore carries floats:
`predict_proba(X)[:, 1]` for out-of-fold arrays, probability averaging for blending,
and a float column in `submission.csv`. See `CLAUDE.md` §5a.

### 0.4 What is still derived rather than hardcoded

The contract above is written into `config/default.yaml`, but `src/` still derives
`id` / `addicted_label` / task type from `sample_submission.csv` and the target dtype
at runtime, with config as an override. This is deliberate: it keeps the detection
logic exercised, lets the regression test fixture run through the same code, and
makes the pipeline resilient if Kaggle revises the files. Do not litter `src/` with
the literal strings `"id"` or `"addicted_label"`.

---

## 1. Architecture

A linear, three-stage CLI pipeline. No orchestration framework.

```
data/raw/*.csv
      │
      ▼
 [inspect]  ── derives the data contract ──▶ reports/data_contract.md
      │
      ▼
 [train]    ── K-fold CV, fits N models ───▶ models/fold_*.pkl
      │                                      models/preprocessor.pkl
      │                                      reports/metrics.json
      │                                      reports/oof_predictions.csv
      ▼
 [predict]  ── loads fold models, averages ▶ submissions/submission.csv
```

Design principles:
- **Config-driven.** One YAML file controls every knob. No magic numbers in code.
- **Contract-driven.** Column roles come from the data, not from literals.
- **Fold-averaged.** Train K models on K folds, average their test predictions. This
  is the standard Playground approach and needs no separate holdout.
- **Fallback-safe.** If LightGBM misbehaves, sklearn's `HistGradientBoosting*` is a
  drop-in second model already wired in.
- **Observable.** There is no wall-clock budget, so runs are long by design. Every
  stage streams progress through `logging` per `CLAUDE.md` §7a; silence is a defect.
- **CPU-bound by choice.** Multi-threaded CPU via `runtime.n_jobs`. Apple MPS is not
  reachable from LightGBM or scikit-learn and would not help at this data scale — see
  `CLAUDE.md` §3a.

---

## 2. Configuration schema

`config/default.yaml`. Every key must be honoured by the code; none may be ignored.

```yaml
project:
  name: smartphone-addiction-s6e8
  seed: 42

paths:
  raw_dir: data/raw
  processed_dir: data/processed
  models_dir: models
  reports_dir: reports
  figures_dir: reports/figures
  submissions_dir: submissions
  train_file: train.csv
  test_file: test.csv
  sample_submission_file: sample_submission.csv

contract:
  # Confirmed from the competition page. Set to null to fall back to auto-detection
  # (see CLAUDE.md §5); explicit values always win.
  id_column: id
  target_column: addicted_label
  task_type: classification    # binary
  drop_columns: []

runtime:
  # No wall-clock budget (CLAUDE.md §2). CPU only — MPS is unreachable, see §3a.
  n_jobs: -1                  # -1 = all cores; passed to every estimator that accepts it
  progress: true              # per-fold and per-iteration logging; false = stage logs only
  log_every_n_iterations: 50  # LightGBM log_evaluation period

cv:
  n_splits: 5
  shuffle: true
  # stratified is used automatically for classification, ignored for regression

metric:
  # Confirmed official metric for S6E8. Do not change.
  # Supported: accuracy | balanced_accuracy | f1_macro | roc_auc |
  #            rmse | mae | r2
  name: roc_auc
  greater_is_better: true

features:
  numeric_imputation: median
  categorical_imputation: most_frequent
  categorical_encoding: ordinal    # ordinal | onehot
  scale_numeric: false             # tree models don't need it
  max_onehot_cardinality: 15
  add_missing_indicators: true     # see §3.4; missingness is informative in this dataset

models:
  # Each entry is trained across all folds; predictions are blended by weight.
  # Sized for accuracy, not speed — there is no time limit. Expect tens of minutes.
  # The caps are deliberately generous so that EARLY STOPPING, not the cap, decides where
  # each fold ends. A first run at n_estimators 3000 / max_iter 1000 finished with LightGBM
  # best_iteration at 2794-3000 and hist_gbm at 941-1000 on 4 of 5 folds — both models were
  # still improving when they ran out of budget, which understates the achievable score and
  # makes the reported CV depend on the cap rather than on the data.
  - name: lightgbm
    enabled: true
    weight: 0.7
    # early_stopping_rounds is read by src/train.py, not passed to the estimator.
    # It uses the fold's own validation slice as eval_set. Set to null to disable and
    # train the full n_estimators.
    early_stopping_rounds: 100
    params:
      n_estimators: 10000
      learning_rate: 0.03
      num_leaves: 63
      min_child_samples: 50
      subsample: 0.9
      subsample_freq: 1
      colsample_bytree: 0.9
      reg_lambda: 1.0
      device: cpu    # do not change; see CLAUDE.md §3a
      verbose: 1
  - name: hist_gbm
    enabled: true
    weight: 0.3
    early_stopping_rounds: null   # hist_gbm early-stops internally, see params below
    params:
      max_iter: 4000
      learning_rate: 0.04
      max_leaf_nodes: 63
      min_samples_leaf: 50
      l2_regularization: 1.0
      early_stopping: true
      n_iter_no_change: 50
      validation_fraction: 0.1
      verbose: 1

output:
  submission_filename: submission.csv
  # MUST stay false for S6E8 — the competition scores probabilities via ROC AUC.
  # This flag exists only to keep the hard-label code path testable. Do not flip it.
  round_predictions_to_labels: false
  clip_probabilities: [0.0, 1.0]   # safety clamp before writing
```

**`metric.name: auto` resolution table**

| task_type | auto metric | greater_is_better |
|---|---|---|
| classification (binary) | roc_auc | true |
| multiclass | accuracy | true |
| regression | rmse | false |

For this project `metric.name` is set explicitly to `roc_auc`, so the `auto` path is
only exercised by the regression fixture in the test suite. Keep it working anyway.

---

## 3. Module specifications

### 3.1 `src/config.py`
- `load_config(path: Path) -> dict` — reads YAML, validates required top-level keys
  (`project`, `paths`, `contract`, `runtime`, `cv`, `metric`, `features`, `models`,
  `output`), raises `ValueError` naming the missing key.
- `resolve_paths(cfg: dict, root: Path) -> dict` — converts every value under
  `paths` to an absolute `Path` relative to the repo root.
- `ensure_dirs(cfg: dict) -> None` — `mkdir(parents=True, exist_ok=True)` for every
  output directory (processed, models, reports, figures, submissions).

### 3.2 `src/contract.py`
- `@dataclass DataContract`: `id_column: str`, `target_column: str`,
  `task_type: str`, `n_classes: int | None`, `numeric_features: list[str]`,
  `categorical_features: list[str]`.
- `derive_contract(train: DataFrame, sample_sub: DataFrame, cfg: dict) -> DataContract`
  implementing the rules in `CLAUDE.md` §5, with config overrides applied last.
- `contract_to_markdown(contract, train, test) -> str` — renders a human-readable
  summary: shapes, dtypes table, target distribution (value counts for
  classification, describe() for regression), missing-value counts per column.
- Guard: if `sample_submission.csv` has fewer than 2 columns, raise a `ValueError`
  explaining the file looks wrong.

### 3.3 `src/data.py`
- `load_raw(cfg) -> tuple[DataFrame, DataFrame, DataFrame]` returning
  `(train, test, sample_submission)`.
- Before reading, check each file exists. If any is missing, raise
  `FileNotFoundError` with this exact style of message:
  ```
  Missing data/raw/train.csv.
  Download the competition data from
  https://www.kaggle.com/competitions/playground-series-s6e8/data
  and place train.csv, test.csv and sample_submission.csv in data/raw/.
  ```
- `validate(train, test, contract) -> None` — assert the target exists in train and
  is absent from test; assert the feature sets match between train and test; assert
  the ID column is unique in both. Raise `ValueError` describing the mismatch.
- `get_cv_splitter(cfg, contract)` → `StratifiedKFold` for classification,
  `KFold` for regression, both seeded from `project.seed`.

### 3.4 `src/features.py`
- `build_preprocessor(contract, cfg) -> ColumnTransformer` using sklearn `Pipeline`s:
  - numeric branch: `SimpleImputer(strategy=cfg.features.numeric_imputation,
    add_indicator=cfg.features.add_missing_indicators)`, plus `StandardScaler` only if
    `scale_numeric` is true.

    **Why the indicator.** Phase 02 measured the real data: *every* one of the 12 features
    carries missing values, from 4.2 % (`age`) to 19.4 % (`social_media_hours`). Median
    imputation on that scale maps "unknown" onto "typical" and destroys a pattern that is
    plausibly predictive here — a user who did not report gaming hours is probably not a
    heavy gamer. `add_indicator=True` keeps the imputed value *and* records that it was
    imputed, appending one binary column per numeric feature that had missing values at fit
    time (sklearn's `features="missing-only"` behaviour). It adds no dependency and no
    leakage. On the real data that widens the matrix from 12 to 21 columns: 9 imputed
    numeric + 9 indicators + 3 ordinal-encoded categoricals.

    The categorical branch keeps plain `most_frequent` imputation and gains no indicator —
    its encoded output is already a discrete code, and `categorical_imputation` is what
    config exposes for it.
  - categorical branch: `SimpleImputer(strategy=...)` then either
    `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)` or
    `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` per config.
    If `categorical_encoding: onehot` and a column's cardinality exceeds
    `max_onehot_cardinality`, fall back to ordinal for that column and log a warning.
- `encode_target(y, contract) -> tuple[ndarray, LabelEncoder | None]` — label-encode
  for classification, pass through for regression.
- Fit the preprocessor **once on the full training set** (imputation and ordinal
  encoding are low-leakage) and reuse it across folds. Persist it to
  `models/preprocessor.pkl`. Document this choice in the README.

### 3.5 `src/models.py`
- `build_model(name: str, params: dict, contract, seed: int, n_jobs: int = -1)`
  returning an unfitted estimator. Supported names: `lightgbm`, `hist_gbm`. Any other
  name raises `ValueError` listing the supported names.
- LightGBM: `LGBMClassifier` or `LGBMRegressor` by task type; inject
  `random_state=seed` and `n_jobs=n_jobs`. `params` passes through verbatim, so
  `device` and `verbose` reach the estimator unmodified.
- hist_gbm: `HistGradientBoostingClassifier` / `...Regressor`; inject
  `random_state=seed`. It has no `n_jobs`; it uses OpenMP threads, governed by the
  `OMP_NUM_THREADS` environment variable, which the pipeline does not set.
- `enabled_models(cfg) -> list[dict]` — filters on `enabled`, raises if the list is
  empty, and normalises weights to sum to 1. Each returned dict carries
  `name`, `weight`, `params`, and `early_stopping_rounds` (defaulting to `None` when
  the key is absent).

### 3.6 `src/metrics.py`
- `resolve_metric(cfg, contract) -> tuple[str, Callable, bool]` returning
  `(name, fn, greater_is_better)`, applying the auto-resolution table in §2.
- Registry mapping each supported name to a callable with signature
  `(y_true, y_pred) -> float`, where `y_pred` is a **probability** for binary
  classification and a raw value otherwise. `rmse` = `sqrt(mean_squared_error(...))`.
- Each entry also declares `needs_labels: bool`. Metrics with `needs_labels=True`
  (accuracy, balanced_accuracy, f1_macro) threshold the incoming probabilities at 0.5
  *inside the metric function*. The caller always passes probabilities; the metric
  adapts. This keeps one canonical prediction representation throughout the pipeline.
- `roc_auc` is binary-only. If selected when `task_type` is multiclass or regression,
  raise `ValueError("roc_auc requires a binary classification target; got {task}")`.

### 3.7 `src/train.py`
`run_train(cfg) -> dict` does, in order:
1. Load raw data, derive contract, validate.
2. Build and fit preprocessor; transform X; encode y.
3. For each enabled model, for each CV fold:
   - log the fold header before fitting, per `CLAUDE.md` §7a
   - fit on the fold's train indices. For LightGBM, pass
     `eval_X=X_val, eval_y=y_val` — **not** the older `eval_set=[(X_val, y_val)]` form,
     which LightGBM 4.7 deprecates with a warning on every fit — plus `eval_metric`
     matching the resolved metric where LightGBM supports it (`auc` for binary), and
     `callbacks=[log_evaluation(period=runtime.log_every_n_iterations)]` when
     `runtime.progress` is true. When the model's `early_stopping_rounds` is not null,
     add `early_stopping(stopping_rounds=..., verbose=progress)` and log the chosen
     `best_iteration_`.
   - predict on the fold's validation indices and accumulate into that model's OOF
     array. **For binary classification use `predict_proba(X_val)[:, 1]`**, for
     multiclass use the full `predict_proba` matrix, for regression use `predict`.
     Never `predict()` on a binary task — see `CLAUDE.md` §5a.
   - persist the fitted estimator to `models/{model_name}_fold{k}.pkl` via `joblib`
   - log the fold's score, its elapsed seconds, and cumulative elapsed vs. estimated
     remaining time across all remaining model-fold pairs

   Early stopping caveat to state in the README: because the stopping iteration is
   chosen on the same fold used to compute that fold's OOF score, reported CV is
   mildly optimistic. It is left on because it prevents overfitting 3000 trees and the
   effect on leaderboard ranking is negligible at this scale. Set
   `early_stopping_rounds: null` to remove the effect entirely.
4. Compute per-fold and mean CV scores per model, plus the weighted-blend OOF score.
5. Write `reports/metrics.json`:
   ```json
   {
     "metric": "roc_auc",
     "greater_is_better": true,
     "task_type": "classification",
     "n_splits": 5,
     "per_model": {
       "lightgbm": {"folds": [0.912, 0.908, ...], "mean": 0.910, "std": 0.003},
       "hist_gbm": {"folds": [...], "mean": ..., "std": ...}
     },
     "blend": {"weights": {"lightgbm": 0.7, "hist_gbm": 0.3}, "score": 0.913},
     "runtime_seconds": 123.4,
     "fold_seconds": {"lightgbm": [31.2, 30.8, ...], "hist_gbm": [...]},
     "best_iterations": {"lightgbm": [1421, 1388, ...]},
     "config_snapshot": { ... }
   }
   ```
   `config_snapshot` must be JSON-serialisable: `paths` values are `Path` objects after
   `resolve_paths`, so convert recursively (`Path` → `str`, numpy scalars → Python
   scalars) before dumping. `best_iterations` is omitted for models that did not early
   stop.
   Sanity check to log, not to assert: a blended ROC AUC below 0.5 means the
   probability column is inverted or labels are misaligned. Below ~0.6 on a Playground
   tabular set usually means a preprocessing bug. Log a warning in either case.
6. Write `reports/oof_predictions.csv` with columns: ID, true target, one OOF column
   per model, and the blended OOF.
7. Persist `models/contract.json` so `predict` does not need `train.csv`.
8. Log a summary table of per-model and blend scores.

### 3.8 `src/predict.py`
`run_predict(cfg) -> Path`:
1. Load `test.csv`, `sample_submission.csv`, `models/contract.json`,
   `models/preprocessor.pkl`. If models are missing, raise with
   `"No trained models found in models/. Run `make train` first."`
2. Transform test features with the persisted preprocessor.
3. For each model, average `predict_proba(X_test)[:, 1]` across its K folds; then blend
   models by their normalised weights. Clip to `output.clip_probabilities`.
   - `round_predictions_to_labels` is false for this competition, so the float
     probability is written directly. The true branch (argmax → inverse label-encode)
     must still exist and be covered by a test, but is not used here.
   - regression: average raw `predict` outputs instead.
4. Build the submission by **copying `sample_submission`'s ID column verbatim** and
   overwriting only the target column. Never re-derive IDs from `test.csv` ordering.
5. Assert all of the following, failing loudly with a specific message on each:
   - row count equals `sample_submission`'s
   - column names equal `sample_submission`'s exactly, in the same order
   - the ID column is identical to `sample_submission`'s, elementwise
   - no nulls, no infinities
   - **when `round_predictions_to_labels` is false and the task is binary**: every
     value lies in [0, 1] **and** the column has more than two distinct values.
     A two-value column means labels leaked in where probabilities belong — this is
     the failure mode `CLAUDE.md` §5a warns about, and it must abort the run.
6. Write `submissions/submission.csv` with `index=False`. Log the path and a
   distribution summary of the predictions.

### 3.9 `src/cli.py`
- `argparse` with subcommands `inspect`, `train`, `predict`, each taking
  `--config` (default `config/default.yaml`) and `--log-level` (default `INFO`).
- Configures `logging.basicConfig` once with a timestamped format.
- Returns exit code 0 on success, 1 on a handled error (log the message, no traceback).

### 3.10 `scripts/inspect_data.py`
Thin wrapper: load data, derive contract, write `reports/data_contract.md` via
`contract_to_markdown`, print the path. This file also carries a **manual checklist**
at the top of the generated markdown listing the five unknowns from `CLAUDE.md` §10
for the student to fill in by hand from the competition page.

### 3.11 `scripts/make_eda.py`
Generates exactly four PNGs into `reports/figures/`, no more:
1. `target_distribution.png` — bar chart (classification) or histogram (regression).
2. `missing_values.png` — horizontal bar of null counts per column; if there are no
   nulls, still emit the figure with a "no missing values" annotation.
3. `numeric_correlations.png` — `matplotlib` `imshow` heatmap of the numeric
   correlation matrix, with a colorbar and rotated tick labels.
4. `feature_importance.png` — from the fold-0 LightGBM model if it exists; if not,
   skip this one and log a notice rather than failing.
Use `matplotlib.use("Agg")` so it works headless in CI and Docker.

---

## 4. Testing specification

All tests must pass **without any real competition data present**, using committed
fixtures.

### 4.1 Fixtures — `tests/fixtures/`
Generate once with a seeded script and commit them. Keep them tiny (~60 train rows,
~20 test rows, 4 numeric + 2 categorical features, some deliberate NaNs).
Provide **two** fixture sets so both code paths are covered:
- `clf/` — binary target named `target`, ID column `id`
- `reg/` — continuous target named `score`, ID column `row_id`

Each set has `train.csv`, `test.csv`, `sample_submission.csv`.

### 4.2 Test files
- `test_contract.py` — auto-detection picks the right ID/target/task type for both
  fixture sets; config override wins over auto-detection; a 1-column
  sample_submission raises `ValueError`.
- `test_data.py` — missing file raises `FileNotFoundError` whose message mentions the
  filename and `data/raw`; validate() catches a train/test column mismatch; splitter
  is `StratifiedKFold` for clf and `KFold` for reg.
- `test_features.py` — preprocessor output has no NaNs; unseen categorical values in
  test encode to -1 rather than raising; one-hot high-cardinality fallback triggers.
- `test_metrics.py` — auto resolution returns accuracy for clf and rmse for reg;
  `rmse` on a known small vector equals a hand-computed value; `roc_auc` on a
  multiclass task raises.
- `test_smoke_pipeline.py` — the important one. Using `tmp_path` and a config that
  points at the clf fixtures with `n_splits: 2` and tiny model params, run
  `run_train` then `run_predict`, and assert:
  - `submission.csv` exists
  - its shape and column names equal the fixture's `sample_submission.csv`
  - its ID column matches the fixture's elementwise
  - it has zero nulls
  - **the target column is float, lies within [0, 1], and has more than two distinct
    values** — the regression guard against writing labels instead of probabilities
  - `metrics.json` exists, `metrics.metric == "roc_auc"`, and `blend.score` is a
    finite float in [0, 1]
  - running the pair twice yields byte-identical submission files (determinism)
  Repeat the core of this for the regression fixture, and add one test that sets
  `round_predictions_to_labels: true` on the clf fixture and asserts the output then
  contains only the two original label values — this covers the branch that S6E8
  itself does not use.

---

## 5. DevOps specification

### 5.1 `Makefile`
Implement every target listed in `CLAUDE.md` §6. Use `.PHONY`. Use a `VENV ?= .venv`
variable and `PY ?= $(VENV)/bin/python` so targets work without manual activation.
`PY` must use `?=`, not `:=` — the Docker image has no virtualenv and overrides it with
`ENV PY=python`, and a `:=` assignment inside the makefile would ignore that.
`PYTHON ?= python3.11` names the interpreter used to build the venv: on macOS the
default `python3` may be older (3.9 on this machine), and §5.4's pins target 3.11.
`make clean` removes `models/`, `reports/figures/`, `reports/metrics.json`,
`reports/oof_predictions.csv`, `submissions/*.csv`, `data/processed/*`, and
`__pycache__` — and must **never** touch `data/raw/`.

### 5.2 `Dockerfile`
- Base `python:3.11-slim`.
- Set `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` (the latter is what makes the
  §7a progress output stream rather than sit in a buffer), and `PY=python` so the
  Makefile's `PY ?=` resolves to the system interpreter instead of a missing venv.
- Install `libgomp1` **and `make`** via apt, then clean apt lists. LightGBM needs
  `libgomp1`; `make` is not present in `python:3.11-slim` and the default
  `CMD ["make", "all"]` cannot work without it.
- Copy `requirements.txt` first, `pip install --no-cache-dir -r requirements.txt`,
  then copy the rest — so the dependency layer caches.
- Create and use a non-root user.
- `WORKDIR /app`. Default `CMD ["make", "all"]`.
- `.dockerignore` must exclude `data/`, `models/`, `submissions/`, `.venv`, `.git`,
  `reports/figures`, `__pycache__`.
- `make docker-run` mounts `data/`, `models/`, `reports/` and `submissions/` as volumes
  so the container reads real data and writes every artifact back to the host. It must
  also pass `--user $(id -u):$(id -g)`: the image's non-root user has a different uid
  from the host user that owns the bind-mounted directories, so without it the
  container cannot write into them and the run fails on the first artifact.

### 5.3 `.github/workflows/ci.yml`
Triggers: `push` and `pull_request` on `main`.

One job, `build`, on `ubuntu-latest`, Python 3.11:
1. `actions/checkout@v4`
2. `actions/setup-python@v5` with `cache: pip`
3. `pip install -r requirements.txt`
4. `ruff check .`
5. `ruff format --check .`
6. `pytest -q`
7. A **fixture smoke run**: copy `tests/fixtures/clf/*` into `data/raw/`, then run
   `python -m src.cli train --config config/ci.yaml` and
   `python -m src.cli predict --config config/ci.yaml`, then assert
   `submissions/submission.csv` exists. This proves the CLI works in a clean
   environment without needing the real (undistributable) Kaggle data.
8. Upload `reports/metrics.json` and `submissions/submission.csv` as artifacts.

Create `config/ci.yaml` as a copy of default with `n_splits: 2` and small model params,
pointing at `data/raw` as usual. Three overrides are mandatory, not optional:

- `contract.id_column`, `contract.target_column` and `contract.task_type` must all be
  `null`. The CI smoke run copies `tests/fixtures/clf/*` into `data/raw/`, and those
  fixtures use the target name `target` — the confirmed S6E8 value `addicted_label`
  would make the run fail on a column that does not exist. Auto-detection handles it.
- `runtime.progress: false`, so CI logs stay readable.
- Model params must be tiny (`n_estimators: 20`, `max_iter: 20`,
  `early_stopping_rounds: null`, `early_stopping: false`); the §2 production values
  would take far longer than a CI job should.

A second job, `docker`, runs `docker build .` to verify the image still builds.

### 5.4 `requirements.txt`
Pin minor versions, e.g.:
```
pandas~=2.2
numpy~=1.26
scikit-learn~=1.5
lightgbm~=4.7
pyyaml~=6.0
matplotlib~=3.9
joblib~=1.4
pytest~=8.3
ruff~=0.6
```
If any pin fails to resolve on Python 3.11, relax that single pin and note it in the
README — do not swap the library.

`lightgbm~=4.7` is tighter than the 4.5 originally written here: `eval_X`/`eval_y` only
exist from 4.7, and §3.7 uses them because 4.7 deprecates `eval_set`. Measured resolutions
on Python 3.11: pandas 2.3.3, numpy 1.26.4, scikit-learn 1.9.0, lightgbm 4.7.0, pyyaml
6.0.3, matplotlib 3.11.1, joblib 1.5.3, pytest 8.4.2, ruff 0.16.2 — all inside their pins.

### 5.5 `pyproject.toml`
Ruff config only (`line-length = 100`, `select = ["E","F","I","UP","B"]`), plus
`[tool.pytest.ini_options]` with `testpaths = ["tests"]`. No packaging metadata — the
project runs via `python -m src.cli`, it is not pip-installable.

---

## 6. README specification

The README is a graded artifact. It must contain, in order:

1. **Title + one-line description + CI badge.**
2. **Problem statement** — predict the probability that a user is labelled
   `addicted_label` from synthetic tabular smartphone-usage features; link to
   <https://www.kaggle.com/competitions/playground-series-s6e8>; runs 1–31 August 2026
   with the final submission deadline 31 August 2026 23:59 UTC; scored on ROC AUC
   against predicted probabilities.
3. **Quickstart** — the three commands to get from clone to submission, including
   where to download the data.
4. **Project structure** — annotated tree.
5. **Pipeline description** — the three stages, in prose, with the diagram from §1.
6. **Results** — CV scores per model and blended, filled in from `metrics.json`,
   plus the public leaderboard score and rank once submitted.
7. **DevOps practices used** — an explicit section mapping each practice to where it
   lives: version control hygiene (`.gitignore`, no data in git), dependency pinning,
   linting/formatting, unit + smoke testing, CI on every push, containerisation,
   build automation via Make, reproducibility via seeding and config, artifact
   management. This section is what earns the CA marks — make it concrete, referencing
   real file paths.
8. **Reproducibility notes** — seed, determinism guarantee, Docker instructions.
9. **Limitations and future work** — three or four honest bullets.

---

## 7. Suggested phase decomposition

The startup prompt will ask for phase files. Use this decomposition — seven phases,
each independently verifiable and each roughly 20–40 minutes of *authoring* work.
Phases 04 and 05 additionally contain unattended training runs whose wall-clock time is
not bounded (`CLAUDE.md` §2) and is expected to run into tens of minutes on real data;
that waiting time is not counted in the 20–40 minute sizing.

| Phase | Title | Produces | Verified by |
|---|---|---|---|
| 01 | Scaffold and tooling | Directory tree, `.gitignore`, `requirements.txt`, `pyproject.toml`, `Makefile` skeleton, `README` skeleton, `config/default.yaml`, `src/__init__.py`, `src/config.py` | `make setup` succeeds; `make lint` passes; `python -c "from src.config import load_config; load_config('config/default.yaml')"` works |
| 02 | Data contract and loading | `src/contract.py`, `src/data.py`, `scripts/inspect_data.py`, `make inspect`; fixtures generated and committed | `make inspect` writes `reports/data_contract.md` on real data, and the auto-detected contract equals `id` / `addicted_label` / binary classification, matching config. Any mismatch halts the phase. |
| 03 | Features and models | `src/features.py`, `src/models.py`, `src/metrics.py` | `test_features.py`, `test_metrics.py` pass |
| 04 | Training pipeline | `src/train.py`, `src/cli.py` (train subcommand), `make train` | `make train` on real data writes `models/*.pkl` and a plausible `reports/metrics.json` |
| 05 | Prediction and submission | `src/predict.py`, `cli` predict subcommand, `make predict`/`make all` | `make all` writes a `submission.csv` matching sample submission's shape, columns and IDs; the `addicted_label` column is float in [0,1] with many distinct values, not 0/1; two runs are byte-identical |
| 06 | Tests, CI, Docker | full `tests/`, `.github/workflows/ci.yml`, `config/ci.yaml`, `Dockerfile`, `.dockerignore` | `make test` and `make lint` pass locally; `make docker-build && make docker-run` reproduces the submission; CI green after push |
| 07 | EDA, docs, packaging | `scripts/make_eda.py`, `make eda`, final `README.md`, `LICENSE`, college-repo copy instructions | Four PNGs exist; README sections all filled with real numbers; the folder copies cleanly into the college repo |

---

## 8. Acceptance criteria (repeat of CLAUDE.md §9 — check at the end of Phase 07)

- [ ] `make lint`, `make test` pass
- [ ] `make all` writes a valid submission, with its wall-clock time recorded in
      `reports/metrics.json` and the README (no time limit)
- [ ] long stages stream progress output per `CLAUDE.md` §7a
- [ ] two runs produce identical submissions
- [ ] Docker path reproduces the same submission
- [ ] CI green
- [ ] README complete with real CV and leaderboard numbers
- [ ] no TODOs, no stubs, no dead code
- [ ] `data/raw/*.csv` are not tracked by git

---

## 9. Explicit non-goals

Do not build any of these, even if they seem like improvements:

- hyperparameter optimisation (Optuna, grid search, Bayesian search)
- stacking meta-learners, pseudo-labelling, target encoding
- neural networks of any kind
- a Streamlit/Flask/FastAPI interface
- MLflow, DVC, Weights & Biases, or any experiment tracker
- Kubernetes manifests, Terraform, Helm charts
- multi-stage Docker builds or image size optimisation
- automatic Kaggle submission via the API
- pre-commit hooks (CI already covers lint)
- resampling, SMOTE, or `scale_pos_weight` tuning for class imbalance — ROC AUC is
  threshold-free and does not need them at this scope
- probability calibration (Platt scaling, isotonic) — it does not change AUC
- support for competitions other than S6E8

If a phase file you generate contains any of the above, it is wrong — regenerate it.

**The lifted runtime limit does not unlock any of them.** Removing the 10-minute budget
(`CLAUDE.md` §2) buys more estimators, more folds and a lower learning rate inside the
existing §2 config — nothing more. It is not licence to add a hyperparameter search, a
stacking layer, or a second library. Likewise, "use the GPU" is not achievable here and
must not become a reason to introduce `torch`; see `CLAUDE.md` §3a.
