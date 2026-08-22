# DevOps-CA1_2023_27

## DevOps CA1 - Open Source Contribution Report

# NLP with Disaster Tweets

## Group Information

- **Class**: TH2

| Roll No / PRN | Name |
|---|---|
| 23070122119 | Krittika Bisht |
| 23070122131 | Manasvi Pawa |

## About the Competition

[Natural Language Processing with Disaster Tweets](https://www.kaggle.com/competitions/nlp-getting-started) is a Kaggle "Getting Started" competition built around a dataset of ~10,000 hand-classified tweets. Twitter has become an important channel for real-time disaster reporting, but not every tweet that *sounds* like a disaster actually describes one — a tweet like "this traffic is ABLAZE" uses disaster language metaphorically, while "Forest fire near La Ronge Sask. Canada" reports a real event.

The task: given a tweet's text (plus optional `keyword` and `location` fields), predict whether it is genuinely about a real disaster (`target = 1`) or not (`target = 0`).

- **Data**: `train.csv` (7,613 labeled tweets), `test.csv` (3,263 unlabeled tweets), `sample_submission.csv`.
- **Evaluation metric**: F1 score between predicted and actual `target` values.
- **Submission format**: a CSV with `id,target` for every row in `test.csv`.

## Key Deliverables

1. **Baseline model** — a fast, interpretable TF-IDF + Logistic Regression pipeline that produces a valid submission in seconds and serves as a sanity-check floor for later models.
2. **Transformer model** — a fine-tuned `distilbert-base-uncased` classifier for a stronger score, runnable both locally (CPU) and on a GPU via Kaggle Notebooks.
3. **Reproducible pipeline** — shared text-cleaning logic, a fixed validation split, and scripts that regenerate submission CSVs from scratch.
4. **Results log** — local validation scores and public leaderboard scores tracked per model (below), so improvements are measurable across iterations.

## Technical Implementation

| Component | Approach |
|---|---|
| Text cleaning | Strip URLs, `@mentions`, and `#` characters (keeping hashtag text) via regex |
| Baseline model | `TfidfVectorizer` (1-2 grams, sublinear TF, 30k max features) + `LogisticRegression`, evaluated with shuffled 5-fold stratified CV |
| Transformer model | `distilbert-base-uncased` fine-tuned with Hugging Face `Trainer` (3 epochs, max length 96, lr 2e-5), 90/10 stratified train/val split, best checkpoint selected by validation F1 |
| Inference | Both scripts write directly to `submissions/*.csv` in the exact `id,target` format Kaggle expects |

### Project structure

```
Dataset/                  train.csv, test.csv, sample_submission.csv
src/baseline.py           TF-IDF + Logistic Regression baseline (CPU, seconds to run)
src/train.py              Fine-tuned transformer (distilbert-base-uncased by default)
notebooks/kaggle_notebook.ipynb   Same transformer pipeline, packaged to run in a Kaggle Notebook with GPU
submissions/               Output CSVs land here (gitignored)
```

## Setup (local)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

```bash
# Fast baseline -> submissions/submission_baseline.csv
python src/baseline.py

# Transformer fine-tune -> submissions/submission_transformer.csv
python src/train.py
```

`src/train.py` runs on CPU as-is (~30-40 min for 3 epochs on this dataset size). To use a stronger model on a GPU, edit `MODEL_NAME` at the top of the file (e.g. `bert-base-uncased`, `roberta-base`).

## Run on Kaggle (GPU)

1. On the [competition page](https://www.kaggle.com/competitions/nlp-getting-started), click **Code → New Notebook**.
2. Upload `notebooks/kaggle_notebook.ipynb` (File → Upload Notebook), or copy its cells in.
3. **Add Input** → attach the `nlp-getting-started` competition dataset.
4. Settings → Accelerator → GPU (T4 x2).
5. Run all cells. It writes `submission.csv` to `/kaggle/working/`.
6. Click **Submit to Competition** directly from the notebook (or download the CSV and use "Submit Predictions" from the competition's Submissions tab).

## Submitting from a local CSV

No notebook required — from the competition page's **Submissions** tab, click **Submit Predictions** and upload any file from `submissions/` (must have `id,target` columns matching `sample_submission.csv`).

## Teaming up

Kaggle teaming is separate from GitHub and must be done on Kaggle itself:

1. Both members join the competition individually (accept the rules).
2. Go to the competition's **Team** tab.
3. One member sends a merge/invite request to the other's Kaggle username; the other accepts.
4. Once merged you share one leaderboard entry and one pool of daily submissions — coordinate before submitting.

## Results log

| Model | Local CV / Val F1 | Public LB F1 | Notes |
|---|---|---|---|
| TF-IDF + LogisticRegression | 0.743 | | `src/baseline.py` |
| distilbert-base-uncased | 0.820 | | `src/train.py` / notebook |
