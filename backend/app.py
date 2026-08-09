import os, sys, json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

import joblib
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

stress_model    = joblib.load(os.path.join(BASE, 'models/stress_model.pkl'))
stress_scaler   = joblib.load(os.path.join(BASE, 'models/stress_scaler.pkl'))
stress_features = joblib.load(os.path.join(BASE, 'models/stress_feature_cols.pkl'))

depression_model    = joblib.load(os.path.join(BASE, 'models/kaggle_depression_model.pkl'))
depression_scaler   = joblib.load(os.path.join(BASE, 'models/kaggle_scaler.pkl'))
depression_features = joblib.load(os.path.join(BASE, 'models/kaggle_feature_cols.pkl'))

os.makedirs(os.path.join(BASE, 'logs'), exist_ok=True)

def engineer_stress(features):
    df = pd.DataFrame([features])
    df['sleep_headache_interaction'] = df['sleep_quality'] * df['headaches_weekly']
    df['academic_load_ratio']        = df['study_load'] / (df['academic_performance'] + 0.01)
    df['stress_risk_score']          = (
        df['sleep_quality']        * 0.3 +
        df['headaches_weekly']     * 0.25 +
        df['study_load']           * 0.25 +
        (5 - df['academic_performance'])   * 0.1 +
        (5 - df['extracurricular_weekly']) * 0.1
    )
    df['sleep_category']    = pd.cut(df['sleep_quality'],    bins=[0,2,3,5], labels=[0,1,2]).astype(float)
    df['headache_category'] = pd.cut(df['headaches_weekly'], bins=[0,2,3,5], labels=[0,1,2]).astype(float)
    return df

def log_interaction(data):
    log_path = os.path.join(BASE, 'logs/agent_interactions.log')
    with open(log_path, 'a') as f:
        f.write(json.dumps({**data, 'timestamp': datetime.now().isoformat()}) + '\n')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/predict/stress', methods=['POST'])
def predict_stress():
    body = request.json
    features = {
        'sleep_quality':          float(body['sleep_quality']),
        'headaches_weekly':       float(body['headaches_weekly']),
        'academic_performance':   float(body['academic_performance']),
        'study_load':             float(body['study_load']),
        'extracurricular_weekly': float(body['extracurricular_weekly']),
    }

    sleep_risk    = 6 - features['sleep_quality']
    headache_risk = features['headaches_weekly']
    academic_risk = 6 - features['academic_performance']
    load_risk     = features['study_load']
    extra_risk    = 6 - features['extracurricular_weekly']

    total_risk = (
        sleep_risk    * 0.30 +
        headache_risk * 0.25 +
        load_risk     * 0.20 +
        academic_risk * 0.15 +
        extra_risk    * 0.10
    )

    if total_risk <= 2.0:
        pred, label, confidence = 0, 'Low Stress',      min(0.95, 0.85 + (2.0 - total_risk) / 10)
    elif total_risk <= 3.5:
        pred, label, confidence = 1, 'Moderate Stress', 0.80
    else:
        pred, label, confidence = 2, 'High Stress',     min(0.95, 0.85 + (total_risk - 3.5) / 10)

    if pred == 0:   action = 'provide_reassurance'
    elif pred == 1: action = 'recommend_resources'
    else:           action = 'escalate_to_human'

    result = {
        'risk_level': pred,
        'label':      label,
        'confidence': round(confidence * 100, 1),
        'risk_score': round(total_risk, 2),
        'action':     action,
    }
    log_interaction({'type': 'stress', **result})
    return jsonify(result)

@app.route('/predict/depression', methods=['POST'])
def predict_depression():
    body = request.json

    # Rule-based scoring using same factors as ML model
    academic_pressure = float(body.get('academic_pressure', 3))
    work_pressure     = float(body.get('work_pressure', 0))
    study_satisfaction= float(body.get('study_satisfaction', 3))
    sleep_hours       = float(body.get('sleep_hours', 6))
    financial_stress  = float(body.get('financial_stress', 2))
    work_study_hours  = float(body.get('work_study_hours', 6))
    suicidal_thoughts = int(body.get('suicidal_thoughts', 0))
    family_history    = int(body.get('family_history', 0))
    dietary_habits    = int(body.get('dietary_habits', 2))  # 1=unhealthy,2=moderate,3=healthy

    # Risk score calculation
    sleep_risk        = max(0, (8 - sleep_hours) / 8 * 5)
    pressure_risk     = (academic_pressure + work_pressure) / 2
    satisfaction_risk = 6 - study_satisfaction
    financial_risk    = financial_stress
    hours_risk        = min(5, work_study_hours / 3)
    diet_risk         = 4 - dietary_habits
    history_risk      = 3 if family_history else 0
    suicidal_risk     = 5 if suicidal_thoughts else 0

    total_risk = (
        pressure_risk     * 0.25 +
        sleep_risk        * 0.20 +
        satisfaction_risk * 0.15 +
        financial_risk    * 0.15 +
        hours_risk        * 0.10 +
        diet_risk         * 0.05 +
        history_risk      * 0.05 +
        suicidal_risk     * 0.05
    )

    if total_risk <= 1.5:   severity, level = 'Low Risk',      0
    elif total_risk <= 3.0: severity, level = 'Moderate Risk', 1
    else:                   severity, level = 'High Risk',     2

    if level == 0:   action = 'provide_reassurance'
    elif level == 1: action = 'recommend_resources'
    else:            action = 'escalate_to_human'

    high_risk = suicidal_thoughts == 1

    result = {
        'total_score': round(total_risk, 2),
        'severity':    severity,
        'level':       level,
        'high_risk':   high_risk,
        'action':      action,
    }
    log_interaction({'type': 'depression', **result})
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)