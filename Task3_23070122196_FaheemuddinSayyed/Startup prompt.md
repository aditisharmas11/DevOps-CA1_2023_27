# Startup prompt

Paste everything inside the fenced block below into a **fresh Claude Code session**
opened in the project workspace. It produces the `plans/` folder only — it writes no
project code.

---

```
You are setting up a project workspace. Two documents are already present in this
directory: `CLAUDE.md` and `Implementation Plan.md`.

STEP 1 — Read both files completely before doing anything else. Read them in full,
not in fragments. `CLAUDE.md` gives you the constraints, conventions, tech stack, and
definition of done. `Implementation Plan.md` gives you the architecture, per-module
specifications, config schema, test spec, DevOps spec, and a suggested seven-phase
decomposition in its section 7.

STEP 2 — Also inspect the current state of the workspace: list the files that exist,
check whether `data/raw/` contains the Kaggle CSVs, and note anything already present.
Do not create, modify, or delete any project files in this step.

STEP 3 — Create a `plans/` directory and write exactly seven phase files into it,
following the decomposition in section 7 of the Implementation Plan:

  plans/phase-01-scaffold-and-tooling.md
  plans/phase-02-data-contract-and-loading.md
  plans/phase-03-features-and-models.md
  plans/phase-04-training-pipeline.md
  plans/phase-05-prediction-and-submission.md
  plans/phase-06-tests-ci-and-docker.md
  plans/phase-07-eda-docs-and-packaging.md

Also write `plans/README.md`: a short index listing the seven phases, the one-line
goal of each, and the instruction that phases are executed one at a time and strictly
in order.

STEP 4 — Each phase file MUST follow this exact structure, with all sections present:

  # Phase NN — <Title>

  ## Objective
  Two or three sentences: what this phase delivers and why it exists.

  ## Preconditions
  What must already be true. Name the specific files and directories that earlier
  phases created and that this phase depends on. For phase 01, state that the
  workspace contains only CLAUDE.md, Implementation Plan.md, and plans/.

  ## Context recap
  Everything from CLAUDE.md and Implementation Plan.md that is needed to do THIS
  phase, restated inline. This section is what makes a fresh session viable — assume
  the executing session has read CLAUDE.md and Implementation Plan.md but has no
  memory of any prior phase's conversation. Copy in the relevant config keys, the
  relevant module specs, and the relevant conventions verbatim rather than
  cross-referencing by section number alone.

  ## Files to create or modify
  A table: path | action (create/modify) | purpose.

  ## Detailed steps
  Numbered, imperative, specific. For each file, specify its complete contents or a
  precise enough description that two different sessions would produce functionally
  equivalent code: function names, signatures, return types, error messages, and
  behaviour on edge cases. Where the Implementation Plan already gives an exact spec
  (config schema, JSON shapes, error message wording), reproduce it here rather than
  pointing at it.

  ## Verification
  Concrete shell commands to run, each with the expected outcome stated. Prefer
  commands that fail loudly. Include at minimum a lint check and, from phase 03
  onward, the relevant tests.

  ## Definition of done
  A checklist. Every item must be objectively checkable — a file exists, a command
  exits zero, a specific assertion holds. No subjective items.

  ## Handoff notes
  What the next phase will assume exists as a result of this one. Flag any decision
  taken here that a later phase must stay consistent with.

STEP 5 — Rules to obey while writing the phase files:

  - Respect every constraint in CLAUDE.md section 2 and every non-goal in
    Implementation Plan section 9. If a phase file you draft contains a non-goal,
    rewrite it.
  - The competition metadata is confirmed: binary classification, target
    `addicted_label`, ID `id`, metric ROC AUC, submission holds PROBABILITIES, deadline
    31 August 2026. These live in `config/default.yaml`. But do NOT scatter the literal
    strings "id" or "addicted_label" through `src/` — the code derives the contract at
    runtime with config as an override, per CLAUDE.md section 5.
  - Read CLAUDE.md section 5a carefully and carry its consequences into phases 04, 05
    and 06. Predicted values are `predict_proba(X)[:, 1]` end to end; blending averages
    probabilities; the submission column is float, not 0/1. Phase 05's verification must
    assert the submission column lies in [0, 1] and has more than two distinct values.
  - Phase files must be self-contained enough that a session which has read only
    CLAUDE.md, Implementation Plan.md, and that one phase file can complete it
    correctly without asking questions.
  - Phases must be strictly ordered with no forward dependencies: nothing in phase N
    may require a file that only phase N+1 creates.
  - Every phase must leave the repository in a working state — lint passes, and from
    phase 03 onward the test suite passes.
  - Size each phase at roughly 20 to 40 minutes of work. If a phase looks much larger
    than that, say so in your summary rather than silently splitting it.
  - Write plain, direct prose. No filler, no motivational language.

STEP 6 — Do NOT implement any of the phases. Do not create `src/`, `tests/`,
`config/`, the Makefile, the Dockerfile, or any other project file. Your entire output
for this session is `plans/README.md` plus the seven phase files.

STEP 7 — When finished, report back with:
  a. the list of files you created
  b. a one-line summary of each phase
  c. any contradiction, ambiguity, or gap you found between CLAUDE.md and
     Implementation Plan.md, or anything in the plan you believe is wrong or
     underspecified — state these plainly rather than papering over them
  d. anything you need from me before phase 01 can be executed

After this, I will run the phases one at a time by saying "execute phase 01", and so
on. Each of those will be a fresh session, so the phase files must carry their own
context.
```

---

## How to run the phases afterwards

Once `plans/` exists, start a **new session per phase** and use:

```
Read CLAUDE.md, Implementation Plan.md, and plans/phase-01-scaffold-and-tooling.md.
Then execute phase 01 exactly as written. Run the verification commands at the end
and show me their output. Do not start any later phase.
```

Then the same for phase 02, and so on. Two habits that make this work reliably:

- **Commit after every phase.** `git add -A && git commit -m "phase 01: scaffold"`.
  If a phase goes wrong you roll back one phase, not the whole project.
- **If a phase's verification fails, fix it inside that phase.** Never move on with a
  red test, because phase N+1's preconditions assume phase N's definition of done
  actually holds.

If a phase reports that reality contradicts the plan — most likely in phase 02, when
the real dataset schema meets the plan's assumptions — stop and tell me what it found
before continuing.
