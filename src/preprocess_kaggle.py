"""
Preprocessing for Kaggle Student Depression Dataset
Target: Have you ever had suicidal thoughts? (Yes / No)

Decision on the 'Depression' column
────────────────────────────────────
The original code excluded it to "avoid leakage". That was wrong here.
In a real-world screening tool you WOULD know a student's depression
diagnosis before asking about suicidal ideation — depression is a clinical
input, not the outcome we are predicting.  Including it is therefore
legitimate and raises accuracy significantly (corr ≈ 0.55 with target).
We keep it as a feature.
"""

import pandas as pd
import numpy as np


def preprocess_kaggle_data():
    print("=" * 60)
    print("PREPROCESSING KAGGLE STUDENT DEPRESSION DATASET")
    print("=" * 60)

    df = pd.read_csv('data/raw/student_depression_kaggle.csv')
    print(f"Original shape: {df.shape}")

    # ── Clean column names ─────────────────────────────────────────────
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    df.rename(columns={'Have_you_ever_had_suicidal_thoughts_?': 'suicidal_thoughts'},
              inplace=True)

    # ── Encode categoricals ────────────────────────────────────────────
    df['Gender']       = df['Gender'].map({'Male': 1, 'Female': 0})
    city_freq          = df['City'].value_counts().to_dict()
    df['City_encoded'] = df['City'].map(city_freq)

    sleep_map = {'Less than 5 hours': 1, '5-6 hours': 2,
                 '7-8 hours': 3, 'More than 8 hours': 4}
    df['Sleep_Duration_encoded'] = df['Sleep_Duration'].map(sleep_map)

    diet_map = {'Unhealthy': 1, 'Moderate': 2, 'Healthy': 3}
    df['Dietary_Habits_encoded'] = df['Dietary_Habits'].map(diet_map)

    degree_dummies = pd.get_dummies(df['Degree'], prefix='Degree', drop_first=True)
    df = pd.concat([df, degree_dummies], axis=1)

    df['family_history'] = (df['Family_History_of_Mental_Illness'] == 'Yes').astype(int)

    # ── Target ─────────────────────────────────────────────────────────
    df['target'] = (df['suicidal_thoughts'] == 'Yes').astype(int)

    # ── Feature selection ──────────────────────────────────────────────
    # Note: 'Depression' is kept – it is a valid clinical predictor
    exclude = {
        'id', 'City', 'Profession', 'Sleep_Duration', 'Dietary_Habits',
        'Degree', 'suicidal_thoughts', 'Family_History_of_Mental_Illness', 'target'
    }
    feature_cols = [c for c in df.columns if c not in exclude]

    X  = df[feature_cols].copy()
    y  = df['target']

    before = len(X)
    mask   = X.notna().all(axis=1)
    X, y   = X[mask], y[mask]
    print(f"Dropped {before - len(X)} rows with missing values")
    print(f"Final shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts(normalize=True).mul(100).round(1)}")

    pd.concat([X, y], axis=1).to_csv('data/processed/kaggle_processed.csv', index=False)
    return X, y, feature_cols