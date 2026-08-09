import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

print('Loading and preparing data...')

# Load processed data (original 520 rows)
df = pd.read_csv('data/processed/stress_processed.csv')

# Use only original 5 features
feature_cols = ['sleep_quality', 'headaches_weekly', 'academic_performance', 
                'study_load', 'extracurricular_weekly']
X = df[feature_cols]
y = df['stress_category']

print(f'Using {len(df)} samples')
print(f'Class distribution:\n{y.value_counts()}')

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight={0: 1.0, 1: 1.5, 2: 1.2}
)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print(f'\nModel Accuracy: {accuracy_score(y_test, y_pred):.4f}')
print('\nClassification Report:')
print(classification_report(y_test, y_pred, target_names=['Low', 'Moderate', 'High']))

# Test cases
print('\n' + '='*50)
print('TESTING ON SPECIFIC CASES:')
print('='*50)

test_cases = [
    {'name': 'LOW STRESS', 'data': [[5, 1, 5, 1, 5]]},
    {'name': 'MODERATE STRESS', 'data': [[3, 3, 3, 3, 3]]},
    {'name': 'HIGH STRESS', 'data': [[1, 5, 1, 5, 1]]}
]

labels = {0: 'Low Stress', 1: 'Moderate Stress', 2: 'High Stress'}

for case in test_cases:
    X_test_case = scaler.transform(np.array(case['data']))
    pred = model.predict(X_test_case)[0]
    proba = model.predict_proba(X_test_case)[0]
    print(f"\n{case['name']}:")
    print(f"  Inputs: {case['data'][0]}")
    print(f"  Predicted: {labels[pred]}")
    print(f"  Confidence: {proba[pred]:.1%}")

# Save model
joblib.dump(model, 'models/stress_model_working.pkl')
joblib.dump(scaler, 'models/stress_scaler_working.pkl')
joblib.dump(feature_cols, 'models/stress_feature_cols_working.pkl')
print('\n✅ Working model saved!')
print('   Files saved:')
print('   - models/stress_model_working.pkl')
print('   - models/stress_scaler_working.pkl')
print('   - models/stress_feature_cols_working.pkl')