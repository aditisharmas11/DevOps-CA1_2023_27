# Deep Eye Vision

AI deepfake image detector with Grad-CAM heatmaps. Upload a JPEG, get a fake-probability score, and see where the model focused.

You need **two terminals**: one for the backend (port `8000`), one for the frontend (port `8080`).

---

## Prerequisites

- **Node.js** 18+
- **Python** 3.10–3.12 (avoid mixing with a broken global Anaconda env — use a venv)
- Local model file: `deepfake_model.h5` at the **repo root** (~154 MB, not in git)

```text
deep-eye-vision/
  deepfake_model.h5   ← put the model here
  backend/
  src/
  package.json
  README.md
```

Optional custom path (PowerShell):

```powershell
$env:MODEL_PATH = "C:\path\to\deepfake_model.h5"
```

---

## 1. Run the backend

```powershell
cd C:\Users\Vedika\OneDrive\Desktop\projects\deep-eye-vision\backend

python -m venv .venv
.\.venv\Scripts\activate

# Important: use python -m pip so packages install INTO the venv
# (plain "pip" may still install into Anaconda)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python app.py
```

You should see the server start on **http://localhost:8000** (and a log that the model loaded).

### Check backend

In another terminal:

```powershell
curl http://localhost:8000/health
```

Expect `"model_loaded": true`. If it is `false`, the `.h5` file is missing or `MODEL_PATH` is wrong.

---

## 2. Run the frontend

Keep the backend running. Open a **second** terminal:

```powershell
cd C:\Users\Vedika\OneDrive\Desktop\projects\deep-eye-vision

npm install
npm run dev
```

Open **http://localhost:8080** in your browser.

1. Upload a **JPEG** image  
2. Click **Detect deepfake**  
3. You should see a fake score and an optional heatmap (Original / Heatmap toggle)

Vite proxies `/predict` and `/health` to `http://localhost:8000`.

---

## macOS / Linux

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

**Frontend** (second terminal, repo root)

```bash
npm install
npm run dev
```

---

## Common problems

| Problem | Fix |
|--------|-----|
| `No module named 'numpy'` (or other packages) while `(.venv)` is active | Reinstall with `python -m pip install -r requirements.txt`, not bare `pip` |
| `No module named 'tensorflow.keras'` | You installed into Anaconda base. Use a fresh `.venv` as above |
| Frontend “Analysis failed” | Backend not running, or `/health` shows `model_loaded: false` |
| Only JPEG accepted | Convert the image to `.jpg` / `.jpeg` |

Confirm the venv Python is used:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should include `backend\.venv\...`, not `anaconda3\...`.

---

## API quick reference

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/health` | `{ "status", "model_loaded", ... }` |
| `POST` | `/predict` | multipart form field `file` (JPEG) |

Example predict response:

```json
{
  "fake_probability": 0.82,
  "is_fake": true,
  "heatmap_base64": "<png base64 or null>"
}
```

---

## Notes

- Research / demo use only — not a forensic or legal verdict.
- Do **not** commit `deepfake_model.h5` (gitignored via `*.h5`).
