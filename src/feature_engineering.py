"""Feature Engineering – Stress and Depression datasets."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, PolynomialFeatures


STRESS_ORIG = ['sleep_quality', 'headaches_weekly', 'academic_performance',
               'study_load', 'extracurricular_weekly']


def engineer_stress_features(df: pd.DataFrame):
    original_features = STRESS_ORIG[:]

    df['sleep_headache_interaction'] = df['sleep_quality'] * df['headaches_weekly']
    df['academic_load_ratio']        = df['study_load'] / (df['academic_performance'] + 0.01)
    df['load_vs_extracurricular']    = df['study_load'] / (df['extracurricular_weekly'] + 0.01)
    df['sleep_performance_product']  = df['sleep_quality'] * df['academic_performance']

    poly = PolynomialFeatures(degree=2, include_bias=False)
    top3 = df[['sleep_quality', 'headaches_weekly', 'study_load']].values
    poly_arr   = poly.fit_transform(top3)
    poly_names = poly.get_feature_names_out(['sleep_quality', 'headaches_weekly', 'study_load'])
    linear_set = {'sleep_quality', 'headaches_weekly', 'study_load'}
    new_poly   = [n for n in poly_names if n not in linear_set]
    poly_df    = pd.DataFrame(
        poly_arr[:, [list(poly_names).index(n) for n in new_poly]],
        columns=['poly_' + n.replace(' ', '_') for n in new_poly],
        index=df.index
    )
    df = pd.concat([df, poly_df], axis=1)

    df['stress_risk_score'] = (
        (5 - df['sleep_quality'])          * 0.30 +
        df['headaches_weekly']             * 0.25 +
        df['study_load']                   * 0.25 +
        (5 - df['academic_performance'])   * 0.10 +
        (5 - df['extracurricular_weekly']) * 0.10
    )

    df['sleep_category']    = pd.cut(df['sleep_quality'],      bins=[0,2,4,5],  labels=[0,1,2]).astype(int)
    df['headache_category'] = pd.cut(df['headaches_weekly'],   bins=[-1,1,3,5], labels=[0,1,2]).astype(int)
    df['load_category']     = pd.cut(df['study_load'],         bins=[0,2,3,5],  labels=[0,1,2]).astype(int)

    new_feats = (
        ['sleep_headache_interaction','academic_load_ratio',
         'load_vs_extracurricular','sleep_performance_product',
         'stress_risk_score','sleep_category','headache_category','load_category']
        + ['poly_' + n.replace(' ', '_') for n in new_poly]
    )
    all_features = original_features + new_feats
    print(f"✅ Stress features: {len(original_features)} orig + {len(new_feats)} engineered = {len(all_features)} total")
    return df, all_features


def engineer_depression_features(df: pd.DataFrame, feature_cols: list):
    new_cols = []
    if 'Academic_Pressure' in df.columns and 'Work/Study_Hours' in df.columns:
        df['pressure_hours_interaction'] = df['Academic_Pressure'] * df['Work/Study_Hours']
        new_cols.append('pressure_hours_interaction')
    if 'Financial_Stress' in df.columns and 'Sleep_Duration_encoded' in df.columns:
        df['finance_sleep_interaction'] = df['Financial_Stress'] * df['Sleep_Duration_encoded']
        new_cols.append('finance_sleep_interaction')
    if 'CGPA' in df.columns and 'Study_Satisfaction' in df.columns:
        df['cgpa_satisfaction_product'] = df['CGPA'] * df['Study_Satisfaction']
        new_cols.append('cgpa_satisfaction_product')
    if 'Age' in df.columns:
        df['age_bucket'] = pd.cut(df['Age'], bins=[0,22,26,35,100], labels=[0,1,2,3]).astype(float)
        new_cols.append('age_bucket')

    updated = feature_cols + [c for c in new_cols if c not in feature_cols]
    print(f"✅ Depression features: {len(feature_cols)} orig + {len(new_cols)} engineered = {len(updated)} total")
    return df, updated


def scale_features(X_train, X_test, feature_names):
    scaler = StandardScaler()
    Xtr = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_names, index=X_train.index)
    Xte = pd.DataFrame(scaler.transform(X_test),      columns=feature_names, index=X_test.index)
    return Xtr, Xte, scaler