# Phase 06 — Tests, CI, and Docker

## Objective

Close the DevOps loop: an end-to-end smoke test that runs the whole pipeline on committed
fixtures, a CI configuration that reproduces it in a clean environment, and a container
image that reproduces it again. For a DevOps CA this is the highest-value phase — CLAUDE.md
§1 says the scaffolding matters as much as the model.

## Preconditions

Phases 01–05 are complete and committed. `make lint` and `make test` pass with five test
files. `make all` produces a valid, deterministic `submissions/submission.csv` on the real
data.

Available in code:

- `src/config.py`, `src/contract.py`, `src/data.py`, `src/features.py`, `src/models.py`,
  `src/metrics.py`, `src/train.py`, `src/predict.py`, `src/cli.py` — all three subcommands
  registered.
- `tests/conftest.py`: `FIXTURES_DIR`, `DEFAULT_CONFIG_PATH`, `TINY_MODELS`,
  `make_config(tmp_path, fixture, **overrides)` — which already nulls the contract, sets
  `runtime = {"n_jobs": 1, "progress": False, "log_every_n_iterations": 0}`,
  `cv.n_splits = 2`, `metric = {"name": "auto", "greater_is_better": None}`, and
  `models = TINY_MODELS`.
- `tests/fixtures/clf/` and `tests/fixtures/reg/`, committed.
- `tests/test_contract.py`, `test_data.py`, `test_features.py`, `test_models.py`,
  `test_metrics.py` — all passing.
- `Makefile` with `docker-build` and `docker-run` already defined. **Do not edit the
  Makefile.**
- `.github/workflows/` exists but is empty.
- Docker installed and running on the host.

**Remote.** Already configured as
`origin git@github.com:Faheem219/smartphone-addiction-s6e8.git`, so the "CI green after
push" item is actionable in this phase. Confirm with `git remote -v` before relying on it.

## Context recap

### `Makefile` facts this phase depends on

Phase 01 wrote the Makefile with `PY ?= $(VENV)/bin/python` — deliberately `?=`, not `:=`,
**so the Docker image can override it with `ENV PY=python`**. A `:=` would ignore the
environment variable and `make all` inside the container would look for a `.venv` that does
not exist.

`make docker-run` is already written as:

```make
docker-run:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		-v "$(PWD)/data:/app/data" \
		-v "$(PWD)/models:/app/models" \
		-v "$(PWD)/reports:/app/reports" \
		-v "$(PWD)/submissions:/app/submissions" \
		$(IMAGE)
```

Four bind mounts and `--user`, because the image's non-root user has a different uid from
the host user that owns those directories; without `--user` the container cannot write into
them and the run dies on the first artifact.

### `Dockerfile` specification (Implementation Plan §5.2)

- Base `python:3.11-slim`.
- Set `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` (the latter is what makes the §7a
  progress output stream rather than sit in a buffer), and `PY=python` so the Makefile's
  `PY ?=` resolves to the system interpreter.
- Install `libgomp1` **and `make`** via apt, then clean apt lists. LightGBM needs
  `libgomp1`; `make` is not present in `python:3.11-slim` and the default
  `CMD ["make", "all"]` cannot work without it.
- Copy `requirements.txt` first, `pip install --no-cache-dir -r requirements.txt`, then copy
  the rest — so the dependency layer caches.
- Create and use a non-root user.
- `WORKDIR /app`. Default `CMD ["make", "all"]`.
- `.dockerignore` must exclude `data/`, `models/`, `submissions/`, `.venv`, `.git`,
  `reports/figures`, `__pycache__`.
- **No multi-stage builds and no image size optimisation** — Implementation Plan §9 lists
  both as non-goals.

### `.github/workflows/ci.yml` specification (Implementation Plan §5.3)

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
   `submissions/submission.csv` exists.
8. Upload `reports/metrics.json` and `submissions/submission.csv` as artifacts.

A second job, `docker`, runs `docker build .` to verify the image still builds.

**Packaging note (Implementation Plan §0.1):** GitHub Actions only executes workflows at
`.github/workflows/` in the **repository root**. Once this project is copied into the
college repo as a subfolder, its CI will not run there. The standalone repo is the canonical
one — CI runs there, and that is where the green badge and Actions screenshots come from.
Phase 07 handles the copy.

### `config/ci.yaml` specification (Implementation Plan §5.3)

A copy of default with `n_splits: 2` and small model params, pointing at `data/raw` as
usual. **Three overrides are mandatory, not optional:**

- `contract.id_column`, `contract.target_column` and `contract.task_type` must all be
  `null`. The smoke run copies `tests/fixtures/clf/*` into `data/raw/`, and those fixtures
  use the target name `target` — the confirmed S6E8 value `addicted_label` would make the
  run fail on a column that does not exist. Auto-detection handles it.
- `runtime.progress: false`, so CI logs stay readable.
- `features.add_missing_indicators` must be present. Phase 03 added the key and
  `_numeric_pipeline` reads it unconditionally, so a `ci.yaml` copied from the
  pre-phase-03 schema raises `KeyError` on the first fit. `validate_config` only checks
  *top-level* keys, so it will not catch this for you.
- Model params must be tiny (`n_estimators: 20`, `max_iter: 20`,
  `early_stopping_rounds: null`, `early_stopping: false`); the production values would take
  far longer than a CI job should.

### Test specification (Implementation Plan §4.2)

`test_smoke_pipeline.py` — the important one. Using `tmp_path` and a config that points at
the clf fixtures with `n_splits: 2` and tiny model params, run `run_train` then
`run_predict`, and assert:

- `submission.csv` exists
- its shape and column names equal the fixture's `sample_submission.csv`
- its ID column matches the fixture's elementwise
- it has zero nulls
- **the target column is float, lies within [0, 1], and has more than two distinct values**
  — the regression guard against writing labels instead of probabilities
- `metrics.json` exists, `metrics.metric == "roc_auc"`, and `blend.score` is a finite float
  in [0, 1]
- running the pair twice yields byte-identical submission files (determinism)

Repeat the core of this for the regression fixture, and add one test that sets
`round_predictions_to_labels: true` on the clf fixture and asserts the output then contains
only the two original label values — this covers the branch that S6E8 itself does not use.

All tests must pass **without any real competition data present**.

### The probability rule, one last time (CLAUDE.md §5a)

The smoke test's `nunique() > 2` assertion is the automated form of the §5a guard. If it
ever fails, the cause is `predict()` where `predict_proba()[:, 1]` belongs — fix the code,
never the assertion.

### Relevant behaviour carried in from phase 05

`_validate_submission` gates the `[0, 1]` and distinctness checks on `contract.is_binary and
not round_predictions_to_labels`. That gating is what lets the label-branch test and the
regression smoke test pass. Do not make those checks unconditional.

## Files to create or modify

| Path | Action | Purpose |
|---|---|---|
| `tests/test_smoke_pipeline.py` | create | End-to-end train→predict on both fixture sets, plus determinism and the label branch. |
| `config/ci.yaml` | create | Fast, fixture-compatible config for CI. |
| `.github/workflows/ci.yml` | create | Lint, format, tests, fixture smoke run, artifacts, Docker build. |
| `Dockerfile` | create | Reproducible container image. |
| `.dockerignore` | create | Keep data, artifacts, venv and git history out of the build context. |

## Detailed steps

### 1. Write `tests/test_smoke_pipeline.py`

Import `run_train` from `src.train`, `run_predict` from `src.predict`, and `make_config`
from `conftest`. Each test builds its own `tmp_path` config, so tests are independent.

| Test | Asserts |
|---|---|
| `test_clf_smoke_writes_probability_submission` | `run_train` then `run_predict` on `clf`: the returned path exists; `sub.shape == sample.shape`; `list(sub.columns) == list(sample.columns)`; the ID column matches `sample_submission.csv` elementwise; zero nulls; `dtype.kind == "f"`; every value in `[0, 1]`; **`nunique() > 2`**. |
| `test_clf_smoke_metrics_json` | `reports/metrics.json` exists under `tmp_path`; `metric == "roc_auc"`; `greater_is_better is True`; `task_type == "classification"`; `n_splits == 2`; each model has 2 per-fold scores; `blend.score` is a finite float in `[0, 1]`; `blend.weights` sums to 1. |
| `test_clf_smoke_writes_expected_artifacts` | `models/` under `tmp_path` contains `preprocessor.pkl`, `contract.json`, and `{lightgbm,hist_gbm}_fold{0,1}.pkl`; `reports/oof_predictions.csv` exists with 60 rows. |
| `test_clf_smoke_is_deterministic` | Run the `run_train`/`run_predict` pair twice against the same config; the submission file's bytes are identical (`read_bytes()` equality). |
| `test_reg_smoke_writes_continuous_submission` | Same pipeline on `reg`: shape, columns and IDs match the fixture's sample submission; zero nulls; all values finite; `metrics.metric == "rmse"`; `greater_is_better is False`; `blend.score` is a finite positive float. Explicitly do **not** assert a `[0, 1]` range. |
| `test_round_predictions_to_labels_writes_labels` | `make_config(tmp_path, "clf", output={"round_predictions_to_labels": True})`: after train+predict, `set(sub[target].unique()).issubset({0, 1})` and `sub[target].nunique() <= 2`. This is the branch S6E8 does not use. |
| `test_predict_without_models_raises` | `run_predict` on a fresh config with no prior `run_train` raises `FileNotFoundError` whose message contains ``Run `make train` first.`` |
| `test_oof_predictions_are_probabilities` | `reports/oof_predictions.csv` from the clf run: `oof_blend` lies in `[0, 1]` and has more than two distinct values. |

Two notes on writing these:

- The fixture sample submission is at `FIXTURES_DIR / "clf" / "sample_submission.csv"`; read
  it directly rather than reconstructing it.
- `make_config` already sets `n_splits: 2` and `TINY_MODELS`, so no test needs to pass model
  overrides. The only override any test needs is `output={"round_predictions_to_labels":
  True}`.

### 2. Write `config/ci.yaml`

Complete contents:

```yaml
# CI configuration: same pipeline, tiny budget, fixture-compatible contract.
# Used by .github/workflows/ci.yml after copying tests/fixtures/clf/*.csv into data/raw/.
project:
  name: smartphone-addiction-s6e8-ci
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
  # MUST stay null. CI runs on tests/fixtures/clf, whose target is named `target`,
  # not `addicted_label`. Auto-detection reads the names from sample_submission.csv.
  id_column: null
  target_column: null
  task_type: null
  drop_columns: []

runtime:
  n_jobs: -1
  progress: false            # keep CI logs readable
  log_every_n_iterations: 0

cv:
  n_splits: 2

  shuffle: true

metric:
  name: auto                 # resolves to roc_auc for the binary fixture
  greater_is_better: null    # take the direction from the registry

features:
  numeric_imputation: median
  categorical_imputation: most_frequent
  categorical_encoding: ordinal
  scale_numeric: false
  max_onehot_cardinality: 15
  add_missing_indicators: true   # REQUIRED: _numeric_pipeline reads it, KeyError if absent

models:
  - name: lightgbm
    enabled: true
    weight: 0.7
    early_stopping_rounds: null
    params:
      n_estimators: 20
      learning_rate: 0.2
      num_leaves: 7
      min_child_samples: 2
      verbose: -1
  - name: hist_gbm
    enabled: true
    weight: 0.3
    early_stopping_rounds: null
    params:
      max_iter: 20
      learning_rate: 0.2
      max_leaf_nodes: 7
      min_samples_leaf: 2
      early_stopping: false
      verbose: 0

output:
  submission_filename: submission.csv
  round_predictions_to_labels: false
  clip_probabilities: [0.0, 1.0]
```

All nine top-level keys are present, because `validate_config` requires them.
`min_child_samples: 2` and `min_samples_leaf: 2` matter: with 60 fixture rows and 2 folds
there are 30 rows per fit, and the production values of 50 would prevent any split, giving a
constant prediction and tripping the `nunique() > 2` assertion for the wrong reason.

### 3. Write `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint
        run: ruff check .

      - name: Format check
        run: ruff format --check .

      - name: Unit tests
        run: pytest -q

      - name: Fixture smoke run
        run: |
          cp tests/fixtures/clf/train.csv tests/fixtures/clf/test.csv tests/fixtures/clf/sample_submission.csv data/raw/
          python -m src.cli inspect --config config/ci.yaml
          python -m src.cli train --config config/ci.yaml
          python -m src.cli predict --config config/ci.yaml
          test -f submissions/submission.csv

      - name: Assert the submission holds probabilities
        run: python -c "import pandas as pd; s = pd.read_csv('submissions/submission.csv'); t = s.columns[1]; assert s[t].between(0, 1).all(), (s[t].min(), s[t].max()); assert s[t].nunique() > 2, s[t].nunique(); print('submission ok', s.shape, s[t].nunique(), 'distinct values')"

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: pipeline-artifacts
          path: |
            reports/data_contract.md
            reports/metrics.json
            submissions/submission.csv

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build the image
        run: docker build -t smartphone-addiction-s6e8 .
```

Points to get right:

- The probability assertion is a single-line `python -c`, not a heredoc. A heredoc inside a
  YAML block scalar is easy to break on indentation, and this check is too important to lose
  to whitespace.
- `data/raw/` exists in the checkout because phase 01 committed `data/raw/.gitkeep`.
- **`pyproject.toml` must set `pythonpath = ["."]` under `[tool.pytest.ini_options]`.**
  The workflow runs bare `pytest -q`, but the Makefile runs `python -m pytest`, and only
  `python -m` puts the working directory on `sys.path`. Without the setting, CI fails with
  `ModuleNotFoundError: No module named 'src'` while `make test` passes locally — observed
  on the first push. It also means a grader typing plain `pytest` gets a green suite.
- The `inspect` step is included ahead of `train`. Implementation Plan §5.3 lists only train
  and predict; adding `inspect` exercises the third subcommand for free and matches what
  `make all` does.
- `actions/upload-artifact@v4` — the v3 action is deprecated and fails on current runners.

### 4. Write the `Dockerfile`

```dockerfile
# Reproducible image for the S6E8 pipeline. Single stage by design —
# Implementation Plan §9 lists multi-stage builds and size optimisation as non-goals.
FROM python:3.11-slim

# PYTHONUNBUFFERED keeps the progress logging (CLAUDE.md §7a) streaming.
# PY overrides the Makefile's `PY ?= $(VENV)/bin/python`: there is no venv in here.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PY=python

# libgomp1: LightGBM's OpenMP runtime. make: not shipped in python:3.11-slim,
# and the default CMD is `make all`.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency layer first, so it caches across source changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user. The output directories are created here because .dockerignore
# excludes data/, models/ and submissions/ from the build context.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p data/raw data/processed models reports/figures submissions \
    && chown -R appuser:appuser /app
USER appuser

CMD ["make", "all"]
```

`make docker-run` passes `--user $(id -u):$(id -g)`, which overrides `USER appuser` at run
time so the process shares the host user's uid and can write through the bind mounts. The
`USER appuser` line still matters — it is what makes a plain `docker run` non-root, which is
what Implementation Plan §5.2 asks for.

### 5. Write `.dockerignore`

```
.git
.gitignore
.github
.venv
venv
__pycache__
*.py[cod]
.pytest_cache
.ruff_cache
data
models
submissions
reports/figures
reports/metrics.json
reports/oof_predictions.csv
plans
*.log
.DS_Store
```

`tests/` is deliberately **not** excluded — keeping it lets `docker run <image> make test`
verify the image quickly without a full training run, and the fixtures are a few kilobytes.

### 6. Format, lint, test

```bash
make fmt
make lint
make test
```

### 7. Build and run the container

```bash
make docker-build
docker run --rm smartphone-addiction-s6e8 make test    # fast check that the image works
make docker-run                                        # the real thing; long
```

## Verification

```bash
# 1. Lint clean.
make lint
# expect: exit 0, zero findings

# 2. Full suite, six test files, no real data touched.
make test
# expect: 0 failures; test_smoke_pipeline collected alongside the other five

# 3. The suite genuinely does not need data/raw — the CI claim depends on this.
mv data/raw /tmp/raw-backup && mkdir -p data/raw && touch data/raw/.gitkeep
make test; echo "exit=$?"
rm -rf data/raw && mv /tmp/raw-backup data/raw
# expect: 0 failures, exit=0 with data/raw empty

# 4. The smoke test on its own, verbosely.
.venv/bin/python -m pytest -v tests/test_smoke_pipeline.py
# expect: every test passes, including the determinism and label-branch cases

# 5. config/ci.yaml validates and resolves.
.venv/bin/python -c "
from src.config import load_config
cfg = load_config('config/ci.yaml')
print('keys      :', sorted(cfg))
print('contract  :', cfg['contract'])
print('n_splits  :', cfg['cv']['n_splits'], '| progress:', cfg['runtime']['progress'])
print('metric    :', cfg['metric'])
print('round     :', cfg['output']['round_predictions_to_labels'])
assert cfg['contract']['target_column'] is None, 'ci.yaml must auto-detect the fixture target'
assert cfg['contract']['id_column'] is None
assert cfg['cv']['n_splits'] == 2
assert cfg['runtime']['progress'] is False
assert cfg['output']['round_predictions_to_labels'] is False
assert all(m['early_stopping_rounds'] is None for m in cfg['models'])
print('ci.yaml ok')
"
# expect: ci.yaml ok

# 6. Reproduce the CI smoke run locally, exactly as the workflow does it.
mv data/raw /tmp/raw-backup && mkdir -p data/raw
cp tests/fixtures/clf/*.csv data/raw/
make clean
.venv/bin/python -m src.cli inspect --config config/ci.yaml
.venv/bin/python -m src.cli train   --config config/ci.yaml
.venv/bin/python -m src.cli predict --config config/ci.yaml
.venv/bin/python -c "
import pandas as pd
s = pd.read_csv('submissions/submission.csv')
t = s.columns[1]
print('shape:', s.shape, '| column:', t, '| distinct:', s[t].nunique())
print('min/max:', s[t].min(), s[t].max())
assert s.shape == (20, 2), s.shape
assert s[t].between(0, 1).all()
assert s[t].nunique() > 2, s[t].nunique()
print('CI smoke run reproduces locally')
"
rm -rf data/raw && mv /tmp/raw-backup data/raw && make clean
# expect: shape (20, 2), distinct well above 2, then
#         CI smoke run reproduces locally
# If distinct == 1, the fixture models are not splitting — check that ci.yaml keeps
# min_child_samples: 2 and min_samples_leaf: 2, not the production value of 50.

# 7. The workflow file is valid YAML with the expected shape.
.venv/bin/python -c "
import yaml
wf = yaml.safe_load(open('.github/workflows/ci.yml'))
print('jobs   :', list(wf['jobs']))
print('on     :', wf[True] if True in wf else wf['on'])
steps = [s.get('name') or s.get('uses') for s in wf['jobs']['build']['steps']]
print('build  :'); [print('   -', s) for s in steps]
assert set(wf['jobs']) == {'build', 'docker'}
assert wf['jobs']['build']['runs-on'] == 'ubuntu-latest'
print('workflow ok')
"
# expect: jobs ['build', 'docker'], the full step list, workflow ok
# Note: PyYAML parses the bare key `on` as the boolean True — that is a YAML quirk,
# not a problem with the file. GitHub Actions reads it correctly.

# 8. Image builds.
make docker-build
# expect: exit 0, image tagged smartphone-addiction-s6e8

# 9. make and libgomp1 are both present in the image, and PY resolves to python.
docker run --rm smartphone-addiction-s6e8 sh -c 'make --version | head -1; python -c "import lightgbm; print(\"lightgbm\", lightgbm.__version__)"; echo "PY=$PY"'
# expect: GNU Make 4.x, a lightgbm version line, PY=python
# A missing `make` or a libgomp import error means step 4's apt line is wrong.

# 10. The container runs the test suite — proves the image is functional cheaply.
docker run --rm smartphone-addiction-s6e8 make test
# expect: 0 failures inside the container

# 11. The container is non-root by default.
docker run --rm smartphone-addiction-s6e8 id -u
# expect: 1000  (not 0)

# 12. No data, models or submissions leaked into the image.
docker run --rm smartphone-addiction-s6e8 sh -c 'ls data/raw | wc -l; ls models | wc -l; ls submissions | wc -l'
# expect: 0, 0, 0 — the build context excluded them

# 13. THE DOCKER REPRODUCIBILITY CHECK (CLAUDE.md §9). This runs `make all` on the real
#     data inside the container. No time limit; expect it to take as long as a host run.
cp submissions/submission.csv /tmp/sub-host.csv
make clean
make docker-run 2>&1 | tee /tmp/docker-run.log
cmp /tmp/sub-host.csv submissions/submission.csv && echo "Docker reproduces the host submission byte-for-byte"
# expect: cmp silent, then the confirmation line
# Note: if the host run used a different thread count than the container, LightGBM may
# differ in the last decimal places. If cmp fails, compare with the tolerance check
# below before concluding anything is broken.

# 14. If step 13's cmp failed, quantify the difference before acting.
.venv/bin/python -c "
import pandas as pd, numpy as np
a = pd.read_csv('/tmp/sub-host.csv')['addicted_label'].to_numpy()
b = pd.read_csv('submissions/submission.csv')['addicted_label'].to_numpy()
print('max abs diff:', float(np.max(np.abs(a - b))))
print('mean abs diff:', float(np.mean(np.abs(a - b))))
"
# expect (if it ran): differences at 1e-15 or below are float noise from a different
# thread count. Fix by pinning threads: set runtime.n_jobs to a fixed positive integer
# in config/default.yaml, or add deterministic: true to the lightgbm params. Both are
# config-only. Record what you did in the README (phase 07).

# 15. Progress output streamed from inside the container (PYTHONUNBUFFERED works).
grep -c "fold .*/5 | fit rows=" /tmp/docker-run.log
# expect: 10

# 16. Push and confirm CI. Requires a GitHub remote.
git remote -v
# if empty: create the standalone repo, `git remote add origin <url>`, then continue
git add -A && git commit -m "phase 06: tests, CI, and Docker" && git push -u origin main
gh run list --limit 1
gh run watch
# expect: both jobs (build, docker) green

# 17. Nothing that should not be tracked got committed.
git ls-files | grep -E '^data/raw/.*\.csv$' || echo "OK: no competition CSVs tracked"
git ls-files | grep -E '^(models|submissions)/.+' | grep -v gitkeep || echo "OK: no artifacts tracked"
# expect both OK lines

# 18. The Makefile and default config are still untouched.
git diff --stat Makefile config/default.yaml
# expect: no output (unless step 14 required a documented config change)
```

## Definition of done

- [ ] `make lint` exits 0 with zero findings.
- [ ] `make test` exits 0 with six test files collected.
- [ ] `make test` still exits 0 with `data/raw/` emptied — no test depends on real data.
- [ ] `tests/test_smoke_pipeline.py` exists and every listed test passes, including:
      the clf submission is float, in `[0, 1]`, with `nunique() > 2`; the reg submission is
      continuous and unclipped; two runs are byte-identical;
      `round_predictions_to_labels: true` yields only values from `{0, 1}`; `run_predict`
      without models raises `FileNotFoundError` mentioning ``make train``.
- [ ] `config/ci.yaml` exists, loads through `load_config`, has all nine top-level keys,
      `contract.*` nulled, `cv.n_splits == 2`, `runtime.progress is False`, every
      `early_stopping_rounds` null, and `round_predictions_to_labels is False`.
- [ ] The CI smoke sequence (`inspect` → `train` → `predict` with `config/ci.yaml` over the
      clf fixtures copied into `data/raw/`) exits 0 and writes a `(20, 2)` submission whose
      target column lies in `[0, 1]` with more than two distinct values.
- [ ] `.github/workflows/ci.yml` exists, parses as YAML, and defines exactly the jobs
      `build` and `docker`, both on `ubuntu-latest`.
- [ ] `Dockerfile` and `.dockerignore` exist.
- [ ] `make docker-build` exits 0.
- [ ] Inside the image: `make --version` works, `import lightgbm` works, `$PY` is `python`,
      `id -u` is 1000, and `data/raw`, `models`, `submissions` are all empty.
- [ ] `docker run --rm <image> make test` exits 0.
- [ ] `make docker-run` exits 0 and writes `submissions/submission.csv` to the host through
      the bind mounts.
- [ ] The container reproduces the host's **result**, evidenced by all of:
      all 10 per-fold CV scores and all 5 `best_iteration` values identical to the host;
      **zero rows changing rank position** between the two submissions; and an ROC AUC
      delta of exactly 0.0 when both are scored against the same labels.

      **Byte-identical output across host and container is NOT the criterion, and asking
      for it was a mistake in an earlier draft of this file.** Measured on this machine
      (macOS arm64 host, linux/arm64 container, both seeing 10 CPUs): the submissions
      differ in 80.75 % of rows at a maximum absolute difference of 1.5e-11 — the last one
      to three digits of the float64 decimal representation. Every fold score matched to
      six decimals and every `best_iteration` matched exactly, so the *models* are the
      same; the residue comes from floating-point summation order in a different libm /
      OpenMP build, which no config setting can remove. A thread pin does not help and
      must not be applied for this reason: the container already used the same thread
      count, and the difference is cross-toolchain, not cross-thread. Since ROC AUC is a
      function of ranking alone and the ranking is provably unchanged, the Kaggle score is
      bit-for-bit the same. Record this in the README rather than chasing it.

      Host-to-host byte-identity is a separate and stricter guarantee, and it *is*
      required — phase 05 proves it across four independent runs.
- [ ] `/tmp/docker-run.log` contains 10 fold-entry lines — progress streamed from the
      container.
- [ ] CI is green on both jobs after a push (requires a GitHub remote).
- [ ] `git ls-files` lists no `data/raw/*.csv` and no files under `models/` or
      `submissions/` other than `.gitkeep`.
- [ ] `scripts/make_eda.py`, `LICENSE`, and the final `README.md` were **not** created —
      those belong to phase 07.

## Handoff notes

What phase 07 may assume exists:

- Six passing test files, including an end-to-end smoke test on both fixture sets.
- `config/ci.yaml`, `.github/workflows/ci.yml`, `Dockerfile`, `.dockerignore`.
- A green CI run on the standalone GitHub repo, and its URL — phase 07 needs the
  `owner/repo` path for the README badge.
- A verified Docker path that reproduces the submission.
- Real numbers to quote: `reports/metrics.json` per-model and blend CV scores, and
  `runtime_seconds`.

Decisions phase 07 must stay consistent with:

1. **The standalone repo is canonical for CI.** The college repo receives a copy whose
   `.github/workflows/` will not execute, because Actions only runs workflows at the
   repository root. Phase 07's README must say this explicitly rather than implying the
   copy has working CI.
2. **The CI badge URL points at the standalone repo**, in the form
   `https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg`.
3. **`.dockerignore` keeps `tests/` in the image** so `docker run <image> make test` works.
   Phase 07 can cite that as a DevOps practice; do not remove it as "dead weight".
4. **`reports/data_contract.md` and `reports/metrics.json` are committed evidence
   artifacts** (phase 01's `.gitignore` allows them; `reports/oof_predictions.csv` is
   excluded for size). Phase 07 commits the figures alongside them.
5. **Any thread pin applied for step 14 is a config change that must be documented** in the
   README's reproducibility section, along with the seed and the Docker instructions.
6. **The early-stopping CV caveat from phase 04 still needs writing up** in the README's
   results or limitations section.

Commit before moving on (if not already done at step 16):

```bash
git add -A && git commit -m "phase 06: tests, CI, and Docker"
```
