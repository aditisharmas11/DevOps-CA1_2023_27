# Phase 04 — Training pipeline

## Objective

Assemble the K-fold cross-validation training loop: fit the preprocessor once, train every
enabled model on every fold, accumulate out-of-fold **probabilities**, persist the fold
models and the contract, and write `reports/metrics.json` and
`reports/oof_predictions.csv`. This phase also makes the run observable — there is no time
limit, runs are long, and the operator must always be able to see where they are.

## Preconditions

Phases 01–03 are complete and committed. `make lint` and `make test` pass with five test
files. Specifically available:

- `src/config.py`: `PROJECT_ROOT`, `load_config(path, root=None)`, `resolve_paths`,
  `ensure_dirs`.
- `src/contract.py`: `DataContract` (`feature_columns`, `is_classification`, `is_binary`),
  `derive_contract`, `save_contract(contract, path, label_classes=None)`, `load_contract`,
  `contract_to_markdown`, `run_inspect`.
- `src/data.py`: `raw_path`, `load_raw`, `validate`, `get_cv_splitter`.
- `src/features.py`: `select_features`, `build_preprocessor(contract, cfg, train=None)`,
  `encode_target`, `save_preprocessor`, `load_preprocessor`.
- `src/models.py`: `SUPPORTED_MODELS`, `build_model(name, params, contract, seed,
  n_jobs=-1)`, `enabled_models(cfg)`.
- `src/metrics.py`: `MetricSpec`, `REGISTRY`, `BINARY_THRESHOLD`, `resolve_metric`.
- `src/cli.py`: `configure_logging`, `build_parser`, `main` — **`inspect` subcommand
  only**; `build_parser` iterates a tuple of `(name, help_text)` pairs.
- `tests/conftest.py`: `make_config`, `TINY_MODELS`.
- `Makefile` with `make train` already wired to
  `$(PY) -m src.cli train --config config/default.yaml`. **Do not edit the Makefile.**
- Real data confirmed in `data/raw/`: `id` / `addicted_label` / binary classification,
  691,369 train rows, 296,302 test rows, 9 numeric + 3 categorical features.

Not yet existing: `src/train.py`, `src/predict.py`, `tests/test_smoke_pipeline.py`.

## Context recap

### The probability rule (CLAUDE.md §5a) — this phase is where it is won or lost

> - Out-of-fold predictions for binary classification are stored as
>   `model.predict_proba(X)[:, 1]` — a float in [0, 1]. **Never** `model.predict(X)`.
> - Blending averages probabilities across folds and across models. Never vote on labels.
> - Any metric in the registry that needs hard labels must threshold the stored
>   probabilities at 0.5 internally. The stored artefact stays a probability.

`predict()` on a binary task anywhere in `src/train.py` is a defect, even where the code
appears to work.

### Runtime and progress (CLAUDE.md §2, §7a)

There is **no wall-clock limit**. Training may run for hours. The pipeline is CPU-only and
multi-threaded via `runtime.n_jobs`; Apple MPS is unreachable from LightGBM and
scikit-learn (CLAUDE.md §3a) — do not add `torch`.

Because runs are long, progress reporting is a functional requirement, verbatim from §7a:

- Every stage logs its start and end at `INFO` with elapsed seconds.
- `train` logs the derived contract, train/test shapes, the enabled models and their
  normalised weights, and then for **every fold of every model** a line on entry
  (`model 1/2 lightgbm | fold 3/5 | fit rows=553095 val rows=138274`) and a line on exit
  carrying that fold's score and elapsed seconds, plus a cumulative
  `elapsed / estimated remaining` figure derived from mean fold time so far.
- LightGBM's own output is routed into Python logging via
  `lightgbm.register_logger(logging.getLogger("lightgbm"))`, so per-iteration eval lines
  carry timestamps. Per-iteration reporting uses a
  `log_evaluation(period=runtime.log_every_n_iterations)` callback with the fold's
  validation slice as `eval_set`.
- `HistGradientBoosting*` receives `verbose=1` from config so it reports its own
  iterations. sklearn writes those to stdout itself; that is not a `print()` in `src/`.
- `runtime.progress: false` reduces this to stage-level logging only. Nothing may depend on
  `progress` being true.
- `print()` remains banned in `src/`.

### `src/train.py` specification (Implementation Plan §3.7)

`run_train(cfg) -> dict` does, in order:

1. Load raw data, derive contract, validate.
2. Build and fit preprocessor; transform X; encode y.
3. For each enabled model, for each CV fold:
   - log the fold header before fitting
   - fit on the fold's train indices. For LightGBM, pass `eval_X=X_val, eval_y=y_val`
     (**not** `eval_set=[(X_val, y_val)]` — LightGBM 4.7 deprecates that form and warns on
     every fit, which would pollute the progress output §7a requires to stay readable;
     `requirements.txt` therefore pins `lightgbm~=4.7`, where `eval_X`/`eval_y` exist),
     `eval_metric` matching the resolved metric where LightGBM supports it (`auc` for
     binary), and `callbacks=[log_evaluation(period=runtime.log_every_n_iterations)]` when
     `runtime.progress` is true. When the model's `early_stopping_rounds` is not null, add
     `early_stopping(stopping_rounds=..., verbose=progress)` and log the chosen
     `best_iteration_`.
   - predict on the fold's validation indices and accumulate into that model's OOF array.
     **For binary classification use `predict_proba(X_val)[:, 1]`**, for multiclass use the
     full `predict_proba` matrix, for regression use `predict`.
   - persist the fitted estimator to `models/{model_name}_fold{k}.pkl` via `joblib`
   - log the fold's score, its elapsed seconds, and cumulative elapsed vs. estimated
     remaining time
4. Compute per-fold and mean CV scores per model, plus the weighted-blend OOF score.
5. Write `reports/metrics.json` (shape below).
6. Write `reports/oof_predictions.csv` with columns: ID, true target, one OOF column per
   model, and the blended OOF.
7. Persist `models/contract.json` so `predict` does not need `train.csv`.
8. Log a summary table of per-model and blend scores.

**`reports/metrics.json` shape:**

```json
{
  "metric": "roc_auc",
  "greater_is_better": true,
  "task_type": "classification",
  "n_splits": 5,
  "per_model": {
    "lightgbm": {"folds": [0.912, 0.908], "mean": 0.910, "std": 0.003},
    "hist_gbm": {"folds": [], "mean": 0.0, "std": 0.0}
  },
  "blend": {"weights": {"lightgbm": 0.7, "hist_gbm": 0.3}, "score": 0.913},
  "runtime_seconds": 123.4,
  "fold_seconds": {"lightgbm": [31.2, 30.8], "hist_gbm": []},
  "best_iterations": {"lightgbm": [1421, 1388]},
  "config_snapshot": {}
}
```

`config_snapshot` must be JSON-serialisable: `paths` values are `Path` objects after
`resolve_paths`, so convert recursively (`Path` → `str`, numpy scalars → Python scalars)
before dumping. `best_iterations` is omitted for models that did not early stop.

**Sanity check to log, not to assert:** a blended ROC AUC below 0.5 means the probability
column is inverted or labels are misaligned. Below ~0.6 on a Playground tabular set usually
means a preprocessing bug. Log a warning in either case.

### Early stopping and its caveat (Implementation Plan §3.7)

`early_stopping_rounds: 100` is set for LightGBM. Because the stopping iteration is chosen
on the same fold used to compute that fold's OOF score, reported CV is **mildly
optimistic**. It is left on because it prevents overfitting 3000 trees, and the effect on
leaderboard ranking is negligible at this scale. This caveat must be stated in the README
(phase 07). Setting `early_stopping_rounds: null` removes the effect entirely.

`hist_gbm` early-stops internally instead, via `early_stopping: true`,
`n_iter_no_change: 50`, `validation_fraction: 0.1` inside its `params` — its
`early_stopping_rounds` key is `null` and no callback is built for it.

### The preprocessor fitting decision (Implementation Plan §3.4)

Fit the preprocessor **once on the full training set** — imputation and ordinal encoding
are low-leakage — and reuse it across folds. Persist to `models/preprocessor.pkl`. Do not
refit per fold.

### Relevant config keys

```yaml
project:
  seed: 42

paths:
  models_dir: models
  reports_dir: reports

runtime:
  n_jobs: -1
  progress: true
  log_every_n_iterations: 50

cv:
  n_splits: 5
  shuffle: true

metric:
  name: roc_auc
  greater_is_better: true

models:
  - name: lightgbm
    enabled: true
    weight: 0.7
    early_stopping_rounds: 100
    params: {n_estimators: 3000, learning_rate: 0.03, num_leaves: 63, ...}
  - name: hist_gbm
    enabled: true
    weight: 0.3
    early_stopping_rounds: null
    params: {max_iter: 1000, early_stopping: true, n_iter_no_change: 50, ...}
```

### Determinism (CLAUDE.md §2)

Every random operation takes its seed from `project.seed`: the CV splitter (phase 02
already does this), `build_model`'s `random_state`, and `hist_gbm`'s internal
`validation_fraction` split. Two consecutive runs must produce byte-identical
`submission.csv` — phase 05 verifies that, but the seeding that makes it true happens here.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `src/train.py` | create | `run_train` and its helpers. |
| `src/cli.py` | modify | Register the `train` subcommand and route it to `run_train`. |
| `models/{lightgbm,hist_gbm}_fold{0..4}.pkl` | create (generated) | Fitted fold estimators. |
| `models/preprocessor.pkl` | create (generated) | Preprocessor fitted on full train. |
| `models/contract.json` | create (generated) | Contract plus label classes, for `predict`. |
| `reports/metrics.json` | create (generated) | Per-fold, per-model and blend scores. |
| `reports/oof_predictions.csv` | create (generated) | OOF probabilities (gitignored — ~40 MB). |

## Detailed steps

### 1. Write `src/train.py`

Module header:

```python
"""Cross-validated training: fits fold models and writes metrics and OOF predictions."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src.config import ensure_dirs
from src.contract import DataContract, derive_contract, save_contract
from src.data import get_cv_splitter, load_raw, validate
from src.features import (
    build_preprocessor,
    encode_target,
    save_preprocessor,
    select_features,
)
from src.metrics import resolve_metric
from src.models import build_model, enabled_models

LOGGER = logging.getLogger(__name__)

LGBM_EVAL_METRIC = {"roc_auc": "auc", "rmse": "rmse", "mae": "l1"}
LOW_AUC_INVERTED = 0.5
LOW_AUC_SUSPICIOUS = 0.6
```

`LGBM_EVAL_METRIC` deliberately covers only the metrics LightGBM names the same way.
Anything absent (`accuracy`, `f1_macro`, `balanced_accuracy`, `r2`) means "omit
`eval_metric` and let LightGBM use its objective default".

Split the work into these functions so none exceeds ~40 lines (CLAUDE.md §7).

**`_jsonable(value: Any) -> Any`** — recursive conversion for `config_snapshot`:
`Path` → `str`; `np.integer` → `int`; `np.floating` → `float`; `np.ndarray` → `list`;
`dict` → dict of converted values; `list`/`tuple` → list of converted values; everything
else returned unchanged.

**`_log_progress(done: int, total: int, elapsed: float) -> None`**

```python
mean = elapsed / done
remaining = mean * (total - done)
LOGGER.info(
    "progress %d/%d model-folds | elapsed %.1fs | mean %.1fs/fold | est. remaining %.1fs",
    done,
    total,
    elapsed,
    mean,
    remaining,
)
```

**`_prepare(cfg) -> tuple[pd.DataFrame, DataContract, np.ndarray, np.ndarray, Any]`**

Returns `(train, contract, x_all, y_all, label_encoder)`.

1. `ensure_dirs(cfg)`
2. `train, test, sample_sub = load_raw(cfg)`
3. `contract = derive_contract(train, sample_sub, cfg)`
4. `validate(train, test, contract)`
5. Log the contract and both shapes at `INFO` (§7a requires it).
6. `preprocessor = build_preprocessor(contract, cfg, train)`
7. `x_all = preprocessor.fit_transform(select_features(train, contract))`
8. `y_all, label_encoder = encode_target(train[contract.target_column], contract)`
9. `save_preprocessor(preprocessor, Path(cfg["paths"]["models_dir"]) / "preprocessor.pkl")`
10. `save_contract(contract, Path(cfg["paths"]["models_dir"]) / "contract.json",
    label_classes=None if label_encoder is None else list(label_encoder.classes_))`
11. Log the transformed feature-matrix shape and the preprocessor fit-once decision.

**`_lgbm_fit_kwargs(spec, cfg, x_val, y_val, metric_name) -> dict[str, Any]`**

```python
progress = bool(cfg["runtime"]["progress"])
period = int(cfg["runtime"]["log_every_n_iterations"])
callbacks: list[Any] = []
if progress and period > 0:
    callbacks.append(lgb.log_evaluation(period=period))
rounds = spec.get("early_stopping_rounds")
if rounds:
    callbacks.append(lgb.early_stopping(stopping_rounds=int(rounds), verbose=progress))
kwargs: dict[str, Any] = {"eval_X": x_val, "eval_y": y_val}
eval_metric = LGBM_EVAL_METRIC.get(metric_name)
if eval_metric:
    kwargs["eval_metric"] = eval_metric
if callbacks:
    kwargs["callbacks"] = callbacks
return kwargs
```

**`_oof_predict(model, x_val, contract) -> np.ndarray`**

```python
if not contract.is_classification:
    return np.asarray(model.predict(x_val), dtype=float)
proba = model.predict_proba(x_val)
if contract.is_binary:
    return np.asarray(proba[:, 1], dtype=float)
return np.asarray(proba, dtype=float)
```

This is the only place in `src/train.py` that produces predictions. There is no
`model.predict` call on a classification path anywhere.

**`_fit_fold(spec, cfg, contract, split, metric_name) -> tuple[Any, np.ndarray, int | None]`**

`split` carries `x_tr, y_tr, x_val, y_val`. Build the estimator with
`build_model(spec["name"], spec["params"], contract, int(cfg["project"]["seed"]),
int(cfg["runtime"]["n_jobs"]))`. For `lightgbm`, call `fit` with
`**_lgbm_fit_kwargs(...)`; for anything else, plain `fit(x_tr, y_tr)`. Return the fitted
model, `_oof_predict(model, x_val, contract)`, and `getattr(model, "best_iteration_",
None)`.

**`_train_one_model(spec, cfg, contract, x_all, y_all, splitter, metric_fn, metric_name,
progress) -> dict[str, Any]`**

Loops folds via `splitter.split(x_all, y_all)`, and for each fold:

1. Log the entry line required by §7a:
   ```python
   LOGGER.info(
       "%s | fold %d/%d | fit rows=%d val rows=%d",
       spec["name"],
       fold + 1,
       n_splits,
       len(train_idx),
       len(val_idx),
   )
   ```
2. Time the fit, call `_fit_fold`, write the OOF slice into the model's array.
3. `joblib.dump(model, models_dir / f"{spec['name']}_fold{fold}.pkl")`
4. Score the fold with `metric_fn(y_all[val_idx], oof[val_idx])` and log:
   ```python
   LOGGER.info(
       "%s | fold %d/%d | %s=%.6f | %.1fs%s",
       spec["name"],
       fold + 1,
       n_splits,
       metric_name,
       score,
       fold_seconds,
       "" if best_iteration is None else f" | best_iteration={best_iteration}",
   )
   ```
5. Call `progress(...)` — the caller passes a closure that owns the global
   `done / total / elapsed` counters, so the ETA spans all models, not just this one.

Return `{"oof": array, "folds": [...], "seconds": [...], "best_iterations": [...]}`.

The OOF array is allocated as `np.zeros(len(y_all))` for binary and regression, and
`np.zeros((len(y_all), contract.n_classes))` for multiclass.

**`_blend(oof_by_model: dict[str, np.ndarray], specs: list[dict]) -> np.ndarray`**

Weighted sum of each model's OOF array using the already-normalised `spec["weight"]`.
Averaging probabilities, never labels.

**`_write_oof_csv(path, train, contract, oof_by_model, blended) -> None`**

Columns in this order: `contract.id_column`, `contract.target_column` (the **original**
target values from `train`, not the encoded array), one column per model, then the blend.
Naming: `oof_{model}` and `oof_blend` for binary/regression;
`oof_{model}_class{j}` / `oof_blend_class{j}` for multiclass. `index=False`.

**`_warn_on_implausible_score(metric_name, score) -> None`**

Only for `roc_auc`: below `LOW_AUC_INVERTED` log
`"blended %s is %.4f (< 0.5): the probability column is probably inverted or labels are misaligned"`;
below `LOW_AUC_SUSPICIOUS` log
`"blended %s is %.4f (< 0.6): suspiciously low for this dataset — check preprocessing"`.
Warnings only — never raise.

**`run_train(cfg) -> dict[str, Any]`** — the orchestrator, roughly:

1. `started = time.perf_counter()`; log `"train: start"`.
2. `train, contract, x_all, y_all, _ = _prepare(cfg)`
3. `metric_name, metric_fn, greater_is_better = resolve_metric(cfg, contract)`
4. `specs = enabled_models(cfg)`; log each name with its normalised weight.
5. `splitter = get_cv_splitter(cfg, contract)`; `total = len(specs) * n_splits`.
6. Loop `specs`, calling `_train_one_model`, collecting results.
7. `blended = _blend(oof_by_model, specs)`;
   `blend_score = metric_fn(y_all, blended)`; `_warn_on_implausible_score(...)`.
8. Build the metrics dict exactly as specified above. `mean` and `std` come from
   `float(np.mean(folds))` and `float(np.std(folds))`. Include a model in
   `best_iterations` only if any of its per-fold values is not `None`.
9. Write `reports/metrics.json` with `json.dump(..., indent=2)`.
10. Write `reports/oof_predictions.csv`.
11. Log a summary table — one `INFO` line per model with `mean ± std`, then the blend
    score, then `"train: done in %.1fs"`.
12. Return the metrics dict.

### 2. Route LightGBM's logging into Python logging

In `src/cli.py`'s `configure_logging`, immediately after `logging.basicConfig(...)`:

```python
lgb.register_logger(logging.getLogger("lightgbm"))
```

with `import lightgbm as lgb` at the top of `src/cli.py`. This satisfies CLAUDE.md §7a:
LightGBM's per-iteration eval lines then carry the same timestamps as everything else,
instead of being written raw to stdout.

### 3. Extend `src/cli.py` with the `train` subcommand

Two edits only — do not restructure the module:

1. Add `("train", "run cross-validated training")` to the tuple `build_parser` iterates.
2. Add to `main`'s dispatch:
   ```python
   elif args.command == "train":
       run_train(cfg)
   ```
   with `from src.train import run_train` at the top.

Leave `predict` alone; phase 05 adds it. The existing `except (FileNotFoundError,
ValueError, KeyError)` handler already covers training failures — a config or contract
problem exits 1 with one log line and no traceback.

### 4. Run it on the real data

```bash
time make train 2>&1 | tee /tmp/train.log
```

Expect a long run. `make train` on 691,369 rows with 5 folds × (LightGBM up to 3000 trees
+ hist_gbm up to 1000 iterations) will take tens of minutes on a laptop CPU. **This is
expected and permitted** — CLAUDE.md §2 sets no limit. Do not reduce `n_estimators` or
`n_splits` to make it finish sooner. Watch the progress lines; if minutes pass with no
output, that is the §7a defect to fix.

## Verification

```bash
# 1. Lint clean.
make lint
# expect: exit 0, zero findings

# 2. Existing suite still green — five test files, unchanged.
make test
# expect: 0 failures

# 3. The train subcommand is registered and its help works.
.venv/bin/python -m src.cli train --help
# expect: usage text showing --config and --log-level
.venv/bin/python -m src.cli --help
# expect: subcommands "inspect" and "train"; NOT "predict" (phase 05)

# 4. Failure path stays clean — no traceback.
.venv/bin/python -m src.cli train --config nope.yaml; echo "exit=$?"
# expect: one ERROR log line about the missing config, then exit=1

# 5. Full training run on real data. No time limit; expect tens of minutes.
time make train 2>&1 | tee /tmp/train.log
# expect exit 0, and in the log:
#   - a contract line and train/test shapes
#   - both model names with normalised weights 0.7 / 0.3
#   - a "fold k/5 | fit rows=... val rows=..." line for all 10 model-folds
#   - per-iteration LightGBM lines every 50 iterations, timestamped, via the
#     "lightgbm" logger
#   - "best_iteration=" on each LightGBM fold (early stopping is on)
#   - a "progress N/10 model-folds | elapsed ... | est. remaining ..." line per fold
#   - a final summary and "train: done in ...s"

# 6. Progress output actually appeared (CLAUDE.md §7a is a requirement, not a nicety).
grep -c "fold .*/5 | fit rows=" /tmp/train.log
# expect: 10
grep -c "est. remaining" /tmp/train.log
# expect: 10
grep -c "lightgbm" /tmp/train.log
# expect: a large number — per-iteration eval lines
grep -c "best_iteration=" /tmp/train.log
# expect: 5   (one per LightGBM fold)

# 7. Artifacts exist and are complete.
ls -1 models/
# expect: contract.json, preprocessor.pkl,
#         hist_gbm_fold0..4.pkl, lightgbm_fold0..4.pkl  (12 files total)
ls -1 models/ | wc -l
# expect: 12

# 8. metrics.json has the specified shape and plausible numbers.
.venv/bin/python -c "
import json, math
m = json.load(open('reports/metrics.json'))
print('metric          :', m['metric'])
print('greater_is_better:', m['greater_is_better'])
print('task_type       :', m['task_type'])
print('n_splits        :', m['n_splits'])
for name, entry in m['per_model'].items():
    print(f'{name:10s} folds={[round(f,5) for f in entry[\"folds\"]]} mean={entry[\"mean\"]:.5f} std={entry[\"std\"]:.5f}')
print('blend weights   :', m['blend']['weights'])
print('blend score     :', m['blend']['score'])
print('runtime_seconds :', m['runtime_seconds'])
print('fold_seconds    :', {k: [round(s,1) for s in v] for k, v in m['fold_seconds'].items()})
print('best_iterations :', m.get('best_iterations'))
assert m['metric'] == 'roc_auc', m['metric']
assert m['greater_is_better'] is True
assert m['task_type'] == 'classification'
assert m['n_splits'] == 5
assert set(m['per_model']) == {'lightgbm', 'hist_gbm'}
for entry in m['per_model'].values():
    assert len(entry['folds']) == 5, entry['folds']
    assert all(0.0 <= f <= 1.0 for f in entry['folds']), entry['folds']
assert abs(sum(m['blend']['weights'].values()) - 1.0) < 1e-9
assert 0.6 < m['blend']['score'] <= 1.0, m['blend']['score']
assert math.isfinite(m['runtime_seconds']) and m['runtime_seconds'] > 0
assert 'config_snapshot' in m and m['config_snapshot']
assert isinstance(json.dumps(m['config_snapshot']), str)
print()
print('metrics.json ok')
"
# expect: blend score comfortably above 0.6 (below that is a preprocessing bug —
#         see the sanity note), every per-fold score in [0,1], metrics.json ok

# 9. The blend beats or matches the weaker single model — a cheap sanity check.
.venv/bin/python -c "
import json
m = json.load(open('reports/metrics.json'))
means = {k: v['mean'] for k, v in m['per_model'].items()}
print('per-model means:', {k: round(v, 5) for k, v in means.items()})
print('blend          :', round(m['blend']['score'], 5))
assert m['blend']['score'] >= min(means.values()), 'blend is worse than the worst model'
print('blend sanity ok')
"
# expect: blend sanity ok

# 10. OOF predictions are PROBABILITIES, not labels (CLAUDE.md §5a).
.venv/bin/python -c "
import pandas as pd
oof = pd.read_csv('reports/oof_predictions.csv')
print('columns:', list(oof.columns))
print('rows   :', len(oof))
print(oof[['oof_lightgbm', 'oof_hist_gbm', 'oof_blend']].describe().loc[['min','mean','max']])
print('distinct blend values:', oof['oof_blend'].nunique())
assert len(oof) == 691369, len(oof)
assert list(oof.columns) == ['id', 'addicted_label', 'oof_lightgbm', 'oof_hist_gbm', 'oof_blend']
for col in ['oof_lightgbm', 'oof_hist_gbm', 'oof_blend']:
    assert oof[col].between(0.0, 1.0).all(), col
    assert oof[col].nunique() > 2, f'{col} has {oof[col].nunique()} distinct values — labels, not probabilities'
    assert oof[col].notna().all(), col
print('OOF probabilities ok')
"
# expect: many thousands of distinct values in every OOF column, all within [0,1]
# expect: OOF probabilities ok
# A column with exactly 2 distinct values means predict() was used instead of
# predict_proba()[:, 1]. That is the CLAUDE.md §5a bug — fix it in this phase.

# 11. contract.json lets predict work without train.csv.
.venv/bin/python -c "
from pathlib import Path
from src.contract import load_contract
contract, classes = load_contract(Path('models/contract.json'))
print('contract:', contract.id_column, contract.target_column, contract.task_type, contract.n_classes)
print('features:', len(contract.feature_columns), '| label_classes:', classes)
assert contract.id_column == 'id' and contract.target_column == 'addicted_label'
assert contract.is_binary
assert len(contract.numeric_features) == 9 and len(contract.categorical_features) == 3
assert classes is not None and len(classes) == 2
print('contract.json ok')
"
# expect: contract.json ok, label_classes [0, 1]

# 12. The persisted preprocessor loads and transforms test data.
.venv/bin/python -c "
from pathlib import Path
from src.config import load_config
from src.contract import load_contract
from src.data import load_raw
from src.features import load_preprocessor, select_features
cfg = load_config('config/default.yaml')
_, test, _ = load_raw(cfg)
contract, _ = load_contract(Path('models/contract.json'))
pre = load_preprocessor(Path('models/preprocessor.pkl'))
x = pre.transform(select_features(test, contract))
print('transformed test:', x.shape)
assert x.shape == (296302, 21), x.shape
print('preprocessor ok')
"
# expect: transformed test: (296302, 21), preprocessor ok
#   21 = 9 imputed numeric + 9 missing indicators + 3 ordinal categoricals, because
#   features.add_missing_indicators is true and all 9 numeric columns have NaNs.

# 13. Fold artifacts are real fitted estimators with predict_proba.
.venv/bin/python -c "
import joblib
m = joblib.load('models/lightgbm_fold0.pkl')
print(type(m).__name__, '| n_features_in_:', m.n_features_in_, '| best_iteration_:', m.best_iteration_)
assert hasattr(m, 'predict_proba')
h = joblib.load('models/hist_gbm_fold0.pkl')
print(type(h).__name__, '| n_iter_:', h.n_iter_)
print('fold models ok')
"
# expect: LGBMClassifier with a best_iteration_ below 3000, HistGradientBoostingClassifier

# 14. reports/metrics.json is committed; oof_predictions.csv is not.
git check-ignore -q reports/metrics.json; echo "metrics ignored? exit=$?"
# expect: exit=1  (NOT ignored)
git check-ignore -q reports/oof_predictions.csv; echo "oof ignored? exit=$?"
# expect: exit=0  (ignored — it is ~40 MB)

# 15. No predict() on a classification path, and no print() in src/.
grep -rn "\.predict(" src/train.py
# expect: exactly one hit, inside _oof_predict's `not contract.is_classification` branch
grep -rn "print(" src/ || echo "OK: no print() in src/"
# expect: OK: no print() in src/

# 16. The Makefile and config were not modified.
git diff --stat Makefile config/default.yaml
# expect: no output
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0; the five existing test files still pass.
- [ ] `src/train.py` exists; `src/cli.py` registers `inspect` and `train` and **not**
      `predict`.
- [ ] `python -m src.cli train --config nope.yaml` exits 1 with one log line and no
      traceback.
- [ ] `make train` exits 0 on the real data.
- [ ] `models/` contains exactly 12 files: `contract.json`, `preprocessor.pkl`, and
      `{lightgbm,hist_gbm}_fold{0,1,2,3,4}.pkl`.
- [ ] `reports/metrics.json` exists and parses; `metric == "roc_auc"`,
      `greater_is_better is True`, `task_type == "classification"`, `n_splits == 5`.
- [ ] Both models have exactly 5 per-fold scores, every one in `[0, 1]`.
- [ ] `blend.weights` sums to 1.0 and `blend.score` is a finite float in `(0.6, 1.0]`.
- [ ] `blend.score >= min(per_model[*].mean)`.
- [ ] `runtime_seconds` is a positive finite float; `fold_seconds` has 5 entries per model.
- [ ] `best_iterations["lightgbm"]` has 5 integer entries, **each strictly below the
      configured `n_estimators`** — proving early stopping, not the cap, ended every fold.
      Likewise every `hist_gbm` fold's `n_iter_` must be below its `max_iter`. If any fold
      sits at its cap the model was still improving, the reported CV understates what the
      data supports, and the fix is to raise that cap in `config/default.yaml` and re-run
      (CLAUDE.md §2: spend the budget on more estimators). This is a config-only change.
- [ ] `config_snapshot` is present and `json.dumps`-able — no `Path` or numpy scalar
      survived.
- [ ] `reports/oof_predictions.csv` has 691,369 rows and columns
      `['id', 'addicted_label', 'oof_lightgbm', 'oof_hist_gbm', 'oof_blend']`.
- [ ] **Every OOF column lies within `[0, 1]`, has more than two distinct values, and has
      no nulls.** More than two distinct values is the check that `predict_proba(X)[:, 1]`
      was used rather than `predict(X)`.
- [ ] `load_contract('models/contract.json')` returns a binary contract with 9 numeric and
      3 categorical features plus a 2-element `label_classes`.
- [ ] `load_preprocessor('models/preprocessor.pkl').transform(select_features(test, c))`
      returns shape `(296302, 21)` (9 numeric + 9 missing indicators + 3 categorical).
- [ ] `/tmp/train.log` contains 10 fold-entry lines, 10 `est. remaining` lines, 5
      `best_iteration=` lines, and timestamped per-iteration LightGBM lines.
- [ ] `grep -rn "print(" src/` finds nothing.
- [ ] `grep -rn "\.predict(" src/train.py` finds only the regression branch.
- [ ] `git check-ignore reports/metrics.json` exits 1;
      `git check-ignore reports/oof_predictions.csv` exits 0.
- [ ] `git diff --stat Makefile config/default.yaml` is empty.
- [ ] `src/predict.py` and `tests/test_smoke_pipeline.py` were **not** created.

## Handoff notes

What phase 05 may assume exists:

- `models/preprocessor.pkl`, `models/contract.json`, and
  `models/{name}_fold{k}.pkl` for `k` in `0..n_splits-1`, written by this phase.
- `src/train.py` exporting `run_train`, plus the helpers `_jsonable`, `_oof_predict`,
  `_blend` and the constants `LGBM_EVAL_METRIC`, `LOW_AUC_INVERTED`, `LOW_AUC_SUSPICIOUS`.
- `src/cli.py` with `inspect` and `train` registered, and LightGBM's logger already routed
  into Python logging by `configure_logging`.
- `reports/metrics.json` and `reports/oof_predictions.csv`.

Decisions later phases must stay consistent with:

1. **Fold artifact naming is `models/{model_name}_fold{k}.pkl`, `k` zero-indexed.**
   Implementation Plan §1's diagram says `models/fold_*.pkl`; §3.7 gives the explicit
   pattern above and that is the one implemented. Phase 05 globs for it — a rename breaks
   loading.
2. **`models/contract.json` carries `label_classes`.** Phase 05's
   `round_predictions_to_labels: true` branch inverse-maps through it. Phase 05 must not
   re-read `train.csv` for label values.
3. **Blend weights are the normalised ones from `enabled_models(cfg)`.** Phase 05 must call
   the same function rather than reading `cfg["models"][i]["weight"]` directly, or the
   submission blend will not match the OOF blend that `metrics.json` reports.
4. **OOF and test predictions are both `predict_proba(X)[:, 1]`.** Phase 05 averages folds
   and then blends models, in that order — probabilities throughout, never labels
   (CLAUDE.md §5a).
5. **The preprocessor is fitted once on full train and persisted.** Phase 05 must load it
   and call `transform`, never `fit_transform`, and must select columns through
   `select_features` so the column order matches.
6. **`early_stopping_rounds` is read from the spec, not passed to the constructor.** It
   produces a `lgb.early_stopping` callback. Phase 06's `config/ci.yaml` sets it to `null`.
7. **`runtime.progress: false` must fully silence per-fold and per-iteration logging.**
   Phase 06's smoke tests and CI rely on that; if any progress line is unconditional, the
   test output becomes unreadable.
8. **`configure_logging` calls `lgb.register_logger`.** Do not move that call into
   `train.py` — it must run once, at logging setup, before any estimator is built.
9. **Early stopping makes reported CV mildly optimistic.** Phase 07's README must state
   this; do not quietly drop the caveat.

Commit before moving on:

```bash
git add -A && git commit -m "phase 04: cross-validated training pipeline"
```
