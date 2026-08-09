"""
Deepfake Detection Backend Server
==================================
Drop your model loading + prediction logic into the marked sections below.
"""

import os
import io
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

app = FastAPI(title="Deepfake Detector API")

# CORS – allows the Vite dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# 🔧 MODEL LOADING — Replace this section
# ──────────────────────────────────────────────
# Example for TensorFlow/Keras:
#   from tensorflow.keras.models import load_model
#   MODEL = load_model("model/deepfake_model.h5")
#
# Example for PyTorch:
#   import torch
#   MODEL = torch.load("model/deepfake_model.pth", map_location="cpu")
#   MODEL.eval()

MODEL = None  # ← replace with your loaded model


def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    🔧 PREPROCESS — Adjust to match YOUR model's input requirements.
    Common steps: resize, normalize, expand dims.
    """
    image = image.convert("RGB")
    image = image.resize((224, 224))  # ← change to your model's input size
    img_array = np.array(image, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # shape: (1, 224, 224, 3)
    return img_array


def predict(img_array: np.ndarray) -> float:
    """
    🔧 PREDICT — Replace with your model's inference call.
    Must return a float between 0 and 1.
      - close to 1 → REAL
      - close to 0 → FAKE

    Examples:
      TensorFlow:  return float(MODEL.predict(img_array)[0][0])
      PyTorch:     return float(torch.sigmoid(MODEL(tensor)).item())
    """
    # ── DEMO MODE (random prediction) ── remove this when you add your model
    return float(np.random.uniform(0, 1))


# ──────────────────────────────────────────────
# API endpoint — no changes needed here
# ──────────────────────────────────────────────
@app.post("/predict")
async def detect_deepfake(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only JPEG images are accepted")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image file")

    img_array = preprocess_image(image)
    score = predict(img_array)  # 0–1, where 1 = real

    # Convert: score close to 0 = fake, so fake_probability = 1 - score
    fake_probability = round(1.0 - score, 4)
    is_fake = fake_probability >= 0.5

    return {
        "fake_probability": fake_probability,
        "is_fake": is_fake,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
