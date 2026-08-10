"""
Deep Eye Vision — Deepfake Detection API
Loads a local Keras .h5 model and returns fake probability + Grad-CAM heatmap.
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# TensorFlow is heavy; import after FastAPI basics so /health can still start if TF fails later
import tensorflow as tf
from tensorflow.keras.models import Model

app = FastAPI(title="Deep Eye Vision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_MODEL_CANDIDATES = [
    Path(os.environ["MODEL_PATH"]) if os.environ.get("MODEL_PATH") else None,
    REPO_ROOT / "deepfake_model.h5",
    BACKEND_DIR / "models" / "deepfake_model.h5",
]

MODEL = None
INPUT_SIZE = (224, 224)
LAST_CONV_LAYER = None
MODEL_LOADED = False
MODEL_LOAD_ERROR: str | None = None


def _resolve_model_path() -> Path | None:
    for candidate in DEFAULT_MODEL_CANDIDATES:
        if candidate is None:
            continue
        path = Path(candidate).expanduser().resolve()
        if path.is_file():
            return path
    return None


def _find_last_conv_layer(model) -> str | None:
    for layer in reversed(model.layers):
        name = layer.__class__.__name__
        if "Conv" in name:
            return layer.name
    return None


def load_model() -> None:
    global MODEL, INPUT_SIZE, LAST_CONV_LAYER, MODEL_LOADED, MODEL_LOAD_ERROR

    path = _resolve_model_path()
    if path is None:
        MODEL_LOADED = False
        MODEL_LOAD_ERROR = (
            "Model file not found. Place deepfake_model.h5 at the repo root "
            "or set MODEL_PATH to the .h5 file."
        )
        print(f"[Deep Eye Vision] {MODEL_LOAD_ERROR}")
        return

    try:
        MODEL = tf.keras.models.load_model(str(path))
        shape = MODEL.input_shape
        # shape: (None, H, W, C) or list for multi-input
        if isinstance(shape, list):
            shape = shape[0]
        if shape and len(shape) >= 3 and shape[1] and shape[2]:
            INPUT_SIZE = (int(shape[1]), int(shape[2]))
        LAST_CONV_LAYER = _find_last_conv_layer(MODEL)
        MODEL_LOADED = True
        MODEL_LOAD_ERROR = None
        print(
            f"[Deep Eye Vision] Loaded {path} | input={INPUT_SIZE} | "
            f"last_conv={LAST_CONV_LAYER}"
        )
    except Exception as exc:  # noqa: BLE001 — surface load failures clearly
        MODEL = None
        MODEL_LOADED = False
        MODEL_LOAD_ERROR = str(exc)
        print(f"[Deep Eye Vision] Failed to load model: {exc}")


load_model()


def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.convert("RGB")
    image = image.resize(INPUT_SIZE, Image.Resampling.BILINEAR)
    img_array = np.array(image, dtype=np.float32) / 255.0
    return np.expand_dims(img_array, axis=0)


def predict_real_score(img_array: np.ndarray) -> float:
    """
    Model outputs a sigmoid score in [0, 1].
    Convention used by this API: close to 1 = REAL, close to 0 = FAKE.
    """
    preds = MODEL.predict(img_array, verbose=0)
    value = float(np.asarray(preds).reshape(-1)[0])
    return float(np.clip(value, 0.0, 1.0))


def make_gradcam_heatmap(img_array: np.ndarray) -> np.ndarray | None:
    if MODEL is None or LAST_CONV_LAYER is None:
        return None

    try:
        last_conv_layer = MODEL.get_layer(LAST_CONV_LAYER)
        grad_model = Model(
            inputs=MODEL.inputs,
            outputs=[last_conv_layer.output, MODEL.output],
        )

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img_array, training=False)
            # Emphasize regions that drive the model's decision toward FAKE
            # (low real-score). Use 1 - prediction when prediction is "real".
            score = predictions[:, 0]
            loss = 1.0 - score

        grads = tape.gradient(loss, conv_outputs)
        if grads is None:
            return None

        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
        heatmap = tf.maximum(heatmap, 0)
        max_val = tf.reduce_max(heatmap)
        heatmap = heatmap / (max_val + 1e-8)
        return heatmap.numpy()
    except Exception as exc:  # noqa: BLE001
        print(f"[Deep Eye Vision] Grad-CAM failed: {exc}")
        return None


def overlay_heatmap(
    original: Image.Image, heatmap: np.ndarray, alpha: float = 0.45
) -> Image.Image:
    """Resize heatmap to original image and blend with a jet-like colormap."""
    heat = Image.fromarray(np.uint8(np.clip(heatmap, 0, 1) * 255), mode="L")
    heat = heat.resize(original.size, Image.Resampling.BILINEAR)

    # Simple jet-ish colormap without matplotlib dependency
    heat_arr = np.array(heat, dtype=np.float32) / 255.0
    r = np.clip(1.5 - np.abs(4 * heat_arr - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * heat_arr - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * heat_arr - 1), 0, 1)
    colored = np.stack([r, g, b], axis=-1)
    colored = (colored * 255).astype(np.uint8)
    heat_rgb = Image.fromarray(colored, mode="RGB")

    base = original.convert("RGB")
    return Image.blend(base, heat_rgb, alpha=alpha)


def image_to_base64_png(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@app.post("/predict")
async def detect_deepfake(file: UploadFile = File(...)):
    if not MODEL_LOADED or MODEL is None:
        raise HTTPException(
            status_code=503,
            detail=MODEL_LOAD_ERROR
            or "Model not loaded. Place deepfake_model.h5 at the repo root or set MODEL_PATH.",
        )

    if file.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only JPEG images are accepted")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image file")

    img_array = preprocess_image(image)
    real_score = predict_real_score(img_array)
    fake_probability = round(1.0 - real_score, 4)
    is_fake = fake_probability >= 0.5

    heatmap_base64 = None
    heatmap = make_gradcam_heatmap(img_array)
    if heatmap is not None:
        overlay = overlay_heatmap(image, heatmap)
        heatmap_base64 = image_to_base64_png(overlay)

    return {
        "fake_probability": fake_probability,
        "is_fake": is_fake,
        "heatmap_base64": heatmap_base64,
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": MODEL_LOADED,
        "input_size": list(INPUT_SIZE),
        "last_conv_layer": LAST_CONV_LAYER,
        "error": MODEL_LOAD_ERROR,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
