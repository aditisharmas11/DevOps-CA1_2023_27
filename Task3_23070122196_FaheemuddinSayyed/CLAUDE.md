# CLAUDE.md

Persistent project context. Read this file at the start of **every** session before
touching any code.

---

## 1. What this project is

A small, fully reproducible machine-learning pipeline for the Kaggle competition
**Playground Series — Season 6, Episode 8: "Predicting Smartphone Addiction"**
(<https://www.kaggle.com/competitions/playground-series-s6e8>).

**Confirmed competition facts** (verified from the competition page):

| Fact | Value |
|---|---|
| Start date | 1 August 2026 |
| Final submission deadline | **31 August 2026, 23:59 UTC** |
| Task | **Binary classification** |
| Target column | `addicted_label` |
| ID column | `id` |
| Evaluation metric | **ROC AUC** between predicted probability and observed target |
| Submission format | `id,addicted_label` — a **probability**, not a hard label |
| Files | `train.csv`, `test.csv`, `sample_submission.csv` |
| Data origin | Synthetic, inspired by the Smartphone Addiction Prediction Dataset |

The probability requirement is the single most important detail in this project.
Writing 0/1 labels instead of probabilities produces a valid-looking file that scores
badly. See §5a.

The repository is a submission for a **DevOps course Continuous Assessment (CA)**.
That means the DevOps scaffolding (containerisation, CI, tests, Makefile,
reproducibility) matters *as much as* the model quality. A mediocre leaderboard
score with clean CI is a better outcome here than a great score with no automation.

**Primary deliverable:** a repo that a grader can clone and run end-to-end with two
commands, producing a valid `submission.csv`.

**Secondary deliverable:** evidence artifacts (metrics, plots, README report) that
document what was done.

---

## 2. Hard constraints — do not violate

| Constraint | Rule |
|---|---|
| Scope | This is a **low-weightage CA**. Do not add features beyond the Implementation Plan. No web UI, no MLflow, no Kubernetes, no cloud deploys, no hyperparameter search frameworks (Optuna etc.). |
| Runtime | **No wall-clock limit.** Training may run for hours if that buys a better score. Spend the budget on more estimators and folds, not on new frameworks. Record the measured runtime in `reports/metrics.json` and the README. |
| Progress visibility | Long runs must report progress continuously — see §7a. A stage that prints nothing for minutes is a defect. |
| Hardware | CPU, multi-threaded, via `runtime.n_jobs`. **Apple MPS is not usable here** — see §3a. |
| Dependencies | Only what is in `requirements.txt`. Do **not** add new third-party packages without an explicit instruction. |
| Network | Training and prediction code must **never** hit the network. Data is read from local disk only. |
| Data | Never commit `data/raw/*.csv` to git. They are gitignored. Never invent or synthesise competition data outside `tests/fixtures/`. |
| Secrets | No API keys, no `kaggle.json`, no tokens in the repo, ever. |
| Determinism | Every random operation takes a seed from config. Two consecutive runs must produce byte-identical `submission.csv`. |

---

## 3. Tech stack (fixed)

- Python **3.11**
- `pandas`, `numpy` — data handling
- `scikit-learn` — preprocessing, CV splitters, metrics, `HistGradientBoosting*` fallback model
- `lightgbm` — primary model
- `pyyaml` — config
- `matplotlib` — EDA plots (no seaborn)
- `pytest` — tests
- `ruff` — lint + format
- Docker, GitHub Actions, GNU Make

Deliberately **excluded**: seaborn, optuna, xgboost, catboost, torch, mlflow, dvc,
hydra, typer, poetry. Do not introduce them.

### 3a. On GPU acceleration and Apple MPS

**MPS cannot be used by this pipeline.** It is a PyTorch/Metal backend. LightGBM and
scikit-learn have no Metal path: LightGBM's GPU support is OpenCL/CUDA only and the
PyPI wheel is built CPU-only, and scikit-learn is CPU-only by design. Reaching MPS
would require `torch` plus a neural network — both explicitly excluded (§3 above,
Implementation Plan §9).

It would also not help. The dataset is ~691k rows × 12 features, which is small for
gradient boosting; LightGBM's histogram algorithm is memory-bandwidth bound and
saturates the performance cores well before a GPU's transfer overhead pays off.

Therefore: run multi-threaded on CPU with `runtime.n_jobs: -1`. The
`models[].params.device` key is exposed in config purely so a GPU-enabled LightGBM
build could be pointed at without touching `src/`. Leave it at `cpu`.

---

## 4. Repository layout (target state)

```
smartphone-addiction-s6e8/
├── CLAUDE.md
├── Implementation Plan.md
├── README.md
├── LICENSE
├── Makefile
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── pyproject.toml              # ruff + pytest config only
├── config/
│   └── default.yaml
├── plans/                      # phase files, created before implementation
│   ├── phase-01-....md
│   └── ...
├── src/
│   ├── __init__.py
│   ├── config.py               # load + validate YAML config
│   ├── contract.py             # derive id/target/task-type from the data
│   ├── data.py                 # load, validate, split
│   ├── features.py             # preprocessing pipeline
│   ├── models.py               # model factory
│   ├── metrics.py              # metric registry
│   ├── train.py                # CV training entrypoint
│   ├── predict.py              # inference + submission entrypoint
│   └── cli.py                  # argparse dispatch
├── scripts/
│   ├── inspect_data.py         # writes reports/data_contract.md
│   └── make_eda.py             # writes reports/figures/*.png
├── tests/
│   ├── fixtures/               # tiny synthetic CSVs — safe to commit
│   ├── test_contract.py
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_metrics.py
│   └── test_smoke_pipeline.py
├── data/
│   ├── raw/                    # gitignored — user places Kaggle CSVs here
│   │   └── .gitkeep
│   └── processed/              # gitignored
├── models/                     # gitignored
├── reports/
│   ├── data_contract.md        # generated
│   ├── metrics.json            # generated
│   └── figures/                # generated
├── submissions/                # gitignored except .gitkeep
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 5. The schema-discovery rule

The contract is known (`id` / `addicted_label` / binary classification), and it is
written explicitly into `config/default.yaml`. But **do not hardcode those strings in
`src/`.** The code still derives the contract at runtime and treats config as an
override. This keeps the auto-detection path exercised by the regression test fixture
and means a column rename on Kaggle's side does not break the pipeline.

The derivation:

1. Read `data/raw/sample_submission.csv`.
2. Column 0 → the **ID column** name.
3. Column 1 → the **target column** name.
4. Inspect `data/raw/train.csv[target]`:
   - non-numeric dtype, or numeric with `nunique <= 20` → **classification**
     (binary if `nunique == 2`, else multiclass)
   - otherwise → **regression**
5. Everything in `train.csv` except ID and target → features. Split into numeric
   vs categorical by dtype.

The user may override any of these in `config/default.yaml`. Config always wins
over auto-detection.

If `data/raw/` is empty, code must fail with a clear, actionable message telling the
user which files to download and where to put them — **never** with a traceback and
never by fabricating data.

---

## 5a. The probability rule (do not get this wrong)

This competition is scored on **ROC AUC against predicted probabilities**. Therefore:

- Out-of-fold predictions for binary classification are stored as
  `model.predict_proba(X)[:, 1]` — a float in [0, 1]. **Never** `model.predict(X)`.
- Blending averages probabilities across folds and across models. Never vote on labels.
- The submission's `addicted_label` column contains floats, not 0/1 integers.
- `output.round_predictions_to_labels` is **false** for this competition. It exists
  only so the regression/label code path stays testable; do not flip it.
- Any metric in the registry that needs hard labels (accuracy, f1_macro) must
  threshold the stored probabilities at 0.5 internally. The stored artefact stays a
  probability.
- A submission whose target column contains only the values 0 and 1 is a **bug**, even
  though Kaggle will accept the file. Phase 05's verification must assert that the
  column has more than two distinct values and lies within [0, 1].

---

## 6. Commands (must all work when the project is complete)

```bash
make setup        # create venv, install requirements
make inspect      # generate reports/data_contract.md from data/raw/
make eda          # generate reports/figures/*.png
make train        # CV training -> models/, reports/metrics.json
make predict      # inference -> submissions/submission.csv
make all          # inspect -> train -> predict
make test         # pytest
make lint         # ruff check + ruff format --check
make fmt          # ruff format
make docker-build
make docker-run   # runs `make all` inside the container
make clean        # remove generated artifacts, keep data/raw
```

Underlying CLI (Make targets are thin wrappers):

```bash
python -m src.cli inspect  --config config/default.yaml
python -m src.cli train    --config config/default.yaml
python -m src.cli predict  --config config/default.yaml
```

---

## 7. Coding conventions

- Line length 100. Ruff enforces it.
- Type hints on every public function signature.
- Docstrings: one-line summary minimum on every module and public function.
- No `print()` in `src/` — use the `logging` module, configured once in `src/cli.py`.
  `print()` is fine in `scripts/`.
- No notebooks in the repo. EDA is a script that writes PNGs.
- Paths: always build from config, always `pathlib.Path`, never string concatenation,
  never absolute paths.
- Functions do one thing. If a function exceeds ~40 lines, split it.
- Fail loudly and early with `ValueError`/`FileNotFoundError` and a message that says
  what the user should do next.

---

## 7a. Progress and verbosity

Training is expected to run long, so the operator must always be able to tell what is
happening and how far along it is. Requirements:

- `logging.basicConfig` is configured once in `src/cli.py` with the format
  `%(asctime)s %(levelname)-8s %(name)s: %(message)s` and `datefmt="%H:%M:%S"`.
- Every stage logs its start and end at `INFO` with an elapsed time in seconds.
- `train` logs, at `INFO`: the derived contract, train/test shapes, the enabled models
  and their normalised weights, and then for **every fold of every model** a line on
  entry (`model 1/2 lightgbm | fold 3/5 | fit rows=553095 val rows=138274`) and a line
  on exit carrying that fold's score and elapsed seconds, plus a cumulative
  `elapsed / estimated remaining` figure derived from mean fold time so far.
- LightGBM's own output is routed into Python logging via
  `lightgbm.register_logger(logging.getLogger("lightgbm"))`, so per-iteration eval
  lines carry timestamps like everything else. Per-iteration reporting is driven by a
  `log_evaluation(period=runtime.log_every_n_iterations)` callback with the fold's
  validation slice as `eval_set`.
- `HistGradientBoosting*` receives `verbose=1` so it reports its own iterations.
  sklearn writes these to stdout itself; that is not a `print()` in `src/` and is
  acceptable.
- `predict` logs each model's fold-averaging progress and a final distribution summary
  (count, min, mean, max, and the count of distinct values) of the written column.
- `runtime.progress: false` must reduce this to stage-level logging only, so CI and the
  test suite stay quiet. Nothing may depend on `progress` being true.

`print()` remains banned in `src/` (§7). All of the above goes through `logging`.

---

## 8. Phase workflow

Implementation is split into numbered phase files in `plans/`. Rules:

- Execute exactly one phase per instruction ("execute phase 03").
- Before executing a phase, read `CLAUDE.md`, `Implementation Plan.md`, and that
  phase file. Also skim earlier phase files' "Definition of done" sections to know
  what should already exist.
- Do not start work from a later phase early, even if it seems trivial.
- At the end of a phase, run its verification commands and show the output.
- If a phase's verification fails, fix it within that phase. Do not proceed.
- If reality contradicts the plan (e.g. the real dataset has a quirk the plan did not
  anticipate), **stop and report it** rather than silently deviating.

---

## 9. Definition of done for the whole project

- [ ] `make lint` passes with zero findings.
- [ ] `make test` passes; all tests run on committed fixtures with no real data present.
- [ ] `make all` runs end-to-end on real data and writes `submissions/submission.csv`.
      There is no time limit; the measured wall-clock time is recorded in
      `reports/metrics.json` as `runtime_seconds` and quoted in the README.
- [ ] Long stages emit continuous progress output per §7a.
- [ ] `submission.csv` has exactly the same shape, column names, and ID values as
      `data/raw/sample_submission.csv`, with no nulls.
- [ ] Two consecutive `make all` runs produce identical `submission.csv`.
- [ ] `reports/metrics.json` contains per-fold and mean CV scores.
- [ ] `make docker-build && make docker-run` reproduces the same result.
- [ ] GitHub Actions CI is green on push.
- [ ] `README.md` documents setup, usage, results, and the DevOps practices used.
- [ ] No leftover TODOs, no stub functions, no commented-out code.

---

## 10. Items to confirm during Phase 02

The competition metadata is settled (see §1). What remains is to confirm the **data**
matches, by reading the actual downloaded CSVs. Record findings in
`reports/data_contract.md`:

1. Auto-detected contract equals `id` / `addicted_label` / binary classification.
   If it does not, **stop and report** — something is wrong with the download.
2. Row counts of train and test; feature count; which features are numeric vs
   categorical.
3. Class balance of `addicted_label`. If it is heavily imbalanced, note it in the
   report — but do **not** add resampling or `scale_pos_weight` without instruction.
   ROC AUC is threshold-free and tolerates imbalance.
4. Missing-value counts per column.
5. Whether `sample_submission.csv` header is exactly `id,addicted_label`.

The competition offers an original source dataset on Kaggle. **Ignore it** — using
external data is out of scope for this CA.
