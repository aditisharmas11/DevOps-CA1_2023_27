# Phase 05 — Prediction and submission

## Objective

Load the persisted preprocessor, contract and fold models; average each model's fold
probabilities; blend the models by their normalised weights; and write
`submissions/submission.csv`. Every guard from CLAUDE.md §5a is enforced here — this phase
is the last line of defence against shipping labels where probabilities belong.

## Preconditions

Phases 01–04 are complete and committed. `make lint` and `make test` pass with five test
files. On disk from phase 04:

- `models/preprocessor.pkl` — the preprocessor fitted once on the full training set.
- `models/contract.json` — the contract plus `label_classes`.
- `models/{lightgbm,hist_gbm}_fold{0,1,2,3,4}.pkl` — 10 fitted estimators.
- `reports/metrics.json` with `metric == "roc_auc"` and a `blend.score` above 0.6.
- `reports/oof_predictions.csv`.

Available in code:

- `src/config.py`: `load_config(path, root=None)`, `resolve_paths`, `ensure_dirs`.
- `src/contract.py`: `DataContract`, `load_contract(path) -> tuple[DataContract, list |
  None]`, `save_contract`, `derive_contract`.
- `src/data.py`: `raw_path`, `load_raw`, `validate`, `get_cv_splitter`.
- `src/features.py`: `select_features`, `load_preprocessor`, `build_preprocessor`,
  `encode_target`.
- `src/models.py`: `enabled_models(cfg)`, `build_model`.
- `src/metrics.py`: `REGISTRY`, `BINARY_THRESHOLD`, `resolve_metric`.
- `src/train.py`: `run_train`.
- `src/cli.py`: `inspect` and `train` registered; `build_parser` iterates a tuple of
  `(name, help_text)` pairs; `configure_logging` already calls `lgb.register_logger`.
- `Makefile` with `make predict` wired to `$(PY) -m src.cli predict --config
  config/default.yaml`, and `make all: inspect train predict`. **Do not edit the
  Makefile.**

Not yet existing: `src/predict.py`, `tests/test_smoke_pipeline.py`, `config/ci.yaml`,
`Dockerfile`.

## Context recap

### The probability rule (CLAUDE.md §5a) — verbatim, because this phase enforces it

> - Out-of-fold predictions for binary classification are stored as
>   `model.predict_proba(X)[:, 1]` — a float in [0, 1]. **Never** `model.predict(X)`.
> - Blending averages probabilities across folds and across models. Never vote on labels.
> - The submission's `addicted_label` column contains floats, not 0/1 integers.
> - `output.round_predictions_to_labels` is **false** for this competition. It exists only
>   so the regression/label code path stays testable; do not flip it.
> - A submission whose target column contains only the values 0 and 1 is a **bug**, even
>   though Kaggle will accept the file. Phase 05's verification must assert that the column
>   has more than two distinct values and lies within [0, 1].

The sample submission confirms the format independently: every one of its 296,302 rows
holds `0.7094243450313797`, which is exactly the training set's positive base rate
(490,474 / 691,369). Kaggle is showing a probability, not a label.

### `src/predict.py` specification (Implementation Plan §3.8)

`run_predict(cfg) -> Path`:

1. Load `test.csv`, `sample_submission.csv`, `models/contract.json`,
   `models/preprocessor.pkl`. If models are missing, raise with
   ``"No trained models found in models/. Run `make train` first."``
2. Transform test features with the persisted preprocessor.
3. For each model, average `predict_proba(X_test)[:, 1]` across its K folds; then blend
   models by their normalised weights. Clip to `output.clip_probabilities`.
   - `round_predictions_to_labels` is false for this competition, so the float probability
     is written directly. The true branch (threshold → inverse label-encode) must still
     exist and be covered by a test, but is not used here.
   - regression: average raw `predict` outputs instead.
4. Build the submission by **copying `sample_submission`'s ID column verbatim** and
   overwriting only the target column. Never re-derive IDs from `test.csv` ordering.
5. Assert all of the following, failing loudly with a specific message on each:
   - row count equals `sample_submission`'s
   - column names equal `sample_submission`'s exactly, in the same order
   - the ID column is identical to `sample_submission`'s, elementwise
   - no nulls, no infinities
   - **when `round_predictions_to_labels` is false and the task is binary**: every value
     lies in [0, 1] **and** the column has more than two distinct values. A two-value
     column means labels leaked in where probabilities belong — this is the failure mode
     CLAUDE.md §5a warns about, and it must abort the run.
6. Write `submissions/submission.csv` with `index=False`. Log the path and a distribution
   summary of the predictions.

### Relevant config keys

```yaml
paths:
  models_dir: models
  submissions_dir: submissions
  test_file: test.csv
  sample_submission_file: sample_submission.csv

runtime:
  progress: true

models:
  - {name: lightgbm, enabled: true, weight: 0.7, ...}
  - {name: hist_gbm, enabled: true, weight: 0.3, ...}

output:
  submission_filename: submission.csv
  round_predictions_to_labels: false
  clip_probabilities: [0.0, 1.0]
```

### Progress requirements for this stage (CLAUDE.md §7a)

> `predict` logs each model's fold-averaging progress and a final distribution summary
> (count, min, mean, max, and the count of distinct values) of the written column.

Stage start and end with elapsed seconds, as with every stage. `runtime.progress: false`
reduces this to stage-level logging only.

### Determinism (CLAUDE.md §2, §9)

> Two consecutive runs must produce byte-identical `submission.csv`.

Everything seeded in phase 04 feeds this. `run_predict` itself introduces no randomness:
it loads fitted estimators and averages. If two `make all` runs differ, the cause is in
training, not here — see the troubleshooting note in Handoff notes.

### Ground truth for the real data

| Property | Value |
|---|---|
| `test.csv` | 296,302 rows × 13 columns |
| `sample_submission.csv` | 296,302 rows, header exactly `id,addicted_label` |
| Transformed test matrix | `(296302, 12)` |
| `test` / `sample_submission` id range | 691,369 – 987,670 |
| Fold models to average | 5 per model, 2 models |

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `src/predict.py` | create | `run_predict` and its helpers. |
| `src/cli.py` | modify | Register the `predict` subcommand and route it to `run_predict`. |
| `submissions/submission.csv` | create (generated) | The deliverable; gitignored. |

## Detailed steps

### 1. Write `src/predict.py`

Module header:

```python
"""Inference: fold-averaged, weight-blended predictions written to a submission file."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.config import ensure_dirs
from src.contract import DataContract, load_contract
from src.data import raw_path
from src.features import load_preprocessor, select_features
from src.metrics import BINARY_THRESHOLD
from src.models import enabled_models

LOGGER = logging.getLogger(__name__)

NO_MODELS_MESSAGE = "No trained models found in {models_dir}. Run `make train` first."
```

**`_fold_model_paths(models_dir: Path, name: str) -> list[Path]`**

```python
paths = sorted(
    models_dir.glob(f"{name}_fold*.pkl"),
    key=lambda path: int(path.stem.rsplit("fold", 1)[-1]),
)
if not paths:
    raise FileNotFoundError(NO_MODELS_MESSAGE.format(models_dir=models_dir))
return paths
```

Sorting by the parsed integer, not lexicographically, so 10 folds would order correctly
after fold 9. The message keeps the wording Implementation Plan §3.8 specifies; the only
change is naming the resolved directory instead of the literal `models/`, which is more
useful when a non-default config is in play.

**`_average_folds(paths: list[Path], x_test: np.ndarray, contract: DataContract) -> np.ndarray`**

Load one estimator at a time — do not hold all ten in memory at once — and accumulate:

```python
total: np.ndarray | None = None
for index, path in enumerate(paths, start=1):
    model = joblib.load(path)
    if not contract.is_classification:
        prediction = np.asarray(model.predict(x_test), dtype=float)
    else:
        proba = model.predict_proba(x_test)
        prediction = np.asarray(proba[:, 1] if contract.is_binary else proba, dtype=float)
    total = prediction if total is None else total + prediction
    LOGGER.info("averaged fold %d/%d from %s", index, len(paths), path.name)
return total / len(paths)
```

The `LOGGER.info` line is the per-model fold-averaging progress §7a asks for. Gate it on
`runtime.progress` by passing the flag in, or log it at `DEBUG` when progress is off —
either satisfies "stage-level logging only".

**`_blend(predictions: dict[str, np.ndarray], specs: list[dict]) -> np.ndarray`**

Weighted sum using `spec["weight"]` from `enabled_models(cfg)`. The same function phase 04
used to weight its OOF blend, so the submission blend and the reported blend score agree.

**`_clip(values: np.ndarray, cfg: dict) -> np.ndarray`**

Apply `output.clip_probabilities` as `np.clip(values, low, high)`. Only for classification
when `round_predictions_to_labels` is false — clipping a regression target to [0, 1] would
be wrong. Log at `INFO` when any value was actually clipped, with the count.

**`_as_label_values(blended, contract, label_classes) -> np.ndarray`**

The `round_predictions_to_labels: true` branch. Not used by S6E8, but must exist and be
tested (phase 06 covers it).

```python
if label_classes is None:
    raise ValueError(
        "output.round_predictions_to_labels is true but models/contract.json has no "
        "label_classes. Re-run `make train` on a classification target."
    )
classes = np.asarray(label_classes)
indices = (blended >= BINARY_THRESHOLD).astype(int) if blended.ndim == 1 else blended.argmax(axis=1)
return classes[indices]
```

Note this thresholds at 0.5 for the binary case rather than taking an argmax — with a
single probability column there is no second column to argmax over. Implementation Plan
§3.8 describes the branch as "argmax → inverse label-encode", which is only literally
correct for the multiclass shape; both shapes are handled here.

**`_validate_submission(submission, sample_sub, contract, cfg) -> None`**

Raise `ValueError` on the first failure, in this order, with these messages:

1. Row count:
   `f"Submission has {len(submission)} rows but sample_submission has {len(sample_sub)}."`
2. Columns:
   `f"Submission columns {list(submission.columns)} do not match sample_submission columns {list(sample_sub.columns)}."`
3. IDs elementwise — compare with `.to_numpy()` equality, and on mismatch report the first
   offending position:
   `f"Submission ID column does not match sample_submission elementwise; first mismatch at row {position}."`
4. Nulls and infinities:
   `f"Submission target column has {count} null or non-finite value(s)."`
   (`~np.isfinite(...)` catches both `NaN` and `±inf` on a float column.)
5. Only when `contract.is_binary` **and** `round_predictions_to_labels` is false:
   - Range: `f"Submission target values fall outside [0, 1]: min={low}, max={high}."`
   - Distinctness:
     ```python
     f"Submission target column has only {n_distinct} distinct value(s); expected "
     f"probabilities. This is the labels-instead-of-probabilities bug described in "
     f"CLAUDE.md §5a."
     ```

Step 5 is the assertion CLAUDE.md §5a demands. It must abort the run, not warn.

**`run_predict(cfg) -> Path`** — the orchestrator:

1. `started = time.perf_counter()`; `LOGGER.info("predict: start")`; `ensure_dirs(cfg)`.
2. `models_dir = Path(cfg["paths"]["models_dir"])`.
3. `contract, label_classes = load_contract(models_dir / "contract.json")` — this is why
   `predict` never needs `train.csv`.
4. `test = pd.read_csv(raw_path(cfg, "test_file"))`;
   `sample_sub = pd.read_csv(raw_path(cfg, "sample_submission_file"))`.
5. `preprocessor = load_preprocessor(models_dir / "preprocessor.pkl")`;
   `x_test = preprocessor.transform(select_features(test, contract))`. **`transform`, never
   `fit_transform`.**
6. `specs = enabled_models(cfg)`; for each, `_average_folds(_fold_model_paths(models_dir,
   spec["name"]), x_test, contract)`.
7. `blended = _blend(predictions, specs)`.
8. If classification and not rounding: `blended = _clip(blended, cfg)`. If rounding:
   `values = _as_label_values(blended, contract, label_classes)`; else `values = blended`.
9. Build the submission **from the sample submission**:
   ```python
   submission = sample_sub.copy()
   submission[contract.target_column] = values
   ```
   Copying the frame carries the ID column verbatim and preserves column names and order
   for free. Never construct the ID column from `test[contract.id_column]` — Implementation
   Plan §3.8 step 4 forbids relying on test-row ordering.
10. `_validate_submission(submission, sample_sub, contract, cfg)`.
11. Write to `Path(cfg["paths"]["submissions_dir"]) / cfg["output"]["submission_filename"]`
    with `index=False`.
12. Log the distribution summary §7a requires — count, min, mean, max, and distinct count
    of the written column — then `"predict: done in %.1fs"`. Return the path.

### 2. Extend `src/cli.py` with the `predict` subcommand

Two edits only:

1. Add `("predict", "write a submission from the trained fold models")` to the tuple
   `build_parser` iterates.
2. Add to `main`'s dispatch:
   ```python
   elif args.command == "predict":
       run_predict(cfg)
   ```
   with `from src.predict import run_predict` at the top.

The existing `except (FileNotFoundError, ValueError, KeyError)` handler now also covers a
missing-models run and a failed submission assertion: both exit 1 with one log line and no
traceback.

### 3. Generate the submission

```bash
time make predict 2>&1 | tee /tmp/predict.log
```

Models from phase 04 are already on disk, so this is minutes at most.

## Verification

```bash
# 1. Lint clean.
make lint
# expect: exit 0, zero findings

# 2. Existing suite green.
make test
# expect: 0 failures

# 3. All three subcommands now registered.
.venv/bin/python -m src.cli --help
# expect: inspect, train, predict

# 4. Missing-models path is actionable, not a traceback.
#    DO NOT move models/ aside to test this: run_predict calls ensure_dirs, which
#    immediately recreates an empty models/, so `mv` back nests the backup inside it and
#    can strand the artifacts (observed in practice — they landed in a directory named
#    "models 2"). Point a throwaway config at a nonexistent models_dir instead.
.venv/bin/python - "$TMPDIR/no-models.yaml" <<'EOF'
import sys, yaml
from pathlib import Path
cfg = yaml.safe_load(Path("config/default.yaml").read_text())
cfg["paths"]["models_dir"] = "definitely-no-models-here"
Path(sys.argv[1]).write_text(yaml.safe_dump(cfg))
EOF
.venv/bin/python -m src.cli predict --config "$TMPDIR/no-models.yaml"; echo "exit=$?"
# expect: one ERROR line mentioning "Run `make train` first.", then exit=1

# 5. Generate the submission.
time make predict 2>&1 | tee /tmp/predict.log
# expect exit 0, and in the log: 5 "averaged fold k/5" lines per model (10 total),
#        and a final distribution summary line

# 6. Progress output appeared.
grep -c "averaged fold" /tmp/predict.log
# expect: 10

# 7. THE CORE CHECK — the submission holds probabilities, matching sample_submission
#    exactly in shape, columns and IDs (CLAUDE.md §5a, §9).
.venv/bin/python -c "
import numpy as np, pandas as pd
sub = pd.read_csv('submissions/submission.csv')
sample = pd.read_csv('data/raw/sample_submission.csv')
target = sample.columns[1]
print('shape        :', sub.shape, '| sample:', sample.shape)
print('columns      :', list(sub.columns))
print('dtype        :', sub[target].dtype)
print('min / max    :', sub[target].min(), '/', sub[target].max())
print('mean         :', sub[target].mean())
print('distinct     :', sub[target].nunique())
print('nulls        :', int(sub[target].isna().sum()))
print('head         :'); print(sub.head(3).to_string(index=False))
assert sub.shape == sample.shape, (sub.shape, sample.shape)
assert list(sub.columns) == list(sample.columns), list(sub.columns)
assert (sub[sample.columns[0]].to_numpy() == sample[sample.columns[0]].to_numpy()).all()
assert sub[target].notna().all()
assert np.isfinite(sub[target].to_numpy()).all()
assert sub[target].dtype.kind == 'f', sub[target].dtype
assert sub[target].between(0.0, 1.0).all(), (sub[target].min(), sub[target].max())
assert sub[target].nunique() > 2, sub[target].nunique()
print()
print('SUBMISSION VALID — float probabilities in [0,1] with', sub[target].nunique(), 'distinct values')
"
# expect: shape (296302, 2), columns ['id', 'addicted_label'], dtype float64,
#         min/max inside [0,1], mean near the 0.709 base rate,
#         distinct in the hundreds of thousands, 0 nulls
# A distinct count of 2 is the CLAUDE.md §5a bug. Fix it in this phase.

# 8. The mean prediction is near the training base rate — a cheap calibration sanity check.
.venv/bin/python -c "
import pandas as pd
mean = pd.read_csv('submissions/submission.csv')['addicted_label'].mean()
print('mean prediction:', round(mean, 6), '| train base rate: 0.709426')
assert 0.60 < mean < 0.80, mean
print('calibration sanity ok')
"
# expect: mean roughly 0.68–0.74; calibration sanity ok

# 9. The IDs come from sample_submission, not from test.csv ordering.
.venv/bin/python -c "
import pandas as pd
sub = pd.read_csv('submissions/submission.csv')
sample = pd.read_csv('data/raw/sample_submission.csv')
assert sub['id'].tolist() == sample['id'].tolist()
print('IDs match sample_submission elementwise:', len(sub), 'rows')
"
# expect: IDs match sample_submission elementwise: 296302 rows

# 10. The submission guard actually fires when fed labels. This must fail.
.venv/bin/python -c "
import pandas as pd
from src.config import load_config
from src.contract import load_contract
from src.predict import _validate_submission
from pathlib import Path
cfg = load_config('config/default.yaml')
contract, _ = load_contract(Path('models/contract.json'))
sample = pd.read_csv('data/raw/sample_submission.csv')
bad = sample.copy()
bad['addicted_label'] = (bad['addicted_label'] > 0.5).astype(int)   # labels, not probabilities
try:
    _validate_submission(bad, sample, contract, cfg)
    raise AssertionError('GUARD DID NOT FIRE — the labels-vs-probabilities check is broken')
except ValueError as exc:
    print('guard fired:', exc)
"
# expect: guard fired: Submission target column has only 1 distinct value(s); expected
#         probabilities. This is the labels-instead-of-probabilities bug ...

# 11. The out-of-range guard fires too.
.venv/bin/python -c "
import pandas as pd
from pathlib import Path
from src.config import load_config
from src.contract import load_contract
from src.predict import _validate_submission
cfg = load_config('config/default.yaml')
contract, _ = load_contract(Path('models/contract.json'))
sample = pd.read_csv('data/raw/sample_submission.csv')
sub = pd.read_csv('submissions/submission.csv')
bad = sub.copy(); bad.loc[0, 'addicted_label'] = 1.5
try:
    _validate_submission(bad, sample, contract, cfg)
    raise AssertionError('range guard did not fire')
except ValueError as exc:
    print('guard fired:', exc)
bad = sub.copy(); bad = bad.iloc[:-1]
try:
    _validate_submission(bad, sample, contract, cfg)
    raise AssertionError('row-count guard did not fire')
except ValueError as exc:
    print('guard fired:', exc)
bad = sub.copy(); bad.loc[0, 'id'] = -1
try:
    _validate_submission(bad, sample, contract, cfg)
    raise AssertionError('ID guard did not fire')
except ValueError as exc:
    print('guard fired:', exc)
"
# expect: three "guard fired:" lines — range, row count, ID mismatch

# 12. predict is deterministic on its own (cheap check, seconds).
cp submissions/submission.csv /tmp/sub-a.csv
make predict >/dev/null 2>&1
cmp /tmp/sub-a.csv submissions/submission.csv && echo "predict is byte-identical across runs"
# expect: predict is byte-identical across runs

# 13. THE FULL DETERMINISM CHECK (CLAUDE.md §9) — two complete pipeline runs.
#     This retrains from scratch twice. There is no time limit; expect this to be the
#     longest step in the phase. Run it and wait.
make all > /tmp/all-run1.log 2>&1 && cp submissions/submission.csv /tmp/sub-run1.csv
make all > /tmp/all-run2.log 2>&1 && cp submissions/submission.csv /tmp/sub-run2.csv
cmp /tmp/sub-run1.csv /tmp/sub-run2.csv && echo "make all is byte-identical across runs"
md5 /tmp/sub-run1.csv /tmp/sub-run2.csv
# expect: cmp silent, "make all is byte-identical across runs", identical md5 hashes
# If they differ, see the troubleshooting note in Handoff notes before changing code.

# 14. Per-fold CV scores are identical across the two runs too.
.venv/bin/python -c "
import json, re
run1 = re.findall(r'fold \d/5 \| roc_auc=([0-9.]+)', open('/tmp/all-run1.log').read())
run2 = re.findall(r'fold \d/5 \| roc_auc=([0-9.]+)', open('/tmp/all-run2.log').read())
print('run1 fold scores:', run1)
print('run2 fold scores:', run2)
assert run1 == run2 and len(run1) == 10, (len(run1), len(run2))
print('training is deterministic')
"
# expect: 10 identical scores in both runs; training is deterministic

# 15. No predict() on a classification path; no print() in src/.
grep -rn "\.predict(" src/predict.py
# expect: exactly one hit, in the `not contract.is_classification` branch of _average_folds
grep -rn "fit_transform" src/predict.py || echo "OK: predict never fits the preprocessor"
# expect: OK: predict never fits the preprocessor
grep -rn "print(" src/ || echo "OK: no print() in src/"
# expect: OK: no print() in src/

# 16. round_predictions_to_labels is still false, and nothing was modified.
grep -n "round_predictions_to_labels" config/default.yaml
# expect: round_predictions_to_labels: false
git diff --stat Makefile config/default.yaml
# expect: no output

# 17. The submission is gitignored.
git check-ignore -q submissions/submission.csv; echo "submission ignored? exit=$?"
# expect: exit=0
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0; the five existing test files still pass.
- [ ] `src/predict.py` exists; `python -m src.cli --help` lists `inspect`, `train` and
      `predict`.
- [ ] With `models/` absent, `python -m src.cli predict` exits 1 with a message containing
      ``Run `make train` first.`` and no traceback.
- [ ] `make predict` exits 0 and writes `submissions/submission.csv`.
- [ ] `make all` exits 0 end to end.
- [ ] `submission.csv` has shape `(296302, 2)` and columns exactly
      `['id', 'addicted_label']`, matching `sample_submission.csv`.
- [ ] The `id` column is elementwise identical to `sample_submission.csv`'s.
- [ ] The target column has dtype float, zero nulls, and zero non-finite values.
- [ ] **Every target value lies within `[0, 1]`.**
- [ ] **The target column has more than two distinct values** (expect hundreds of
      thousands).
- [ ] The mean prediction falls between 0.60 and 0.80 — near the 0.709 training base rate.
- [ ] `_validate_submission` raises `ValueError` for each of: a 0/1 label column, a value
      above 1, a short frame, and a mismatched ID.
- [ ] Two consecutive `make predict` runs produce byte-identical files.
- [ ] **Two consecutive `make all` runs produce byte-identical `submission.csv`** (matching
      md5) and identical per-fold CV scores.
- [ ] `grep -rn "fit_transform" src/predict.py` finds nothing.
- [ ] `grep -rn "\.predict(" src/predict.py` finds only the regression branch.
- [ ] `grep -rn "print(" src/` finds nothing.
- [ ] `config/default.yaml` still has `round_predictions_to_labels: false`.
- [ ] `git diff --stat Makefile config/default.yaml` is empty.
- [ ] `git check-ignore submissions/submission.csv` exits 0.
- [ ] `tests/test_smoke_pipeline.py`, `config/ci.yaml`, `Dockerfile`, `.dockerignore` were
      **not** created.

## Handoff notes

What phase 06 may assume exists:

- `src/predict.py` exporting `run_predict`, plus the helpers `_fold_model_paths`,
  `_average_folds`, `_blend`, `_clip`, `_as_label_values`, `_validate_submission`, and the
  constant `NO_MODELS_MESSAGE`.
- `src/cli.py` with all three subcommands registered.
- A verified end-to-end path: `make all` produces a valid, deterministic
  `submissions/submission.csv`.
- Real-data numbers for the README: per-model and blend CV scores in
  `reports/metrics.json`, and the measured `runtime_seconds`.

Decisions later phases must stay consistent with:

1. **The submission is built by copying `sample_submission` and overwriting one column.**
   Phase 06's smoke test asserts columns and IDs match the fixture's sample submission
   elementwise, which only holds if this stays true.
2. **`_validate_submission` gates the [0,1] and distinctness checks on `contract.is_binary
   and not round_predictions_to_labels`.** Phase 06 adds a test that sets
   `round_predictions_to_labels: true` and asserts the output contains only the two
   original label values — that test passes precisely because those two checks are gated.
   Do not make them unconditional.
3. **`_as_label_values` thresholds at 0.5 for 1-D input and argmaxes for 2-D.** Phase 06's
   label-branch test exercises the 1-D path.
4. **Clipping applies only to classification when not rounding.** The regression smoke test
   in phase 06 would fail if a continuous target were clipped to [0, 1].
5. **`predict` reads the contract from `models/contract.json`, never from `train.csv`.**
   Phase 06's Docker run and CI smoke run depend on `predict` working with only `test.csv`
   and `sample_submission.csv` present alongside the model artifacts.
6. **`enabled_models(cfg)` is the single source of blend weights**, used identically by
   `train` and `predict`.
7. **Determinism troubleshooting.** If two `make all` runs ever diverge, do **not** start
   rewriting code. The cause is almost always LightGBM thread-count nondeterminism. The
   fix is config-only: add `deterministic: true` and `force_row_wise: true` to the
   `lightgbm` entry's `params` in `config/default.yaml`, or set `runtime.n_jobs` to a fixed
   positive integer instead of `-1`. Both are within the existing schema and add no
   dependency. Record whichever you used in the README's reproducibility section.

Commit before moving on:

```bash
git add -A && git commit -m "phase 05: prediction and submission"
```
