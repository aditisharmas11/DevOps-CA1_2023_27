from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model


def find_best_checkpoint(checkpoints_dir: Path) -> Path:
    # Documentation-only change added 2026-08-08: small clarifying comment.
    # No functional modifications are made to the data-preparation logic.
    """Return checkpoint with highest val_acc based on filename pattern."""
    pattern = re.compile(r"val_acc_(\d+\.\d+)\.keras$")
    best_path: Path | None = None
    best_acc = -1.0

    for candidate in checkpoints_dir.glob("*.keras"):
        match = pattern.search(candidate.name)
        if not match:
            continue
        score = float(match.group(1))
        if score > best_acc:
            best_acc = score
            best_path = candidate

    if best_path is None:
        raise FileNotFoundError(f"No valid checkpoint found under {checkpoints_dir}")

    print(f"Selected checkpoint: {best_path.name} (val_acc={best_acc:.4f})")
    return best_path


def read_sampled_rows(
    csv_path: Path,
    rows_per_file: int,
    chunksize: int,
    random_seed: int,
) -> pd.DataFrame:
    """Read a bounded sample from a large CSV using chunk sampling."""
    selected_chunks: List[pd.DataFrame] = []
    collected = 0

    for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunksize, low_memory=False)):
        if collected >= rows_per_file:
            break

        chunk.columns = chunk.columns.str.strip()

        remaining = rows_per_file - collected
        per_chunk_take = min(max(2000, rows_per_file // 16), remaining)

        if len(chunk) > per_chunk_take:
            sampled = chunk.sample(n=per_chunk_take, random_state=random_seed + i)
        else:
            sampled = chunk

        selected_chunks.append(sampled)
        collected += len(sampled)

    if not selected_chunks:
        raise ValueError(f"No rows were read from {csv_path}")

    out = pd.concat(selected_chunks, ignore_index=True)
    print(f"Loaded {len(out):,} sampled rows from {csv_path.name}")
    return out


def load_sampled_dataset(
    datasets_dir: Path,
    rows_per_file: int,
    chunksize: int,
    random_seed: int,
) -> pd.DataFrame:
    """Load and combine sampled data from all dataset CSV files."""
    csv_paths = sorted(datasets_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found under {datasets_dir}")

    frames: List[pd.DataFrame] = []
    for idx, csv_path in enumerate(csv_paths):
        sampled = read_sampled_rows(
            csv_path=csv_path,
            rows_per_file=rows_per_file,
            chunksize=chunksize,
            random_seed=random_seed + idx * 100,
        )
        sampled["_source_file"] = csv_path.name
        frames.append(sampled)

    combined = pd.concat(frames, ignore_index=True)
    combined.columns = combined.columns.str.strip()
    return combined


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the same broad cleaning logic used by notebook workflow."""
    if "Label" not in df.columns:
        raise KeyError("Required column 'Label' was not found.")

    cleaned = df.copy()
    cleaned["Label"] = cleaned["Label"].astype(str)
    cleaned["Label"] = cleaned["Label"].str.replace(r"[^\x00-\x7F]+", " ", regex=True)
    cleaned["Label"] = cleaned["Label"].str.replace("  ", " ", regex=False).str.strip()
    cleaned["Label"] = cleaned["Label"].apply(lambda value: "Web Attack" if "Web Attack" in value else value)

    cleaned.replace([np.inf, -np.inf], np.nan, inplace=True)
    cleaned.dropna(inplace=True)
    cleaned.drop_duplicates(inplace=True)
    cleaned = cleaned[cleaned["Label"] != ""]

    return cleaned


def compute_training_label_names(
    datasets_dir: Path,
    min_samples: int,
    chunksize: int,
) -> List[str]:
    """Infer training-time label set from full dataset label counts."""
    counts: Dict[str, int] = {}

    for csv_path in sorted(datasets_dir.glob("*.csv")):
        for chunk in pd.read_csv(
            csv_path,
            usecols=lambda col: col.strip() == "Label",
            chunksize=chunksize,
            low_memory=False,
        ):
            label_col = chunk.columns[0]
            labels = chunk[label_col].astype(str)
            labels = labels.str.replace(r"[^\x00-\x7F]+", " ", regex=True)
            labels = labels.str.replace("  ", " ", regex=False).str.strip()
            labels = labels.apply(lambda value: "Web Attack" if "Web Attack" in value else value)

            for label, count in labels.value_counts().items():
                counts[label] = counts.get(label, 0) + int(count)

    valid = sorted([label for label, count in counts.items() if count >= min_samples])
    if not valid:
        raise ValueError(
            "No labels met minimum sample count from full dataset. "
            f"min_samples={min_samples}"
        )

    print("Training label set inferred from full dataset:")
    for label in valid:
        print(f"- {label}: {counts[label]:,}")

    return valid


def filter_and_balance_classes(
    df: pd.DataFrame,
    valid_labels: List[str],
    benign_label: str,
    benign_cap: int,
    random_seed: int,
) -> pd.DataFrame:
    """Filter low-frequency classes and cap BENIGN count for better demo balance."""
    filtered = df[df["Label"].isin(valid_labels)].copy()

    benign_df = filtered[filtered["Label"] == benign_label]
    attack_df = filtered[filtered["Label"] != benign_label]

    if len(benign_df) > benign_cap:
        benign_df = benign_df.sample(n=benign_cap, random_state=random_seed)

    balanced = pd.concat([benign_df, attack_df], ignore_index=True)
    balanced = balanced.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)

    print("Class distribution after filtering and balancing:")
    print(balanced["Label"].value_counts())

    return balanced


def extract_features_and_labels(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Build numeric feature matrix and aligned labels."""
    if "Label" not in df.columns:
        raise KeyError("Column 'Label' not found.")

    features = df.drop(columns=["Label"]).copy()

    if "_source_file" in features.columns:
        features = features.drop(columns=["_source_file"])

    # Coerce every feature to numeric to match model expectations.
    features = features.apply(pd.to_numeric, errors="coerce")
    features.replace([np.inf, -np.inf], np.nan, inplace=True)

    valid_mask = ~features.isna().any(axis=1)
    features = features.loc[valid_mask].reset_index(drop=True)
    labels = df.loc[valid_mask, "Label"].reset_index(drop=True)

    zero_var_cols = features.columns[features.std(ddof=0) == 0].tolist()
    if zero_var_cols:
        features = features.drop(columns=zero_var_cols)

    return features, labels, zero_var_cols


def build_replay_sequence(
    sampled_df: pd.DataFrame,
    benign_label: str,
    replay_benign_count: int,
    replay_attack_per_class: int,
    random_seed: int,
) -> pd.DataFrame:
    """Create a deterministic benign-then-attack timeline for live replay."""
    benign = sampled_df[sampled_df["Label"] == benign_label]
    attacks = sampled_df[sampled_df["Label"] != benign_label]

    if benign.empty or attacks.empty:
        raise ValueError("Replay sequence requires both BENIGN and ATTACK samples.")

    parts: List[pd.DataFrame] = []
    base = benign.sample(n=min(replay_benign_count, len(benign)), random_state=random_seed)
    parts.append(base)

    for i, label in enumerate(sorted(attacks["Label"].unique().tolist())):
        class_rows = attacks[attacks["Label"] == label]
        take = min(replay_attack_per_class, len(class_rows))
        parts.append(class_rows.sample(n=take, random_state=random_seed + i + 10))

    replay = pd.concat(parts, ignore_index=True)
    replay.insert(0, "timeline_step", np.arange(1, len(replay) + 1))
    return replay


def save_assets(
    workspace: Path,
    assets_dir: Path,
    checkpoint_path: Path,
    scaler: MinMaxScaler,
    feature_columns: List[str],
    zero_var_columns: List[str],
    label_names: List[str],
    grid_size: int,
    sampled_df: pd.DataFrame,
    replay_df: pd.DataFrame,
    default_alert_threshold: float,
) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)

    scaler_path = assets_dir / "scaler.joblib"
    meta_path = assets_dir / "preprocessing_meta.json"
    samples_path = assets_dir / "demo_samples.csv"
    replay_path = assets_dir / "replay_sequence.csv"

    joblib.dump(scaler, scaler_path)

    checkpoint_rel = checkpoint_path.resolve().relative_to(workspace.resolve())

    meta: Dict[str, object] = {
        "checkpoint_path": checkpoint_rel.as_posix(),
        "feature_columns": feature_columns,
        "zero_variance_columns": zero_var_columns,
        "label_names": label_names,
        "grid_size": grid_size,
        "target_features": grid_size * grid_size,
        "default_alert_threshold": default_alert_threshold,
        "benign_label": "BENIGN",
    }

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    sampled_df.to_csv(samples_path, index=False)
    replay_df.to_csv(replay_path, index=False)

    print(f"Saved scaler: {scaler_path}")
    print(f"Saved metadata: {meta_path}")
    print(f"Saved demo samples: {samples_path} ({len(sampled_df):,} rows)")
    print(f"Saved replay sequence: {replay_path} ({len(replay_df):,} rows)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare offline demo assets for IDS Streamlit app.")
    parser.add_argument("--workspace", type=Path, default=Path("."), help="Project root path")
    parser.add_argument("--datasets-dir", type=Path, default=Path("datasets"), help="Directory containing CSV files")
    parser.add_argument("--checkpoints-dir", type=Path, default=Path("Checkpoints"), help="Directory containing .keras checkpoints")
    parser.add_argument("--assets-dir", type=Path, default=Path("artifacts"), help="Output asset directory")
    parser.add_argument("--rows-per-file", type=int, default=40000, help="Sample size to read per dataset file")
    parser.add_argument("--chunksize", type=int, default=100000, help="CSV chunk size for sampling")
    parser.add_argument(
        "--training-min-samples",
        type=int,
        default=1000,
        help="Class threshold used during original model training",
    )
    parser.add_argument("--benign-cap", type=int, default=50000, help="Upper bound for BENIGN rows")
    parser.add_argument("--samples-per-class", type=int, default=120, help="Rows per class for demo_samples.csv")
    parser.add_argument("--replay-benign-count", type=int, default=25, help="BENIGN rows at start of replay sequence")
    parser.add_argument("--replay-attack-per-class", type=int, default=6, help="ATTACK rows per class in replay")
    parser.add_argument("--alert-threshold", type=float, default=0.70, help="Default alert confidence threshold")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    datasets_dir = (workspace / args.datasets_dir).resolve()
    checkpoints_dir = (workspace / args.checkpoints_dir).resolve()
    assets_dir = (workspace / args.assets_dir).resolve()

    np.random.seed(args.seed)

    print("Loading sampled dataset...")
    sampled_raw = load_sampled_dataset(
        datasets_dir=datasets_dir,
        rows_per_file=args.rows_per_file,
        chunksize=args.chunksize,
        random_seed=args.seed,
    )

    print("Cleaning data...")
    cleaned = clean_dataset(sampled_raw)

    print("Inferring training labels from full dataset...")
    training_label_names = compute_training_label_names(
        datasets_dir=datasets_dir,
        min_samples=args.training_min_samples,
        chunksize=args.chunksize,
    )

    print("Filtering and balancing classes...")
    balanced = filter_and_balance_classes(
        df=cleaned,
        valid_labels=training_label_names,
        benign_label="BENIGN",
        benign_cap=args.benign_cap,
        random_seed=args.seed,
    )

    print("Extracting features...")
    features, labels, zero_var_columns = extract_features_and_labels(balanced)

    label_names = training_label_names
    if len(label_names) < 2:
        raise ValueError("Need at least two classes for a meaningful IDS demo.")

    checkpoint_path = find_best_checkpoint(checkpoints_dir)
    model = load_model(checkpoint_path, compile=False)

    if not isinstance(model.input_shape, tuple) or len(model.input_shape) != 4:
        raise ValueError(f"Unexpected model input shape: {model.input_shape}")

    output_classes = int(model.output_shape[-1])
    if len(label_names) != output_classes:
        raise ValueError(
            "Label count does not match model output width. "
            f"labels={len(label_names)}, model_outputs={output_classes}."
        )

    grid_size = int(model.input_shape[1])
    target_features = grid_size * grid_size

    if features.shape[1] > target_features:
        raise ValueError(
            f"Feature count ({features.shape[1]}) exceeds model capacity ({target_features}). "
            "Update feature selection before running demo."
        )

    print("Fitting scaler...")
    scaler = MinMaxScaler()
    scaler.fit(features.values)

    sampled_for_demo_parts: List[pd.DataFrame] = []
    working_df = features.copy()
    working_df["Label"] = labels

    for i, label in enumerate(label_names):
        class_df = working_df[working_df["Label"] == label]
        if class_df.empty:
            continue
        take = min(args.samples_per_class, len(class_df))
        sampled_for_demo_parts.append(class_df.sample(n=take, random_state=args.seed + i))

    sampled_for_demo = pd.concat(sampled_for_demo_parts, ignore_index=True)
    sampled_for_demo = sampled_for_demo.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)

    replay_df = build_replay_sequence(
        sampled_df=sampled_for_demo,
        benign_label="BENIGN",
        replay_benign_count=args.replay_benign_count,
        replay_attack_per_class=args.replay_attack_per_class,
        random_seed=args.seed,
    )

    save_assets(
        workspace=workspace,
        assets_dir=assets_dir,
        checkpoint_path=checkpoint_path,
        scaler=scaler,
        feature_columns=features.columns.tolist(),
        zero_var_columns=zero_var_columns,
        label_names=label_names,
        grid_size=grid_size,
        sampled_df=sampled_for_demo,
        replay_df=replay_df,
        default_alert_threshold=args.alert_threshold,
    )

    print("Asset preparation completed successfully.")


if __name__ == "__main__":
    main()
