"""
Fine-tune a transformer for the Kaggle "NLP with Disaster Tweets" competition.

Runs as-is on CPU (locally) or GPU (Kaggle Notebook / Colab) -- device is
picked automatically. Only DATA_DIR differs between the two environments
(see notebooks/kaggle_notebook.ipynb for the Kaggle version).

Model choice:
    distilbert-base-uncased  -- default. ~40% faster/lighter than BERT-base,
                                 trains in a reasonable time on CPU, minimal
                                 accuracy loss for short-text classification.
    bert-base-uncased / roberta-base -- swap MODEL_NAME below when running
                                 on a GPU (Kaggle Notebook) for a stronger
                                 leaderboard score (~+1-2 F1 points).

Usage:
    python src/train.py
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 96
NUM_EPOCHS = 3
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
SEED = 42

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "Dataset"
OUT_DIR = ROOT / "submissions"
MODEL_DIR = ROOT / "outputs" / MODEL_NAME.replace("/", "-")


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {"f1": f1_score(labels, preds)}


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    train_df = pd.read_csv(DATA_DIR / "train.csv")
    test_df = pd.read_csv(DATA_DIR / "test.csv")

    train_df["text_clean"] = train_df["text"].apply(clean_text)
    test_df["text_clean"] = test_df["text"].apply(clean_text)

    train_part, val_part = train_test_split(
        train_df, test_size=0.1, random_state=SEED, stratify=train_df["target"]
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(
            batch["text_clean"], truncation=True, max_length=MAX_LENGTH
        )

    train_ds = Dataset.from_pandas(train_part[["text_clean", "target"]].rename(
        columns={"target": "labels"}
    ))
    val_ds = Dataset.from_pandas(val_part[["text_clean", "target"]].rename(
        columns={"target": "labels"}
    ))
    test_ds = Dataset.from_pandas(test_df[["text_clean"]])

    train_ds = train_ds.map(tokenize, batched=True)
    val_ds = val_ds.map(tokenize, batched=True)
    test_ds = test_ds.map(tokenize, batched=True)

    collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2
    )

    args = TrainingArguments(
        output_dir=str(MODEL_DIR),
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        logging_steps=50,
        report_to="none",
        seed=SEED,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    print(f"Validation F1: {metrics['eval_f1']:.4f}")

    preds = trainer.predict(test_ds)
    labels = np.argmax(preds.predictions, axis=1)

    OUT_DIR.mkdir(exist_ok=True)
    submission = pd.DataFrame({"id": test_df["id"], "target": labels})
    out_path = OUT_DIR / "submission_transformer.csv"
    submission.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(submission)} rows)")


if __name__ == "__main__":
    main()
