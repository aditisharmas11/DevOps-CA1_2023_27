# Implementation phases

Seven phases. **Execute one at a time, strictly in order.** Each phase file is
self-contained: a fresh session that has read `CLAUDE.md`, `Implementation Plan.md`, and
one phase file has everything it needs to complete that phase without asking questions.

| Phase | File | Goal |
|---|---|---|
| 01 | [phase-01-scaffold-and-tooling.md](phase-01-scaffold-and-tooling.md) | Directory tree, `.gitignore`, pinned `requirements.txt`, `pyproject.toml`, full `Makefile`, `config/default.yaml`, and `src/config.py`. |
| 02 | [phase-02-data-contract-and-loading.md](phase-02-data-contract-and-loading.md) | Derive the data contract from the CSVs, load and validate raw data, write `reports/data_contract.md`, commit the test fixtures. |
| 03 | [phase-03-features-and-models.md](phase-03-features-and-models.md) | Preprocessing `ColumnTransformer`, the model factory, and the metric registry. |
| 04 | [phase-04-training-pipeline.md](phase-04-training-pipeline.md) | K-fold CV training with probability OOF predictions, fold model artifacts, `reports/metrics.json`, and live progress logging. |
| 05 | [phase-05-prediction-and-submission.md](phase-05-prediction-and-submission.md) | Fold-averaged blended probabilities written to `submissions/submission.csv`, with the probability guards enforced. |
| 06 | [phase-06-tests-ci-and-docker.md](phase-06-tests-ci-and-docker.md) | Smoke tests, `config/ci.yaml`, GitHub Actions CI, `Dockerfile`, `.dockerignore`. |
| 07 | [phase-07-eda-docs-and-packaging.md](phase-07-eda-docs-and-packaging.md) | Four EDA figures, the graded `README.md`, `LICENSE`, and college-repo packaging. |

## How to run a phase

Start a fresh session and say:

```
Read CLAUDE.md, Implementation Plan.md, and plans/phase-01-scaffold-and-tooling.md.
Then execute phase 01 exactly as written. Run the verification commands at the end
and show me their output. Do not start any later phase.
```

## Rules

- **One phase per session.** Do not start work belonging to a later phase, even if it
  looks trivial.
- **Commit after every phase**: `git add -A && git commit -m "phase 01: scaffold"`. A
  bad phase then costs one rollback, not the project.
- **A failing verification is fixed inside its own phase.** Never advance with a red
  test — phase N+1's preconditions assume phase N's definition of done actually holds.
- **If reality contradicts the plan, stop and report it.** Do not silently deviate.
  Phase 02 is the likeliest place for this, where the real schema meets the plan's
  assumptions.

## Ordering constraints worth knowing up front

- `src/cli.py` is created in phase 02 with only the `inspect` subcommand, then extended
  in phase 04 (`train`) and phase 05 (`predict`).
- The `Makefile` is written complete in phase 01. Its `inspect`, `train`, `predict`,
  `eda`, `docker-*` targets exist immediately but only become functional in phases 02,
  04, 05, 07 and 06 respectively. This is intentional — the file is not re-edited five
  times.
- The test suite starts in phase 02 and must stay green from then on.
