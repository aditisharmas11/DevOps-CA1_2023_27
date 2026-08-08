# Phase 01 — Scaffold and tooling

## Objective

Create the repository skeleton: directory tree, git hygiene, pinned dependencies, ruff
and pytest configuration, the complete `Makefile`, the full `config/default.yaml`, and
`src/config.py` — the one module every later phase imports. This phase exists so that
every subsequent phase can assume a working venv, a passing lint gate, and a validated
config object.

## Preconditions

The workspace contains only:

- `CLAUDE.md`
- `Implementation Plan.md`
- `Startup prompt.md`
- `plans/` (this file and its six siblings, plus `plans/README.md`)
- `data/raw/train.csv`, `data/raw/test.csv`, `data/raw/sample_submission.csv` — already
  downloaded and present, 43 MB / 18 MB / 7.3 MB
- a git repository on branch `main` with **no commits yet**

No `src/`, `tests/`, `config/`, `Makefile`, `requirements.txt` or `.gitignore` exists.

## Context recap

Everything below is needed for this phase. Do not go looking for it elsewhere.

### Tech stack (fixed — CLAUDE.md §3)

Python **3.11**; `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `pyyaml`, `matplotlib`
(no seaborn), `pytest`, `ruff`, plus Docker / GitHub Actions / GNU Make. Excluded and
not to be introduced: seaborn, optuna, xgboost, catboost, torch, mlflow, dvc, hydra,
typer, poetry.

**Interpreter note specific to this machine:** the default `python3` on the developer's
Mac is 3.9.6. `python3.11` exists at `/opt/homebrew/bin/python3.11`. The `Makefile` must
therefore name `python3.11` explicitly when building the venv, never bare `python3`.

### Hardware and runtime (CLAUDE.md §2, §3a)

There is **no wall-clock limit** on the pipeline. The pipeline is CPU-only and
multi-threaded via `runtime.n_jobs`. Apple MPS is unreachable from LightGBM and
scikit-learn and must not be pursued; do not add `torch`.

### Coding conventions (CLAUDE.md §7)

- Line length 100, enforced by ruff.
- Type hints on every public function signature.
- One-line docstring minimum on every module and public function.
- No `print()` in `src/`; use `logging`, configured once in `src/cli.py`. `print()` is
  fine in `scripts/`.
- Paths: always built from config, always `pathlib.Path`, never string concatenation,
  never absolute paths hardcoded.
- Functions do one thing; split anything over ~40 lines.
- Fail loudly and early with `ValueError` / `FileNotFoundError` and a message saying
  what the user should do next.

### Target repository layout (CLAUDE.md §4)

```
smartphone-addiction-s6e8/
├── CLAUDE.md, Implementation Plan.md, README.md, LICENSE
├── Makefile, Dockerfile, .dockerignore, .gitignore
├── requirements.txt, pyproject.toml
├── config/default.yaml
├── plans/
├── src/{__init__,config,contract,data,features,models,metrics,train,predict,cli}.py
├── scripts/{inspect_data,make_eda}.py
├── tests/{fixtures/,test_contract,test_data,test_features,test_metrics,test_smoke_pipeline}.py
├── data/{raw,processed}/          # both gitignored
├── models/                        # gitignored
├── reports/{data_contract.md,metrics.json,figures/}
├── submissions/                   # gitignored except .gitkeep
└── .github/workflows/ci.yml
```

This phase creates the directories and only the files listed in its own table below.

### `src/config.py` specification (Implementation Plan §3.1)

- `load_config(path: Path) -> dict` — reads YAML, validates the required top-level keys
  `project`, `paths`, `contract`, `runtime`, `cv`, `metric`, `features`, `models`,
  `output`, and raises `ValueError` naming the missing key.
- `resolve_paths(cfg: dict, root: Path) -> dict` — converts every value under `paths` to
  an absolute `Path` relative to the repo root.
- `ensure_dirs(cfg: dict) -> None` — `mkdir(parents=True, exist_ok=True)` for every
  output directory (processed, models, reports, figures, submissions).

### Makefile requirements (CLAUDE.md §6, Implementation Plan §5.1)

Targets: `setup inspect eda train predict all test lint fmt docker-build docker-run
clean`. Use `.PHONY`. Use `VENV ?= .venv` and **`PY ?= $(VENV)/bin/python`** — `?=`, not
`:=`, because the Docker image sets `ENV PY=python` and a `:=` assignment would ignore
it. `make clean` removes `models/`, `reports/figures/`, `reports/metrics.json`,
`reports/oof_predictions.csv`, `submissions/*.csv`, `data/processed/*`, and
`__pycache__` — and must **never** touch `data/raw/`, nor delete any `.gitkeep`.

Underlying CLI the Make targets wrap:

```bash
python -m src.cli inspect  --config config/default.yaml
python -m src.cli train    --config config/default.yaml
python -m src.cli predict  --config config/default.yaml
```

### pyproject.toml requirements (Implementation Plan §5.5)

Ruff config only (`line-length = 100`, `select = ["E","F","I","UP","B"]`) plus
`[tool.pytest.ini_options]` with `testpaths = ["tests"]`. **No packaging metadata** —
the project runs via `python -m src.cli` and is not pip-installable.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `.gitignore` | create | Keep data, models, submissions, venv, caches and OS cruft out of git. |
| `requirements.txt` | create | Pinned dependency set. |
| `pyproject.toml` | create | Ruff + pytest configuration. |
| `Makefile` | create | Every target from CLAUDE.md §6. |
| `README.md` | create | Skeleton with the nine section headings from Implementation Plan §6; filled in phase 07. |
| `config/default.yaml` | create | The single source of every knob. |
| `src/__init__.py` | create | Marks `src` as a package. |
| `src/config.py` | create | Config loading, validation, path resolution. |
| `data/raw/.gitkeep` | create | Keep the gitignored directory in the tree. |
| `data/processed/.gitkeep` | create | Same. |
| `models/.gitkeep` | create | Same. |
| `submissions/.gitkeep` | create | Same. |
| `reports/figures/.gitkeep` | create | Same. |
| `scripts/` | create | Empty directory; populated in phases 02 and 07. |
| `tests/fixtures/` | create | Empty directory; populated in phase 02. |

## Detailed steps

### 1. Create the directory tree

```bash
mkdir -p config src scripts tests/fixtures data/raw data/processed models \
         reports/figures submissions .github/workflows
touch data/raw/.gitkeep data/processed/.gitkeep models/.gitkeep \
      submissions/.gitkeep reports/figures/.gitkeep
```

`data/raw/` already holds the three competition CSVs. Do not move, rename or delete
them.

### 2. Write `.gitignore`

```gitignore
# Competition data — never committed (CLAUDE.md §2)
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep

# Trained artifacts
models/*
!models/.gitkeep

# Submissions
submissions/*
!submissions/.gitkeep

# Large generated report — regenerate with `make train`
reports/oof_predictions.csv

# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ruff_cache/
*.egg-info/

# Secrets — CLAUDE.md §2 forbids these in the repo, ever
kaggle.json
.env

# OS
.DS_Store
```

Note what is deliberately **not** ignored: `reports/data_contract.md`,
`reports/metrics.json` and `reports/figures/*.png` are the graded evidence artifacts
(CLAUDE.md §1, "Secondary deliverable") and get committed in phase 07.
`reports/oof_predictions.csv` *is* ignored because on the real data it is ~40 MB.
`tests/fixtures/**/*.csv` are also not ignored — they are tiny synthetic files and must
be committed.

### 3. Write `requirements.txt`

Exactly the pins from Implementation Plan §5.4:

```
pandas~=2.2
numpy~=1.26
scikit-learn~=1.5
lightgbm~=4.5
pyyaml~=6.0
matplotlib~=3.9
joblib~=1.4
pytest~=8.3
ruff~=0.6
```

If any single pin fails to resolve on Python 3.11, relax that one pin and note it in a
comment in the file — do **not** swap the library for another.

### 4. Write `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`select` goes under `[tool.ruff.lint]`, not bare `[tool.ruff]` — the top-level form is
deprecated in ruff 0.6 and emits a warning that would show up in `make lint` output.

### 5. Write the `Makefile`

Recipe lines must be indented with **tabs**, not spaces.

```make
VENV   ?= .venv
PYTHON ?= python3.11
PY     ?= $(VENV)/bin/python
CONFIG ?= config/default.yaml
IMAGE  ?= smartphone-addiction-s6e8

.PHONY: setup inspect eda train predict all test lint fmt docker-build docker-run clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

inspect:
	$(PY) -m src.cli inspect --config $(CONFIG)

eda:
	PYTHONPATH=. $(PY) scripts/make_eda.py --config $(CONFIG)

train:
	$(PY) -m src.cli train --config $(CONFIG)

predict:
	$(PY) -m src.cli predict --config $(CONFIG)

all: inspect train predict

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

fmt:
	$(PY) -m ruff format .

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD)/data:/app/data" \
		-v "$(PWD)/models:/app/models" \
		-v "$(PWD)/reports:/app/reports" \
		-v "$(PWD)/submissions:/app/submissions" \
		$(IMAGE)

clean:
	rm -f models/*.pkl models/*.json
	rm -f reports/figures/*.png
	rm -f reports/metrics.json reports/oof_predictions.csv
	rm -f submissions/*.csv
	find data/processed -type f ! -name '.gitkeep' -delete
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
```

Points to get right:

- `PY ?=` so `ENV PY=python` in the phase-06 Dockerfile wins. An environment variable
  overrides `?=` but not `:=`.
- `$$(id -u)` — doubled `$` so make passes the shell substitution through.
- `clean` uses explicit patterns and a `! -name '.gitkeep'` filter so the placeholder
  files survive; it never mentions `data/raw`.
- `PYTHONPATH=.` on the `eda` recipe. Running `python scripts/make_eda.py` puts
  `scripts/` on `sys.path`, not the repo root, so `import src...` would fail. Setting
  `PYTHONPATH=.` fixes it without `sys.path` manipulation or `# noqa: E402` comments
  inside the scripts. Anything under `scripts/` is run this way — from the repo root,
  with `PYTHONPATH=.` set.
- `make eda`, `make inspect`, `make train`, `make predict`, `make docker-*` reference
  files that do not exist yet. That is expected: they become functional in phases 07,
  02, 04, 05 and 06. Do not create stubs to make them pass early.

### 6. Write `config/default.yaml`

Reproduce this exactly. It is the schema from Implementation Plan §2 with the
competition metadata already filled in.

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
  n_jobs: -1                   # -1 = all cores
  progress: true               # per-fold and per-iteration logging
  log_every_n_iterations: 50   # LightGBM log_evaluation period

cv:
  n_splits: 5
  shuffle: true
  # stratified is used automatically for classification, ignored for regression

metric:
  # Confirmed official metric for S6E8. Do not change.
  # Supported: accuracy | balanced_accuracy | f1_macro | roc_auc | rmse | mae | r2
  # Also accepts: auto
  name: roc_auc
  greater_is_better: true

features:
  numeric_imputation: median
  categorical_imputation: most_frequent
  categorical_encoding: ordinal    # ordinal | onehot
  scale_numeric: false             # tree models don't need it
  max_onehot_cardinality: 15

models:
  # Each entry is trained across all folds; predictions are blended by weight.
  # Sized for accuracy, not speed — there is no time limit.
  - name: lightgbm
    enabled: true
    weight: 0.7
    # Read by src/train.py, not passed to the estimator. null disables early stopping.
    early_stopping_rounds: 100
    params:
      n_estimators: 3000
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
    early_stopping_rounds: null   # hist_gbm early-stops internally, see params
    params:
      max_iter: 1000
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

### 7. Write `src/__init__.py`

A single docstring line:

```python
"""Smartphone addiction (Kaggle Playground S6E8) modelling pipeline."""
```

### 8. Write `src/config.py`

Complete contents:

```python
"""Configuration loading, validation, and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TOP_LEVEL_KEYS = (
    "project",
    "paths",
    "contract",
    "runtime",
    "cv",
    "metric",
    "features",
    "models",
    "output",
)

OUTPUT_DIR_KEYS = (
    "processed_dir",
    "models_dir",
    "reports_dir",
    "figures_dir",
    "submissions_dir",
)


def load_config(path: Path | str, root: Path | None = None) -> dict[str, Any]:
    """Read a YAML config, validate its top-level keys, and resolve its directories."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Missing config file {config_path}. Pass an existing path with --config."
        )
    with config_path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config {config_path} did not parse to a mapping of keys.")
    validate_config(cfg, config_path)
    return resolve_paths(cfg, root if root is not None else PROJECT_ROOT)


def validate_config(cfg: dict[str, Any], source: Path | str = "<config>") -> None:
    """Raise ValueError naming the first required top-level key that is missing."""
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in cfg:
            raise ValueError(f"Config {source} is missing required top-level key '{key}'.")


def resolve_paths(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    """Return a shallow copy of cfg with every paths.*_dir value an absolute Path."""
    resolved = dict(cfg)
    paths = dict(cfg["paths"])
    for key, value in paths.items():
        if key.endswith("_dir"):
            paths[key] = (Path(root) / str(value)).resolve()
    resolved["paths"] = paths
    return resolved


def ensure_dirs(cfg: dict[str, Any]) -> None:
    """Create every output directory named in the config."""
    for key in OUTPUT_DIR_KEYS:
        Path(cfg["paths"][key]).mkdir(parents=True, exist_ok=True)
```

Design points that later phases depend on:

- Only keys ending in `_dir` are turned into `Path`s. The `*_file` keys stay plain
  filename strings and are joined against `raw_dir` at the point of use.
- `raw_dir` is resolved but deliberately **absent from `OUTPUT_DIR_KEYS`**, so
  `ensure_dirs` never creates it. A missing `data/raw/` must surface as the actionable
  `FileNotFoundError` from phase 02's `load_raw`, not be silently papered over.
- `load_config` takes an optional `root`, defaulting to `PROJECT_ROOT`. This is a small
  extension to the Implementation Plan §3.1 signature and exists so phase 06's tests can
  point a `tmp_path`-based config at fixture data. `resolve_paths` stays public and
  separately callable as the plan specifies.

### 9. Write the `README.md` skeleton

Nine headings in the order given by Implementation Plan §6, each with a placeholder
line. Use the literal text `_Filled in Phase 07._` as the placeholder — **not** the word
`TODO`, because CLAUDE.md §9 requires the finished repo to contain no TODOs and phase 07
verifies that with a grep.

```markdown
# smartphone-addiction-s6e8

Reproducible ML pipeline for Kaggle Playground Series S6E8, *Predicting Smartphone
Addiction*. DevOps course continuous assessment.

## Problem statement
_Filled in Phase 07._

## Quickstart
_Filled in Phase 07._

## Project structure
_Filled in Phase 07._

## Pipeline
_Filled in Phase 07._

## Results
_Filled in Phase 07._

## DevOps practices used
_Filled in Phase 07._

## Reproducibility
_Filled in Phase 07._

## Limitations and future work
_Filled in Phase 07._
```

### 10. Build the environment and format

```bash
make setup
make fmt
```

`make fmt` before verifying, so `ruff format --check` in step 11 has nothing to
complain about.

## Verification

Run each of these and show the output.

```bash
# 1. The venv exists and is Python 3.11 — not the system 3.9.
.venv/bin/python --version
# expect: Python 3.11.x

# 2. Dependencies installed, LightGBM imports (it needs libomp on macOS).
.venv/bin/python -c "import pandas, numpy, sklearn, lightgbm, yaml, matplotlib, joblib; print('imports ok')"
# expect: imports ok
# If lightgbm fails with a libomp error, run `brew install libomp` and retry.

# 3. Lint gate is clean.
make lint
# expect: "All checks passed!" from ruff check, and
#         "N files already formatted" from ruff format --check; exit code 0

# 4. Config loads, validates, and resolves paths.
.venv/bin/python -c "
from src.config import load_config
cfg = load_config('config/default.yaml')
print('keys:', sorted(cfg))
print('raw_dir:', cfg['paths']['raw_dir'])
print('n_jobs:', cfg['runtime']['n_jobs'], 'progress:', cfg['runtime']['progress'])
print('target:', cfg['contract']['target_column'], '| metric:', cfg['metric']['name'])
print('round_to_labels:', cfg['output']['round_predictions_to_labels'])
"
# expect keys: ['contract','cv','features','metric','models','output','paths','project','runtime']
# expect raw_dir to be an ABSOLUTE path ending in /data/raw
# expect n_jobs: -1  progress: True
# expect target: addicted_label | metric: roc_auc
# expect round_to_labels: False   <-- must be False, per CLAUDE.md §5a

# 5. Missing-key validation fails loudly.
.venv/bin/python -c "
from src.config import validate_config
try:
    validate_config({'project': {}}, 'x.yaml')
except ValueError as exc:
    print('OK:', exc)
"
# expect: OK: Config x.yaml is missing required top-level key 'paths'.

# 6. ensure_dirs is idempotent and does not create data/raw.
.venv/bin/python -c "
from src.config import load_config, ensure_dirs
cfg = load_config('config/default.yaml')
ensure_dirs(cfg); ensure_dirs(cfg)
print('ensure_dirs ok')
"
# expect: ensure_dirs ok

# 7. The competition CSVs are ignored by git; the tree placeholders are not.
git check-ignore -v data/raw/train.csv data/raw/test.csv data/raw/sample_submission.csv
# expect: three lines, each naming .gitignore — exit code 0
git check-ignore -q data/raw/.gitkeep; echo "gitkeep ignored? exit=$?"
# expect: exit=1  (NOT ignored)

# 8. Nothing under data/raw is staged.
git add -A && git status --porcelain | grep -c '^A.*data/raw/.*\.csv' || echo "0 raw CSVs staged"
# expect: 0 raw CSVs staged

# 9. make clean is safe: it must not remove the competition data.
make clean && ls data/raw/
# expect: sample_submission.csv  test.csv  train.csv  (all three still present)
```

## Definition of done

- [ ] `.venv/bin/python --version` reports 3.11.x.
- [ ] `.venv/bin/python -c "import pandas, numpy, sklearn, lightgbm, yaml, matplotlib, joblib"` exits 0.
- [ ] `make lint` exits 0 with zero findings.
- [ ] `make setup`, `make fmt`, `make clean` all exit 0.
- [ ] These files exist: `.gitignore`, `requirements.txt`, `pyproject.toml`, `Makefile`,
      `README.md`, `config/default.yaml`, `src/__init__.py`, `src/config.py`.
- [ ] These directories exist: `config/`, `src/`, `scripts/`, `tests/fixtures/`,
      `data/raw/`, `data/processed/`, `models/`, `reports/figures/`, `submissions/`,
      `.github/workflows/`.
- [ ] `.gitkeep` exists in `data/raw/`, `data/processed/`, `models/`, `submissions/`,
      `reports/figures/`.
- [ ] `load_config('config/default.yaml')` returns a dict with exactly the nine required
      top-level keys, `paths.raw_dir` an absolute `Path`, and
      `output.round_predictions_to_labels is False`.
- [ ] `validate_config({'project': {}})` raises `ValueError` whose message names
      `'paths'`.
- [ ] `git check-ignore data/raw/train.csv` exits 0.
- [ ] `git check-ignore data/raw/.gitkeep` exits 1.
- [ ] `make clean` leaves all three CSVs in `data/raw/`.
- [ ] `grep -rn "TODO" --include='*.py' --include='*.md' --include='*.yaml' src config README.md` finds nothing.
- [ ] No `src/contract.py`, `src/data.py`, `src/features.py`, `src/models.py`,
      `src/metrics.py`, `src/train.py`, `src/predict.py`, `src/cli.py`, `Dockerfile`, or
      `tests/test_*.py` was created — those belong to later phases.

## Handoff notes

What phase 02 may assume exists:

- A working `.venv` on Python 3.11 with all dependencies importable.
- `config/default.yaml` complete, including the `runtime` block and the confirmed
  contract values `id` / `addicted_label` / `classification`.
- `src/config.py` exporting `PROJECT_ROOT`, `REQUIRED_TOP_LEVEL_KEYS`,
  `OUTPUT_DIR_KEYS`, `load_config`, `validate_config`, `resolve_paths`, `ensure_dirs`.
- `make inspect` already wired to `python -m src.cli inspect --config config/default.yaml`
  — phase 02 creates `src/cli.py`, it does not touch the `Makefile`.
- The three competition CSVs in `data/raw/`, gitignored.

Decisions later phases must stay consistent with:

1. **`PY ?=` not `PY :=`.** Phase 06's Dockerfile sets `ENV PY=python` to run `make all`
   without a venv. Changing this to `:=` silently breaks `make docker-run`.
2. **`PYTHON ?= python3.11`.** Never bare `python3` — this machine's default is 3.9.6.
3. **Only `paths.*_dir` keys become `Path`s.** `paths.train_file` and friends stay
   strings, joined to `raw_dir` by the consumer. Phase 02's `load_raw` relies on this.
4. **`ensure_dirs` does not create `raw_dir`.** Phase 02's missing-file error depends on
   `data/raw/` being left alone.
5. **`load_config(path, root=None)`** — the `root` parameter is how phase 06's tests
   redirect a config at `tmp_path`. Keep it.
6. **`runtime` is a required top-level key.** Every config file created later —
   including phase 06's `config/ci.yaml` and the dicts built by `tests/conftest.py` —
   must include it or `validate_config` will reject them.
7. **`reports/` is committed, `reports/oof_predictions.csv` is not.** Phase 04 writes
   that CSV knowing it is gitignored for size.
8. **The `Makefile` is final.** Later phases add the files its targets call; they do not
   edit the `Makefile` itself.

Commit before moving on:

```bash
git add -A && git commit -m "phase 01: scaffold and tooling"
```
