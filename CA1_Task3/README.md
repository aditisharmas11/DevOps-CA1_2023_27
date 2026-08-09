# Kaggle Challenge: Titanic MLOps Pipeline

## 👥 Team Members

| PRN | Name |
| :--- | :--- |
| **24070122501** | Aryan Bhadange |
| **24070122508** | Atharva More |
| **24070122510** | Neel Khule |
| **24070122515** | Tanmay Salunkhe |

---

## 📌 Problem Statement
Implementation of an end-to-end DevOps/MLOps continuous integration pipeline for the [Kaggle Titanic Competition](https://www.kaggle.com/competitions/titanic).

## 🏗️ Architecture & Workflow
1. **Model Training (`train.py`):** Preprocesses raw Titanic dataset, trains a Random Forest classifier, and exports model artifacts (`model.joblib`) alongside performance metrics (`metrics.txt`).
2. **REST API (`app.py`):** Serves model predictions via FastAPI endpoint (`/predict`).
3. **Automated Testing (`test_app.py`):** Executes unit tests using Pytest and FastAPI TestClient.
4. **Containerization (`Dockerfile`):** Packages application runtime environment and generates fresh model artifacts on container creation.
5. **CI/CD Pipeline (`.github/workflows/cml.yml`):** Automated GitHub Actions workflow to train, test, and build Docker containers on code pushes.
