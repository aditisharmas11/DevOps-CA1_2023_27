from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model


# Documentation-only note: timestamp 2026-08-08. This comment documents a
# non-functional edit across older files; it does not change behavior.
class IDSPredictor:
    """Reusable predictor for the IDS Streamlit demo."""

    def __init__(
        self,
        assets_dir: str | Path = "artifacts",
        checkpoint_path: str | Path | None = None,
        alert_threshold: float | None = None,
    ) -> None:
        self.assets_dir = Path(assets_dir).resolve()
        meta_path = self.assets_dir / "preprocessing_meta.json"
        scaler_path = self.assets_dir / "scaler.joblib"

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file missing: {meta_path}")
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler file missing: {scaler_path}")

        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.feature_columns: List[str] = list(self.meta["feature_columns"])
        self.label_names: List[str] = list(self.meta["label_names"])
        self.grid_size = int(self.meta["grid_size"])
        self.target_features = int(self.meta["target_features"])
        self.benign_label = str(self.meta.get("benign_label", "BENIGN"))

        default_threshold = float(self.meta.get("default_alert_threshold", 0.70))
        self.alert_threshold = float(alert_threshold) if alert_threshold is not None else default_threshold

        checkpoint_value = checkpoint_path if checkpoint_path is not None else self.meta["checkpoint_path"]
        self.checkpoint_path = self._resolve_checkpoint(checkpoint_value)

        self.scaler = joblib.load(scaler_path)
        self.model = load_model(self.checkpoint_path, compile=False)

        if self.model.input_shape[1] != self.grid_size or self.model.input_shape[2] != self.grid_size:
            raise ValueError(
                "Model input shape and metadata grid size mismatch. "
                f"Model shape={self.model.input_shape}, metadata grid={self.grid_size}"
            )

        self.probability_columns: Dict[str, str] = {
            label: f"prob_{self._slugify_label(label)}" for label in self.label_names
        }

    def _resolve_checkpoint(self, checkpoint_value: str | Path) -> Path:
        path = Path(checkpoint_value)
        if path.is_absolute():
            return path

        workspace_root = self.assets_dir.parent
        candidate = (workspace_root / path).resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {candidate}")
        return candidate

    @staticmethod
    def _slugify_label(label: str) -> str:
        value = re.sub(r"[^0-9A-Za-z]+", "_", label).strip("_").lower()
        return value if value else "unknown"

    def _validate_input_columns(self, df: pd.DataFrame) -> None:
        missing = [col for col in self.feature_columns if col not in df.columns]
        if missing:
            preview = ", ".join(missing[:10])
            extra = "..." if len(missing) > 10 else ""
            raise ValueError(f"Missing required feature columns: {preview}{extra}")

    def transform_features(self, df: pd.DataFrame) -> np.ndarray:
        """Convert raw feature dataframe into model-ready 4D tensor."""
        self._validate_input_columns(df)

        features = df[self.feature_columns].copy()
        features = features.apply(pd.to_numeric, errors="coerce")
        features.replace([np.inf, -np.inf], np.nan, inplace=True)

        # During demo playback we prefer resilience over hard failure.
        features = features.fillna(0.0)

        scaled = self.scaler.transform(features.values)

        if scaled.shape[1] > self.target_features:
            raise ValueError(
                f"Scaled feature width {scaled.shape[1]} exceeds target {self.target_features}."
            )

        if scaled.shape[1] < self.target_features:
            pad_count = self.target_features - scaled.shape[1]
            scaled = np.pad(scaled, ((0, 0), (0, pad_count)), mode="constant", constant_values=0)

        tensor = scaled.reshape(-1, self.grid_size, self.grid_size, 1).astype(np.float32)
        return tensor

    def predict(
        self,
        df: pd.DataFrame,
        alert_threshold: float | None = None,
    ) -> pd.DataFrame:
        """Return predictions, confidence, alert state, and class probabilities."""
        threshold = float(alert_threshold) if alert_threshold is not None else self.alert_threshold

        tensor = self.transform_features(df)
        probabilities = self.model.predict(tensor, verbose=0)

        pred_idx = np.argmax(probabilities, axis=1)
        pred_labels = [self.label_names[i] for i in pred_idx]
        confidences = np.max(probabilities, axis=1)

        alerts = [
            (label != self.benign_label) and (confidence >= threshold)
            for label, confidence in zip(pred_labels, confidences)
        ]

        severities = [self._severity(conf) if alert else "none" for conf, alert in zip(confidences, alerts)]

        results = df.copy().reset_index(drop=True)
        results["predicted_label"] = pred_labels
        results["confidence"] = np.round(confidences, 4)
        results["alert"] = alerts
        results["severity"] = severities

        for i, label in enumerate(self.label_names):
            col_name = self.probability_columns[label]
            results[col_name] = np.round(probabilities[:, i], 6)

        return results

    @staticmethod
    def _severity(confidence: float) -> str:
        if confidence >= 0.90:
            return "high"
        if confidence >= 0.80:
            return "medium"
        return "low"


def load_artifact_table(assets_dir: str | Path, filename: str) -> pd.DataFrame:
    path = Path(assets_dir).resolve() / filename
    if not path.exists():
        raise FileNotFoundError(f"Artifact file missing: {path}")
    return pd.read_csv(path)
