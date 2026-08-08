# Phase 07 — EDA, docs, and packaging

## Objective

Produce the evidence artifacts and the graded write-up: four EDA figures, the complete
`README.md` filled with real numbers, a `LICENSE`, and instructions for copying the folder
into the college repository. Then run the whole-project acceptance checklist. This is the
phase that turns a working pipeline into a submittable CA.

## Preconditions

Phases 01–06 are complete and committed. `make lint`, `make test` (six test files), `make
all`, `make docker-build` and `make docker-run` all pass. CI is green on the standalone
GitHub repo.

On disk:

- `models/`: `preprocessor.pkl`, `contract.json`, `{lightgbm,hist_gbm}_fold{0..4}.pkl`.
- `reports/metrics.json` with real per-model and blend CV scores and `runtime_seconds`.
- `reports/data_contract.md` from `make inspect`.
- `reports/oof_predictions.csv` (gitignored).
- `submissions/submission.csv` — valid float probabilities.
- `README.md` — the phase 01 skeleton with nine headings, each holding the placeholder
  `_Filled in Phase 07._`.
- `Makefile` with `eda: PYTHONPATH=. $(PY) scripts/make_eda.py --config $(CONFIG)`. **Do not
  edit the Makefile.**

Available in code: all of `src/`, `tests/conftest.py`, `scripts/inspect_data.py`.

Not yet existing: `scripts/make_eda.py`, `LICENSE`.

## Things this phase needs from the operator

Two of the three are already settled — use these values, do not ask again:

1. **Repo: `Faheem219/smartphone-addiction-s6e8`** (confirmed via `git remote -v`). The badge
   URL is
   `https://github.com/Faheem219/smartphone-addiction-s6e8/actions/workflows/ci.yml/badge.svg`.
2. **`LICENSE`: MIT, `Copyright (c) 2026 Faheem219`.**
3. **The public leaderboard score and rank** are *not* available yet — they require
   uploading `submissions/submission.csv` to Kaggle.

> **STOP POINT — confirmed with the operator.** Complete every step of this phase except the
> Kaggle upload and the leaderboard numbers. Write the Results section with the real CV
> figures and an explicit `_pending upload_` marker where the leaderboard score and rank go,
> then **stop and report**. The operator will supply the leaderboard score, rank, and
> anything else from Kaggle afterwards, and the README and any other affected docs get
> updated in a follow-up pass. Do not invent a score, and do not treat the pending marker as
> a reason to leave other sections unfinished.

## Context recap

### `scripts/make_eda.py` specification (Implementation Plan §3.11)

Generates exactly four PNGs into `reports/figures/`, **no more**:

1. `target_distribution.png` — bar chart (classification) or histogram (regression).
2. `missing_values.png` — horizontal bar of null counts per column; if there are no nulls,
   still emit the figure with a "no missing values" annotation.
3. `numeric_correlations.png` — `matplotlib` `imshow` heatmap of the numeric correlation
   matrix, with a colorbar and rotated tick labels.
4. `feature_importance.png` — from the fold-0 LightGBM model if it exists; if not, skip this
   one and log a notice rather than failing.

Use `matplotlib.use("Agg")` so it works headless in CI and Docker. `matplotlib` only — **no
seaborn** (CLAUDE.md §3). `print()` is allowed in `scripts/` (CLAUDE.md §7).

### README specification (Implementation Plan §6) — the README is a graded artifact

It must contain, in order:

1. **Title + one-line description + CI badge.**
2. **Problem statement** — predict the probability that a user is labelled `addicted_label`
   from synthetic tabular smartphone-usage features; link to
   <https://www.kaggle.com/competitions/playground-series-s6e8>; runs 1–31 August 2026 with
   the final submission deadline 31 August 2026 23:59 UTC; scored on ROC AUC against
   predicted probabilities.
3. **Quickstart** — the three commands to get from clone to submission, including where to
   download the data.
4. **Project structure** — annotated tree.
5. **Pipeline description** — the three stages, in prose, with the diagram from
   Implementation Plan §1.
6. **Results** — CV scores per model and blended, filled in from `metrics.json`, plus the
   public leaderboard score and rank once submitted.
7. **DevOps practices used** — an explicit section mapping each practice to where it lives:
   version control hygiene (`.gitignore`, no data in git), dependency pinning,
   linting/formatting, unit + smoke testing, CI on every push, containerisation, build
   automation via Make, reproducibility via seeding and config, artifact management. **This
   section is what earns the CA marks — make it concrete, referencing real file paths.**
8. **Reproducibility notes** — seed, determinism guarantee, Docker instructions.
9. **Limitations and future work** — three or four honest bullets.

### The pipeline diagram to reproduce in the README (Implementation Plan §1)

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

Correct `models/fold_*.pkl` to the pattern actually implemented,
`models/{model_name}_fold{k}.pkl` — Implementation Plan §3.7 specifies it and phase 04 built
it that way.

### Facts the README must state, and which are easy to get wrong

- **The submission holds probabilities, not labels** (CLAUDE.md §5a). Say so, and say why: a
  file of 0s and 1s uploads cleanly and scores far worse, because ROC AUC needs the ranking
  information thresholding destroys.
- **The preprocessor is fitted once on the full training set** and reused across folds —
  imputation and ordinal encoding are low-leakage. Implementation Plan §3.4 requires this
  choice to be documented in the README.
- **Early stopping makes reported CV mildly optimistic.** LightGBM's stopping iteration is
  chosen on the same fold used to compute that fold's OOF score. It is on because it prevents
  overfitting 3000 trees; `early_stopping_rounds: null` removes the effect. This must appear
  in Results or Limitations, not be quietly dropped.
- **There is no runtime budget** (CLAUDE.md §2). Quote the measured `runtime_seconds` from
  `metrics.json` instead of a limit.
- **Apple MPS is not usable and the pipeline is CPU-only** (CLAUDE.md §3a). LightGBM and
  scikit-learn have no Metal path; LightGBM's GPU support is OpenCL/CUDA only and the PyPI
  wheel is CPU-only; reaching MPS would require `torch` plus a neural net, both excluded. At
  ~691k rows × 12 features a GPU would not help anyway. State this in Reproducibility or
  Limitations so the choice reads as deliberate rather than as an oversight.
- **Class balance is 70.9 % positive and no resampling was applied** — ROC AUC is
  threshold-free (CLAUDE.md §10, Implementation Plan §9).
- **Mild imbalance, `n_splits: 5`, `seed: 42`** — all config-driven, nothing hardcoded.

### The packaging note (Implementation Plan §0.1) — do not soften this

> GitHub Actions only executes workflows located at `.github/workflows/` in the
> **repository root**. Once this project is copied into the college repo as a subfolder, its
> CI will *not* run there. Therefore the standalone repo is the canonical one — CI runs
> there, and that is where the green build badge and Actions screenshots come from. The
> college repo receives a copy.

The CA table the college asks for (Implementation Plan §0.1):

| Field | Value |
|---|---|
| Problem Statement with online link | https://www.kaggle.com/competitions/playground-series-s6e8 |
| Submission date | 31 August 2026 (final submission deadline, 23:59 UTC) |
| Issue Repository | the standalone GitHub repo for this project |
| Github name/email id | the student's GitHub handle and email |
| Github assigned repo | the path of this project's folder inside the college repo |

### Whole-project definition of done (CLAUDE.md §9) — checked here

- `make lint` passes with zero findings.
- `make test` passes; all tests run on committed fixtures with no real data present.
- `make all` runs end-to-end on real data and writes `submissions/submission.csv`; the
  measured wall-clock time is recorded in `reports/metrics.json` and quoted in the README.
- Long stages emit continuous progress output per §7a.
- `submission.csv` has exactly the same shape, column names and ID values as
  `data/raw/sample_submission.csv`, with no nulls.
- Two consecutive `make all` runs produce identical `submission.csv`.
- `reports/metrics.json` contains per-fold and mean CV scores.
- `make docker-build && make docker-run` reproduces the same result.
- GitHub Actions CI is green on push.
- `README.md` documents setup, usage, results and the DevOps practices used.
- No leftover TODOs, no stub functions, no commented-out code.

### Non-goals reminder (Implementation Plan §9)

No hyperparameter search, no stacking, no neural nets, no web interface, no experiment
tracker, no Kubernetes/Terraform/Helm, no multi-stage Docker, no automatic Kaggle API
submission, no pre-commit hooks, no resampling, no probability calibration, no support for
other competitions. Phase 07 writes documentation and figures — it does not add features.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `scripts/make_eda.py` | create | Generate exactly four PNGs into `reports/figures/`. |
| `reports/figures/target_distribution.png` | create (generated) | Class balance. |
| `reports/figures/missing_values.png` | create (generated) | Null counts per column. |
| `reports/figures/numeric_correlations.png` | create (generated) | Numeric correlation heatmap. |
| `reports/figures/feature_importance.png` | create (generated) | Fold-0 LightGBM importances. |
| `README.md` | modify | Replace all nine placeholders with the real write-up. |
| `LICENSE` | create | MIT, with the confirmed name and year. |

## Detailed steps

### 1. Write `scripts/make_eda.py`

```python
"""Generate the four EDA figures into reports/figures/."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow matplotlib.use)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.cli import configure_logging  # noqa: E402
from src.config import ensure_dirs, load_config  # noqa: E402
from src.contract import DataContract, derive_contract  # noqa: E402
from src.data import load_raw  # noqa: E402

LOGGER = logging.getLogger("scripts.make_eda")
FIGURE_SIZE = (9, 6)
DPI = 120
```

`matplotlib.use("Agg")` must run before `pyplot` is imported, which forces imports after it
and needs `# noqa: E402` on each — ruff's `E402` would otherwise fail the lint gate. This is
the one place in the project where that comment is justified; add a one-line comment saying
so.

Four figure functions, each taking what it needs and returning the written `Path`:

**`_plot_target_distribution(train, contract, figures_dir) -> Path`**
Classification: `train[target].value_counts().sort_index()` as a bar chart, each bar
annotated with its count and percentage. Regression: a 50-bin histogram. Title names the
target column. Save as `target_distribution.png`.

**`_plot_missing_values(train, figures_dir) -> Path`**
`train.isna().sum()`, filtered to non-zero, sorted ascending, as `barh`. If nothing is
missing, still create the figure and annotate it with "no missing values" centred in the
axes — Implementation Plan §3.11 requires the file either way. Save as
`missing_values.png`.

**`_plot_numeric_correlations(train, contract, figures_dir) -> Path`**
`train[contract.numeric_features].corr()` rendered with `imshow`, `cmap="coolwarm"`,
`vmin=-1`, `vmax=1`. Add `fig.colorbar(...)`, set both tick sets to the column names, and
rotate the x labels 45° with `ha="right"`. Save as `numeric_correlations.png`.

**`_plot_feature_importance(models_dir, contract, cfg, figures_dir) -> Path | None`**
Load `models_dir / "lightgbm_fold0.pkl"`. If it is absent, log
`"models/lightgbm_fold0.pkl not found; skipping feature_importance.png — run `make train` first"`
and return `None` — do not fail. Otherwise take `model.feature_importances_` and pair it with
names:

```python
names: list[str] = []
preprocessor_path = models_dir / "preprocessor.pkl"
if preprocessor_path.is_file():
    names = list(load_preprocessor(preprocessor_path).get_feature_names_out())
if len(names) != len(importances):
    names = [f"f{index}" for index in range(len(importances))]
```

**Take the names from the persisted preprocessor, not from `contract.feature_columns`.** The
transformed matrix is wider than the contract's feature list: `features.add_missing_indicators`
is true, so the real data yields 21 columns from 12 features — 9 imputed numeric, 9
`missingindicator_*` columns, 3 ordinal categoricals. `get_feature_names_out()` returns exactly
those 21 names in order (verified in phase 03), which makes the plot readable and, incidentally,
shows how much signal the missingness itself carries. The length check is the fallback for a
config where the widths still disagree — generic names beat mislabelled ones. Sort ascending,
plot `barh`, save as `feature_importance.png`.

Import `load_preprocessor` from `src.features` for this.

**`main() -> int`**
Parse `--config` (default `config/default.yaml`) and `--log-level` (default `INFO`);
`configure_logging`; `load_config`; `ensure_dirs`; `load_raw`; `derive_contract`; call the
four plotters; `print()` each path written; return 0. Wrap the body in
`except (FileNotFoundError, ValueError, KeyError) as exc` printing `f"error: {exc}"` to
`stderr` and returning 1, mirroring `scripts/inspect_data.py`.

Close every figure with `plt.close(fig)` after saving, or a long session leaks them.

Then:

```bash
make eda
```

### 2. Write `LICENSE`

Standard MIT text, `Copyright (c) 2026 <confirmed name>`. No modifications to the licence
body.

### 3. Rewrite `README.md`

Replace every `_Filled in Phase 07._` placeholder. Content requirements per section:

**1 — Title, description, badge.** Title, a one-line description, and:

```markdown
[![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/<repo>/actions/workflows/ci.yml)
```

**2 — Problem statement.** The competition link, the 1–31 August 2026 window with the
31 August 2026 23:59 UTC deadline, binary classification on synthetic tabular
smartphone-usage features, target `addicted_label`, ID `id`, metric ROC AUC **against
predicted probabilities**. State the dataset shape measured in phase 02: 691,369 train rows,
296,302 test rows, 12 features (9 numeric, 3 categorical), 70.9 % positive class. Include a
short callout that the submission column is a float probability and that writing 0/1 labels
scores far worse.

**3 — Quickstart.**

```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
make setup
# Download train.csv, test.csv and sample_submission.csv from
# https://www.kaggle.com/competitions/playground-series-s6e8/data
# and place them in data/raw/
make all
```

Note that `make setup` needs Python 3.11 available as `python3.11`, and that
`submissions/submission.csv` is the file to upload. Mention the expected wall-clock time from
`metrics.json`.

**4 — Project structure.** The annotated tree from CLAUDE.md §4, updated to what actually
exists: include `config/ci.yaml`, `tests/test_models.py`, `tests/conftest.py`,
`tests/fixtures/make_fixtures.py`, and `reports/oof_predictions.csv`; drop anything that was
never built. Annotate each entry with one clause.

**5 — Pipeline.** The three stages in prose plus the corrected diagram from the Context
recap. Explain in this section:
- the contract is derived at runtime from `sample_submission.csv` and the target dtype, with
  config as an override, so no column name is hardcoded in `src/` (CLAUDE.md §5);
- the preprocessor is fitted once on the full training set and reused across folds, because
  median imputation and ordinal encoding are low-leakage — the choice Implementation Plan
  §3.4 asks to be documented here;
- fold averaging: K models per algorithm, their test probabilities averaged, then the two
  algorithms blended 0.7 / 0.3;
- probabilities end to end — `predict_proba(X)[:, 1]` for OOF and for test, averaging
  probabilities never labels, and a float column in the submission.

**6 — Results.** A table filled from `reports/metrics.json`: per-model per-fold scores, mean
± std, and the blended OOF score. Quote `runtime_seconds`. Add the LightGBM early-stopping
caveat — reported CV is mildly optimistic because the stopping iteration is chosen on the
same fold that scores it; `early_stopping_rounds: null` removes the effect. Then the public
leaderboard score and rank, or an explicit `_pending upload_` marker if the submission has not
been made yet. Reference the four figures with relative image links.

**7 — DevOps practices used.** The marks live here. One row or bullet per practice, each
naming a real path:

| Practice | Where it lives |
|---|---|
| Version-control hygiene | `.gitignore` — `data/raw/*.csv`, `models/`, `submissions/*.csv` and `reports/oof_predictions.csv` are excluded; `.gitkeep` files preserve the tree |
| Dependency pinning | `requirements.txt`, minor-version pins |
| Lint and format gate | `ruff` via `pyproject.toml`, run by `make lint` and CI |
| Unit tests | `tests/test_contract.py`, `test_data.py`, `test_features.py`, `test_models.py`, `test_metrics.py` |
| End-to-end smoke test | `tests/test_smoke_pipeline.py` on committed fixtures — no real data needed |
| Test fixtures as code | `tests/fixtures/make_fixtures.py`, deterministic and regenerable |
| CI on every push | `.github/workflows/ci.yml` — lint, format, tests, a fixture pipeline run, artifact upload, and a Docker build job |
| Containerisation | `Dockerfile`, `.dockerignore`; `make docker-build` / `make docker-run` |
| Build automation | `Makefile` — every workflow is one target |
| Configuration as data | `config/default.yaml`, `config/ci.yaml`; no magic numbers in `src/` |
| Reproducibility | `project.seed: 42` threaded through the splitter and every estimator; two runs byte-identical |
| Artifact management | `reports/metrics.json`, `reports/data_contract.md`, `reports/figures/*.png` committed; CI uploads them per run |
| Observability | structured `logging` with per-fold progress and ETA (CLAUDE.md §7a); no `print()` in `src/` |

**8 — Reproducibility.** `seed: 42`; what determinism is guaranteed (two consecutive `make
all` runs give byte-identical `submission.csv`) and how it is verified; any thread pin applied
in phase 06 step 14; Docker instructions including that `make docker-run` bind-mounts `data/`,
`models/`, `reports/` and `submissions/` and passes `--user` so the container writes as the
host user; and the CPU-only / no-MPS explanation from CLAUDE.md §3a.

**9 — Limitations and future work.** Three or four honest bullets. Reasonable candidates: the
early-stopping optimism in reported CV; only two model families with fixed hyperparameters,
since hyperparameter search is out of scope; no external data, though the competition offers
an original source dataset; the preprocessor is fitted on full train rather than per fold, a
deliberate small-leakage trade; CPU-only, and a GPU path would need a different library.

Also add a short **Packaging for the college repository** section:

```bash
rsync -av --exclude '.git' --exclude '.venv' --exclude 'data' \
          --exclude 'models' --exclude 'submissions' --exclude '__pycache__' \
          ./ <college-repo>/smartphone-addiction-s6e8/
```

State plainly that the copied folder's `.github/workflows/ci.yml` will **not** run in the
college repo, because Actions only executes workflows at the repository root, and that the
standalone repo is therefore the canonical one for the green badge and Actions screenshots.
Include the CA table with the five fields filled in.

### 4. Commit the evidence artifacts

`reports/data_contract.md`, `reports/metrics.json` and `reports/figures/*.png` are the
secondary deliverable (CLAUDE.md §1) and phase 01's `.gitignore` allows them.
`reports/oof_predictions.csv` stays out — it is ~40 MB.

Note for later: `make clean` deletes the committed figures and `metrics.json`. That is
intended — restore them with `git checkout reports/`.

### 5. Run the whole-project acceptance checklist

Every item from CLAUDE.md §9, in one pass. See Verification.

## Verification

```bash
# 1. Lint and tests.
make lint && make test
# expect: both exit 0

# 2. Exactly four figures, no more (Implementation Plan §3.11).
make eda
ls -1 reports/figures/*.png
ls -1 reports/figures/*.png | wc -l
# expect: feature_importance.png, missing_values.png, numeric_correlations.png,
#         target_distribution.png  — and exactly 4

# 3. Every figure is a valid, non-trivial PNG.
.venv/bin/python -c "
from pathlib import Path
for path in sorted(Path('reports/figures').glob('*.png')):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    assert len(data) > 5000, (path, len(data))
    print(f'{path.name:28s} {len(data):>8,} bytes  OK')
"
# expect: four OK lines

# 4. EDA is headless-safe and degrades gracefully without models.
mv models /tmp/models-backup
make eda 2>&1 | tail -5
ls -1 reports/figures/*.png | wc -l
mv /tmp/models-backup models
# expect: a notice that lightgbm_fold0.pkl was not found and the figure was skipped,
#         exit 0, and the other three PNGs still present — no traceback

# 5. No seaborn, no excluded dependency.
grep -rniE "seaborn|torch|optuna|xgboost|catboost|mlflow|dvc" src/ scripts/ requirements.txt || echo "OK: no excluded dependency"
# expect: OK: no excluded dependency

# 6. README has all nine sections and no placeholders left.
grep -n "^#\{1,2\} " README.md
grep -c "_Filled in Phase 07._" README.md
# expect: the nine section headings plus the packaging section; placeholder count 0

# 7. No TODOs, stubs, or commented-out code anywhere (CLAUDE.md §9).
grep -rn "TODO\|FIXME\|XXX" --include='*.py' --include='*.md' --include='*.yaml' --include='*.yml' --include='Makefile' --include='Dockerfile' . | grep -v '^./plans/' || echo "OK: no TODO/FIXME/XXX"
grep -rn "pass$\|NotImplementedError\|^\s*#\s*[a-z_]\+(" src/ scripts/ || echo "OK: no stubs or commented-out code"
# expect: both OK lines

# 8. The README's real numbers match metrics.json rather than being invented.
.venv/bin/python -c "
import json
m = json.load(open('reports/metrics.json'))
print('metric        :', m['metric'])
print('per-model mean:', {k: round(v['mean'], 5) for k, v in m['per_model'].items()})
print('blend score   :', round(m['blend']['score'], 5))
print('runtime (s)   :', round(m['runtime_seconds'], 1))
print()
print('Cross-check every one of these against the README Results table.')
"
# expect: values printed; verify each appears in README.md

# 9. The CI badge points at a real workflow on the real repo.
grep -n "actions/workflows/ci.yml/badge.svg" README.md
git remote -v
# expect: the badge URL's <owner>/<repo> matches the origin remote

# 10. LICENSE exists and names a real year and holder.
head -3 LICENSE
# expect: MIT License, then a Copyright (c) 2026 <name> line

# 11. ACCEPTANCE — full pipeline, twice, byte-identical (CLAUDE.md §9).
make clean
time make all 2>&1 | tee /tmp/accept-run1.log
cp submissions/submission.csv /tmp/accept-1.csv
time make all 2>&1 | tee /tmp/accept-run2.log
cmp /tmp/accept-1.csv submissions/submission.csv && echo "ACCEPT: two make all runs are byte-identical"
# expect: cmp silent, then the ACCEPT line

# 12. ACCEPTANCE — the submission matches the sample submission exactly and holds
#     probabilities (CLAUDE.md §5a, §9).
.venv/bin/python -c "
import numpy as np, pandas as pd
sub = pd.read_csv('submissions/submission.csv')
sample = pd.read_csv('data/raw/sample_submission.csv')
t = sample.columns[1]
checks = {
    'shape matches':        sub.shape == sample.shape,
    'columns match':        list(sub.columns) == list(sample.columns),
    'ids match':            (sub[sample.columns[0]].to_numpy() == sample[sample.columns[0]].to_numpy()).all(),
    'no nulls':             bool(sub[t].notna().all()),
    'all finite':           bool(np.isfinite(sub[t].to_numpy()).all()),
    'dtype is float':       sub[t].dtype.kind == 'f',
    'within [0,1]':         bool(sub[t].between(0, 1).all()),
    'more than 2 distinct': sub[t].nunique() > 2,
}
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL'), name)
assert all(checks.values())
print()
print('ACCEPT: submission is valid —', sub.shape[0], 'rows,', sub[t].nunique(), 'distinct probabilities')
"
# expect: eight PASS lines then the ACCEPT line

# 13. ACCEPTANCE — Docker reproduces it.
make docker-build && make docker-run
cmp /tmp/accept-1.csv submissions/submission.csv && echo "ACCEPT: Docker reproduces the host submission"
# expect: the ACCEPT line (or a documented float-noise difference per phase 06 step 14)

# 14. ACCEPTANCE — tests pass with no real data present.
mv data/raw /tmp/raw-backup && mkdir -p data/raw && touch data/raw/.gitkeep
make test; echo "exit=$?"
rm -rf data/raw && mv /tmp/raw-backup data/raw
# expect: 0 failures, exit=0

# 15. ACCEPTANCE — no data or artifacts tracked by git.
git ls-files | grep -E '^data/raw/.*\.csv$' || echo "ACCEPT: no competition CSVs tracked"
git ls-files | grep -E '^(models|submissions)/' | grep -v '\.gitkeep$' || echo "ACCEPT: no artifacts tracked"
git ls-files reports/
# expect: two ACCEPT lines; reports/ lists data_contract.md, metrics.json and four PNGs,
#         and NOT oof_predictions.csv

# 16. ACCEPTANCE — evidence artifacts are committed.
git status --porcelain reports/
# expect: no output — everything under reports/ that should be tracked is committed

# 17. ACCEPTANCE — CI green on the standalone repo.
git add -A && git commit -m "phase 07: EDA, docs, and packaging" && git push
gh run watch
# expect: both build and docker jobs green

# 18. The college-repo copy is clean.
rm -rf /tmp/college-copy && mkdir -p /tmp/college-copy
rsync -a --exclude '.git' --exclude '.venv' --exclude 'data' --exclude 'models' \
         --exclude 'submissions' --exclude '__pycache__' ./ /tmp/college-copy/smartphone-addiction-s6e8/
du -sh /tmp/college-copy/smartphone-addiction-s6e8
find /tmp/college-copy -name '*.csv' | grep -v fixtures || echo "ACCEPT: no competition data in the copy"
ls /tmp/college-copy/smartphone-addiction-s6e8
# expect: a small folder, only fixture CSVs, the ACCEPT line, and the full source tree
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0 with six test files, including with `data/raw/` emptied.
- [ ] `scripts/make_eda.py` exists; `make eda` exits 0.
- [ ] `reports/figures/` contains **exactly four** PNGs:
      `target_distribution.png`, `missing_values.png`, `numeric_correlations.png`,
      `feature_importance.png`. Each has a valid PNG magic header and exceeds 5 KB.
- [ ] `make eda` with `models/` absent still exits 0, writes the other three figures, and
      logs a skip notice for the importance plot — no traceback.
- [ ] `grep -rniE "seaborn|torch|optuna|xgboost|catboost|mlflow|dvc" src/ scripts/
      requirements.txt` finds nothing.
- [ ] `LICENSE` exists with a real year and copyright holder.
- [ ] `README.md` contains all nine specified sections in order, plus a
      "Packaging for the college repository" section, and **zero** occurrences of
      `_Filled in Phase 07._`.
- [ ] The README's Results table numbers match `reports/metrics.json` exactly (per-model
      folds, mean ± std, blend score, `runtime_seconds`).
- [ ] The README states: the submission holds probabilities and why; the preprocessor is
      fitted once on full train; the early-stopping CV-optimism caveat; that there is no
      runtime budget and what the measured runtime was; that the pipeline is CPU-only and
      Apple MPS is unreachable; that class imbalance was recorded and deliberately not
      resampled.
- [ ] The README's DevOps section names at least the thirteen practices listed above, each
      with a real file path.
- [ ] The CI badge URL's `<owner>/<repo>` matches `git remote -v`.
- [ ] The README states that CI does not run from the college-repo copy and that the
      standalone repo is canonical.
- [ ] The CA table is present with all five fields filled.
- [ ] `grep -rn "TODO\|FIXME\|XXX"` over tracked source, config and docs (excluding
      `plans/`) finds nothing.
- [ ] No stub functions, no `NotImplementedError`, no commented-out code in `src/` or
      `scripts/`.
- [ ] Two consecutive `make all` runs produce byte-identical `submission.csv`.
- [ ] `submission.csv` passes all eight acceptance checks: shape, columns, IDs, no nulls,
      all finite, float dtype, within `[0, 1]`, more than two distinct values.
- [ ] `make docker-build && make docker-run` reproduces the same submission (or the
      difference is quantified as float noise and documented).
- [ ] `git ls-files` shows no `data/raw/*.csv` and nothing under `models/` or `submissions/`
      besides `.gitkeep`.
- [ ] `git ls-files reports/` lists `data_contract.md`, `metrics.json` and the four PNGs, and
      **not** `oof_predictions.csv`.
- [ ] `git status --porcelain reports/` is empty.
- [ ] CI is green on both jobs after the final push.
- [ ] The `rsync` college-repo copy contains no competition CSVs and the full source tree.

## Handoff notes

The project is complete at the end of this phase. Two things remain outside the
repository's control and are the operator's to do:

1. **Upload `submissions/submission.csv` to Kaggle**, then fill the leaderboard score and
   rank into the README's Results section and re-commit. Until then that line carries an
   explicit pending marker — do not invent a number.
2. **Copy the folder into the college repository** with the `rsync` command above, and fill
   the CA table's "Github assigned repo" field with the folder's path inside that repo.

Standing facts worth remembering for any later edit:

- `make clean` deletes `reports/figures/*.png` and `reports/metrics.json`, which are tracked.
  Restore with `git checkout reports/`. This is a deliberate trade: `make clean` is defined
  by Implementation Plan §5.1 to remove generated artifacts, and those files are both
  generated *and* graded evidence.
- Regenerating figures or metrics produces a git diff. Re-commit deliberately rather than
  letting `make all` churn tracked files unnoticed.
- The seed lives in `config/default.yaml` as `project.seed`. Changing it changes every
  reported number in the README.
- If the leaderboard score comes in far below the reported CV, the first thing to check is
  that the uploaded file was the float-probability `submission.csv` and not a
  post-processed copy.
