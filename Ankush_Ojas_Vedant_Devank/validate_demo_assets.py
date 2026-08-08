from __future__ import annotations

from pathlib import Path

import pandas as pd

from inference_pipeline import IDSPredictor


def main() -> None:
    # Documentation-only edit added 2026-08-08: small comment for traceability.
    # This file's runtime logic is unchanged.
    workspace = Path(".").resolve()
    assets_dir = workspace / "artifacts"

    required_paths = [
        assets_dir / "preprocessing_meta.json",
        assets_dir / "scaler.joblib",
        assets_dir / "demo_samples.csv",
        assets_dir / "replay_sequence.csv",
    ]

    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required artifacts:\n" + "\n".join(missing))

    predictor = IDSPredictor(assets_dir=assets_dir)

    demo_samples = pd.read_csv(assets_dir / "demo_samples.csv")
    if demo_samples.empty:
        raise ValueError("demo_samples.csv is empty.")

    sample = demo_samples.head(5)
    output = predictor.predict(sample)

    if len(output) != len(sample):
        raise ValueError("Prediction row count does not match input row count.")

    required_output_cols = {"predicted_label", "confidence", "alert", "severity"}
    if not required_output_cols.issubset(output.columns):
        missing_cols = sorted(required_output_cols.difference(output.columns))
        raise ValueError(f"Missing expected output columns: {missing_cols}")

    if len(predictor.label_names) != predictor.model.output_shape[-1]:
        raise ValueError(
            "Label mapping size mismatch: "
            f"labels={len(predictor.label_names)} model_outputs={predictor.model.output_shape[-1]}"
        )

    print("Demo assets validation successful.")
    print(f"Loaded checkpoint: {predictor.checkpoint_path}")
    print(f"Classes: {predictor.label_names}")
    print("Sample predictions:")
    print(output[["Label", "predicted_label", "confidence", "alert", "severity"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
