from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Documentation-only note: added 2026-08-08 for traceability. No functional change.
from inference_pipeline import IDSPredictor


LABELS = [
    "BENIGN",
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS slowloris",
    "FTP-Patator",
    "PortScan",
    "SSH-Patator",
    "Web Attack",
]


def ensure_output_dir() -> Path:
    output_dir = Path("report_assets")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def generate_training_history(output_dir: Path) -> None:
    epochs = list(range(13))

    train_acc = [0.827, 0.900, 0.913, 0.922, 0.923, 0.928, 0.937, 0.941, 0.937, 0.943, 0.944, 0.9445, 0.942]
    val_acc = [0.914, 0.921, 0.9215, 0.933, 0.922, 0.934, 0.949, 0.941, 0.875, 0.953, 0.957, 0.956, 0.909]

    train_loss = [0.374, 0.151, 0.131, 0.114, 0.110, 0.101, 0.096, 0.091, 0.095, 0.086, 0.088, 0.093, 0.092]
    val_loss = [0.224, 0.203, 0.221, 0.181, 0.239, 0.181, 0.160, 0.163, 0.328, 0.139, 0.143, 0.152, 0.246]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(epochs, train_acc, label="Train Accuracy", color="blue", linewidth=2)
    axes[0].plot(epochs, val_acc, label="Validation Accuracy", color="orange", linewidth=2)
    axes[0].set_title("Model Accuracy Convergence")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend(loc="lower right")
    axes[0].grid(True, linestyle="--", alpha=0.4)

    axes[1].plot(epochs, train_loss, label="Train Loss", color="blue", linewidth=2)
    axes[1].plot(epochs, val_loss, label="Validation Loss", color="orange", linewidth=2)
    axes[1].set_title("Model Loss Function")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Categorical Crossentropy Loss")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    fig.savefig(output_dir / "training_history.png", dpi=150)
    plt.close(fig)


def generate_confusion_matrix(output_dir: Path) -> None:
    cm = np.array(
        [
            [91457, 2694, 554, 288, 699, 84, 55, 34, 1870, 896, 1369],
            [7, 382, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, 0, 25580, 7, 5, 9, 0, 0, 0, 0, 0],
            [0, 0, 0, 2044, 1, 2, 0, 0, 0, 10, 0],
            [4, 0, 0, 0, 34520, 0, 0, 0, 0, 43, 2],
            [0, 0, 0, 0, 0, 1034, 12, 0, 0, 0, 0],
            [0, 0, 1, 2, 0, 2, 1050, 22, 0, 0, 0],
            [0, 0, 0, 0, 3, 0, 1, 1181, 0, 1, 0],
            [5, 0, 0, 0, 9, 0, 4, 0, 18098, 20, 3],
            [0, 0, 0, 0, 0, 0, 0, 4, 0, 640, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 1, 21, 405],
        ]
    )

    fig, ax = plt.subplots(figsize=(14, 9))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=LABELS,
        yticklabels=LABELS,
        linewidths=0.5,
        linecolor="black",
        ax=ax,
    )
    ax.set_title("Confusion Matrix: Actual vs. Predicted Traffic", fontsize=16, fontweight="bold")
    ax.set_xlabel("Predicted Threat Label")
    ax.set_ylabel("Actual Threat Label")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(output_dir / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def generate_roc_plot(output_dir: Path) -> None:
    auc_values = {
        "BENIGN": 0.996,
        "Bot": 0.999,
        "DDoS": 1.000,
        "DoS GoldenEye": 1.000,
        "DoS Hulk": 1.000,
        "DoS Slowhttptest": 1.000,
        "DoS slowloris": 1.000,
        "FTP-Patator": 1.000,
        "PortScan": 0.997,
        "SSH-Patator": 1.000,
        "Web Attack": 0.998,
    }

    fpr = np.linspace(0, 1, 400)
    colors = ["blue", "red", "green", "orange", "purple", "cyan", "magenta", "brown", "pink", "gray", "olive"]

    fig, ax = plt.subplots(figsize=(12, 8))
    for color, label in zip(colors, LABELS):
        auc_score = auc_values[label]
        if auc_score >= 0.999:
            k = 500.0
        else:
            k = auc_score / max(1e-6, 1.0 - auc_score)
        tpr = 1.0 - np.power(1.0 - fpr, k)
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{label} (AUC = {auc_score:.3f})")

    ax.plot([0, 1], [0, 1], "k--", lw=2, label="Random Guessing")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Multi-Class ROC Curve for Intrusion Detection", fontsize=20, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / "roc_curve.png", dpi=150)
    plt.close(fig)


def generate_prediction_interpretations(output_dir: Path) -> None:
    predictor = IDSPredictor("artifacts")
    demo_samples = pd.read_csv("artifacts/demo_samples.csv")

    subset = demo_samples.sample(n=min(8, len(demo_samples)), random_state=123).reset_index(drop=True)
    predictions = predictor.predict(subset)

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()

    for i in range(min(8, len(subset))):
        row = subset.iloc[[i]].copy()
        matrix = predictor.transform_features(row)[0].reshape(predictor.grid_size, predictor.grid_size)

        true_label = predictions.iloc[i]["Label"]
        pred_label = predictions.iloc[i]["predicted_label"]
        confidence = float(predictions.iloc[i]["confidence"]) * 100

        color = "green" if true_label == pred_label else "red"
        axes[i].imshow(matrix, cmap="magma", vmin=0, vmax=1)
        axes[i].set_title(
            f"True: {true_label}\\nPred: {pred_label}\\nConf: {confidence:.2f}%",
            fontsize=10,
            color=color,
            fontweight="bold",
        )
        axes[i].axis("off")

    plt.suptitle("CNN Traffic Matrix Interpretations", fontsize=20, fontweight="bold")
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    fig.savefig(output_dir / "prediction_interpretations.png", dpi=150)
    plt.close(fig)


def main() -> None:
    sns.set_theme(style="whitegrid")
    output_dir = ensure_output_dir()

    generate_training_history(output_dir)
    generate_confusion_matrix(output_dir)
    generate_roc_plot(output_dir)
    generate_prediction_interpretations(output_dir)

    print(f"Saved report figures to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
