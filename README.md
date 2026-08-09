# 🧠 Mental Health Screening System

An AI-powered mental health screening system for students that combines **machine learning models** with an **autonomous agent** to predict stress levels and depression risk.

---

## 📌 Project Overview

| Component | Description |
|-----------|-------------|
| **Stress ML Model** | Predicts stress levels (Low/Moderate/High) from lifestyle factors |
| **Depression ML Model** | Predicts depression risk from Kaggle student survey data (27,868 records) |
| **Autonomous Agent** | Interacts with users, calculates risk scores, and takes appropriate actions |

### Key Features
- ✅ 91.35% accurate stress prediction using stacking ensemble  
- ✅ Autonomous agent with perception, reasoning, decision, and action capabilities  
- ✅ Transparent, explainable risk calculation with weighted formula  
- ✅ Tool integration (logging, resource fetching, escalation simulation)  

---

## 📊 Datasets Used

| Dataset | Samples | Features | Target |
|---------|---------|----------|--------|
| Student Stress Factors | 520 students | 5 lifestyle factors | Stress Level (1-5) |
| Kaggle Student Depression | 27,868 students | 18 features | Suicidal Thoughts (Yes/No) |

---

## 🤖 Models Used

### Stacking Ensemble Architecture

| Level | Stress Model | Depression Model |
|-------|--------------|------------------|
| **Base Model 1** | Random Forest (100 trees) | Random Forest (200 trees) |
| **Base Model 2** | XGBoost (100 trees) | XGBoost (200 trees) |
| **Base Model 3** | - | LightGBM (300 estimators) |
| **Meta-Learner** | Logistic Regression | Logistic Regression |

### Why Stacking Ensemble?
- Combines strengths of multiple algorithms  
- Random Forest handles non-linear relationships  
- XGBoost captures complex patterns  
- LightGBM provides fast training on large datasets  
- Logistic Regression prevents overfitting  

---

## 🤖 Autonomous Agent (Agentic AI)

### Agent Architecture
**Perception → Reasoning → Decision → Action → Tools**

### Risk Calculation Formula (Transparent & Explainable)

    Risk Score =
    (6 - sleep) × 0.30 +          # Poor sleep = higher risk (30%)
    (headaches) × 0.25 +          # More headaches = higher risk (25%)
    (study_load) × 0.20 +         # Higher load = higher risk (20%)
    (6 - academic) × 0.15 +       # Poor academics = higher risk (15%)
    (6 - extracurricular) × 0.10  # Fewer activities = higher risk (10%)

### Decision Mapping

| Risk Score | Stress Level | Agent Action |
|------------|--------------|--------------|
| 0.0 - 2.0 | Low Stress 🟢 | Provide Reassurance & Wellness Tips |
| 2.0 - 3.5 | Moderate Stress 🟡 | Recommend Resources & Counseling |
| 3.5 - 5.0 | High Stress 🔴 | Escalate to Human Counselor |

### Agent Capabilities

| Agentic AI Concept | Implementation |
|-------------------|----------------|
| **Perception** | Collects user inputs via interactive questionnaire |
| **Reasoning** | Calculates risk using weighted clinical formula |
| **Decision** | Maps risk score to appropriate action |
| **Action** | Executes response (reassure/resources/escalate) |
| **Tool Use** | Logs interactions, fetches resources, simulates escalation |
| **Memory** | Stores conversation context and history |
| **Transparency** | Shows internal reasoning and risk components |

---

## 📈 Results

### ML Model Performance

| Model | Accuracy | F1-Score |
|-------|----------|----------|
| **Stress Prediction** | **91.35%** | 91.38% |
| **Depression Risk (Kaggle)** | **85%+** | 85%+ |

### Stress Model - Per Class Performance

| Stress Level | Precision | Recall | F1-Score |
|--------------|-----------|--------|----------|
| Low | 98% | 95% | 96% |
| Moderate | 85% | 92% | 88% |
| High | 89% | 86% | 87% |

### Agent Test Results

| Input Scenario | Risk Score | Prediction | Agent Action |
|----------------|------------|------------|--------------|
| Perfect lifestyle (5,1,5,1,5) | 1.0 | Low Stress 🟢 | Reassurance |
| Average lifestyle (3,3,3,3,3) | 3.0 | Moderate Stress 🟡 | Resources |
| High stress (1,5,1,5,1) | 5.0 | High Stress 🔴 | Escalate |

---

## 🔑 Key Findings

| Finding | Implication |
|---------|-------------|
| **Sleep quality** is the most important predictor (30% weight) | Interventions should focus on sleep hygiene |
| **Kaggle dataset** with 27,868 samples provides robust training | Model generalizes well to diverse populations |
| **Stacking ensemble** improved accuracy by 5% | Ensemble methods are valuable for mental health prediction |
| **Rule-based agent** provides transparency and trust | Users understand why they received a certain result |

---

## 🛠️ Technologies Used

Python 3.11 | Pandas | NumPy | Scikit-learn | XGBoost | LightGBM | Matplotlib | Seaborn | Joblib

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python src/agent.py
python main.py