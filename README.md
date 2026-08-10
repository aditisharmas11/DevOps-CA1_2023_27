# 🌾 SmartAgri — AI-Based Crop Recommendation System

## DevOps CA-1 | Hackathon Challenge Based Group Project

---

# 👥 Team Details

### Group Size: 4 Students

| Student ID | Name | Division | GitHub |
|---|---|---|---|
| 23070122265 | **Mithlesh Yadav** | TH2 | [MITHLESH55](https://github.com/MITHLESH55) |
| 23070122261 | **Adarsh Jha** | TH2 | [AdarshCodes1221](https://github.com/AdarshCodes1221) |
| 23070122280 | **Prabin Yadav** | TH2 | [Prabin-yadav](https://github.com/Prabin-yadav) |
| 23070122232 | **Velagala Prapul Krishna Reddy** | TH2 | [prapulreddy7](https://github.com/prapulreddy7) |

---

# 🏆 Selected Hackathon Challenge

### Hackathon: Tech Eximius 2026

**Platform:** Unstop

**Challenge:** Tech Eximius 2026

**Official Challenge Link:**

https://unstop.com/hackathons/tech-eximius-2026-tech-circle-1690635

The team selected this hackathon/challenge as part of the **DevOps CA-1 Challenge Selection Task**.

The objective of the CA task was to identify an existing:

- Hackathon challenge
- Kaggle challenge
- Open-source challenge
- Linux Foundation challenge
- Bug / issue requiring a solution

We selected the Hackathon challange
The selected challenge was then recorded by the group in the provided class spreadsheet.


---

# 📌 Selected Problem / Project

## AI-Based Crop Recommendation System

The project focuses on building an AI-powered agricultural decision-support system that combines:

- Crop Recommendation
- Fertilizer Recommendation
- Yield Prediction

The goal is to provide farmers with useful recommendations using soil parameters, location, environmental information and historical agricultural data.

---

# 🎯 Problem Statement

Indian farmers often make crop and fertilizer decisions with limited data.

The project identifies several challenges:

- Farmers have limited access to data-driven crop recommendations.
- Crop and fertilizer decisions depend on several factors such as soil, location and season.
- Yield prediction is difficult without historical agricultural information.
- There is no single system connecting **crop selection + fertilizer recommendation + yield estimation** into one recommendation pipeline.
- Agricultural extension services have limited rural reach.

The proposed system addresses this by creating a unified AI pipeline that takes soil parameters and location information and provides:

1. **Top-3 crop recommendations**
2. **Best fertilizer recommendation**
3. **Expected yield range**

The intended target users are **smallholder farmers across India with basic soil-test access**.

---

# 💡 Proposed Solution

SmartAgri is a web-based AI decision-support platform.

The system accepts farmer/field information and processes it through multiple machine-learning models.

```text
Farmer Input
     ↓
Soil + Location + Season + Irrigation
     ↓
Rainfall Enrichment
     ↓
Feature Engineering
     ↓
AI / ML Models
     ↓
┌──────────────────────────────┐
│ Crop Recommendation          │
│ Fertilizer Recommendation    │
│ Yield Prediction             │
└──────────────────────────────┘
     ↓
Unified Recommendation
```

---

# 🌾 Main Features

### 1. Crop Recommendation

Recommends suitable crops based on:

- NPK values
- Soil pH
- Soil type
- Temperature
- Humidity
- Season
- District
- Irrigation
- Rainfall

The system ranks suitable crops and provides confidence/suitability scores.

The crop dataset contains approximately **57,000 records covering 57 crops**.

---

### 2. 🧪 Fertilizer Recommendation

The system recommends an appropriate fertilizer based on:

- Soil type
- Nitrogen
- Phosphorus
- Potassium
- Crop
- Growth stage
- Irrigation

The fertilizer dataset contains approximately **10,000 records** and covers seven fertilizers.

---

### 3. 📈 Yield Prediction

The system estimates expected crop yield using historical agricultural data.

The yield dataset contains approximately **345,658 records**, with information including:

- State
- Season
- Crop
- Rainfall
- Fertilizer

---

### 4. 🌧️ Rainfall Enrichment

District-wise rainfall information is used to add environmental context to the recommendations.

The rainfall dataset contains **641 records** containing monthly and seasonal rainfall averages.

---

# 🤖 Machine Learning Models

## Crop Recommendation

**Algorithms:**

- Random Forest
- XGBoost

**Task:** Multi-class classification

**Dataset:** 57,000 records / 57 crops

Expected accuracy: approximately **98–99%**.

The evaluated models achieved approximately **99.9% accuracy**, with XGBoost selected for the crop recommendation system.

---

## Fertilizer Recommendation

**Algorithm:**

- Gradient Boosting / Random Forest evaluation

**Task:** Multi-class classification

**Dataset:** 10,000 records / 7 fertilizers

The project reports approximately **95–97% expected accuracy**, with Random Forest selected in the presented validation results.

---

## Yield Prediction

**Algorithms evaluated:**

- Extra Trees
- Random Forest
- XGBoost
- LightGBM

**Task:** Regression

The selected model is **Extra Trees**, with:

- R² = **0.949**
- RMSE = **2.496**
- MAE = **0.701**

---

# 📊 Overall Results

The project combines multiple factors to generate an overall recommendation.

| Factor | Weight |
|---|---:|
| Suitability | 0.35 |
| Yield | 0.15 |
| Region | 0.10 |
| Irrigation | 0.10 |
| Presence | 0.10 |
| Season | 0.20 |

The presented overall system score/accuracy is **94.23%**.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────┐
                    │  Farmer Inputs   │
                    │                  │
                    │ NPK / pH         │
                    │ Season           │
                    │ District         │
                    │ Irrigation       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Rainfall         │
                    │ Enrichment       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Feature          │
                    │ Engineering      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │ Crop Model │ │ Fertilizer │ │ Yield Model│
       │            │ │ Model      │ │            │
       │ XGBoost    │ │ ML Model   │ │ ExtraTrees │
       └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                 ┌──────────────────────┐
                 │ Unified Farmer Output │
                 │                      │
                 │ Top Crops             │
                 │ Fertilizer            │
                 │ Yield Estimate        │
                 │ Planting Guidance     │
                 └──────────────────────┘
```

The project architecture follows the flow described in the project presentation: farmer input → rainfall enrichment → feature engineering → three ML models → combined farmer output.

---

# 🖥️ Technology Used

### Programming

- Python

### Web Application

- Streamlit
- HTML
- CSS

### Machine Learning

- Scikit-learn
- XGBoost
- LightGBM
- Random Forest
- Extra Trees
- Gradient Boosting

### Data Processing

- Pandas
- NumPy

### Visualization

- Matplotlib
- Seaborn

### Version Control

- Git
- GitHub

---

# 📂 Project Modules

```text
SmartAgri
│
├── Crop Recommendation
├── Fertilizer Recommendation
├── Yield Prediction
├── Rainfall Enrichment
├── Feature Engineering
├── Model Training
├── Model Evaluation
├── Streamlit Dashboard
└── Testing
```

---

# 👨‍💻 Team Contributions

## 23070122265 — Mithlesh Yadav

**Role: Team Member**

Contributions include:

- Hackathon/challenge research
- Agricultural problem analysis
- Project development
- Testing and validation
- Documentation

GitHub: [MITHLESH55](https://github.com/MITHLESH55)

---

## 23070122261 — Adarsh Jha

**Role: Team Member**

Contributions include:

- Challenge research
- Application development
- Testing and debugging
- Git/GitHub collaboration
- Documentation

GitHub: [AdarshCodes1221](https://github.com/AdarshCodes1221)

---

## 23070122280 — Prabin Yadav

**Role: Team Member**

Contributions include:

- Streamlit dashboard development
- UI/UX implementation
- Integration of AI recommendation modules
- Crop/fertilizer/yield workflow integration
- Testing and debugging
- Git/GitHub repository management

GitHub: [Prabin-yadav](https://github.com/Prabin-yadav)

---

## 23070122232 — Velagala Prapul Krishna Reddy

**Role: Team Member**

Contributions include:

- Machine-learning/data processing work
- Model evaluation
- Agricultural dataset analysis
- Testing
- Documentation

GitHub: [prapulreddy7](https://github.com/prapulreddy7)

---

# 🔗 GitHub Submission

The project is maintained using Git and GitHub as required for the DevOps CA-1 submission.

### Parent Repository

**DevOps CA-1 Repository:**

`aditisharmas11/DevOps-CA1_2023_27`

The team created/forked the repository, cloned it locally, developed the project and will push the final project implementation to the assigned GitHub repository.

---

# 🔄 Git / GitHub Workflow

```text
College Repository
       ↓
     Fork
       ↓
     Clone
       ↓
 Team Development
       ↓
   Local Testing
       ↓
  Git Add / Commit
       ↓
     Git Push
       ↓
Final GitHub Submission
```

---

# 📅 CA-1 Assignment Details

This project was completed as part of the **DevOps CA-1 Task 3**.

### Task Requirements

Students were required to:

1. Form a group of maximum four students.
2. Find a suitable:
   - Bug / issue
   - Hackathon challenge
   - Kaggle challenge
   - Open-source challenge
   - Linux Foundation challenge
3. Enter the selected challenge/problem statement in the provided spreadsheet.
4. Groups were assigned problems based on the order in which they filled the sheet.
5. No other group could select the same problem statement.
6. Complete the project based on the selected challenge.
7. Push the final repository to GitHub.

### Submission Deadline

**10 August 2026**

---

# 📝 Challenge Selection Record

| Field | Details |
|---|---|
| Course | DevOps |
| Assessment | CA-1 |
| Task | Task 3 |
| Group Size | 4 |
| Division | TH2 |
| Selected Challenge | Tech Eximius 2026 |
| Platform | Unstop |
| Project | AI-Based Crop Recommendation System |
| Submission | GitHub |
| Deadline | 10 August 2026 |

---

# ⚠️ Project Limitations

The project presentation identifies several limitations:

### Fertilizer Recommendation Scope

The fertilizer model covers only seven crops. For the remaining crops, the system uses NPK-based rule logic rather than a machine-learning recommendation.

### Static Rainfall Data

District rainfall values are based on 30-year averages and may not accurately represent current climate variability.

### Yield Prediction

The yield dataset contains post-harvest aggregates, meaning the yield model should be considered a **historical benchmark rather than a genuine pre-planting predictor**.

### Scope

The system is designed primarily for smallholder farmers in India with basic soil-test access and relies on historical datasets and correct user-provided information.

---

# 🚀 Future Scope

Possible future improvements include:

- Real-time weather integration
- Expanded fertilizer recommendations
- Crop price prediction
- Mobile application for farmers
- Real-time agricultural monitoring

---

# 📚 References

1. Dahiphale, V. et al. (2023). *Smart Farming Crop Recommendation using Machine Learning.*
2. Waheed, A. et al. (2024). *Crop Recommendation System using Machine Learning and Explainable AI.*
3. van Klompenburg, T. et al. (2020). *Crop Yield Prediction using Machine Learning: A Systematic Literature Review.*
4. Chen, T. & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System.*
5. Breiman, L. (2001). *Random Forests.*

---

# 🌾 Conclusion

SmartAgri aims to combine crop recommendation, fertilizer guidance and yield estimation into a single AI-powered agricultural decision-support system.

The project was selected and developed as part of the **DevOps CA-1 Task 3 challenge-based group assignment**.

---

## 👥 Group

**Mithlesh Yadav • Adarsh Jha • Prabin Yadav • Velagala Prapul Krishna Reddy**

### TH2 | DevOps CA-1 | 2026

🌾 **Smart Farming. Better Decisions. Better Future.**
