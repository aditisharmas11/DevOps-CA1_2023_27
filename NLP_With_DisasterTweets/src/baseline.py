"""
TF-IDF + Logistic Regression baseline for the Kaggle "NLP with Disaster Tweets" competition.

Fast, CPU-only sanity-check model. Trains in seconds and produces a valid
submission.csv so you always have a working leaderboard entry while the
transformer trains in the background.

Usage:
    python src/baseline.py
"""

import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "Dataset"
OUT_DIR = ROOT / "submissions"


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    train_df = pd.read_csv(DATA_DIR / "train.csv")
    test_df = pd.read_csv(DATA_DIR / "test.csv")

    train_df["text_clean"] = train_df["text"].apply(clean_text)
    test_df["text_clean"] = test_df["text"].apply(clean_text)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_features=30000,
        sublinear_tf=True,
    )
    X_train = vectorizer.fit_transform(train_df["text_clean"])
    X_test = vectorizer.transform(test_df["text_clean"])
    y_train = train_df["target"]

    clf = LogisticRegression(C=1.0, max_iter=1000)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1")
    print(f"5-fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)

    OUT_DIR.mkdir(exist_ok=True)
    submission = pd.DataFrame({"id": test_df["id"], "target": preds})
    out_path = OUT_DIR / "submission_baseline.csv"
    submission.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(submission)} rows)")


if __name__ == "__main__":
    main()
