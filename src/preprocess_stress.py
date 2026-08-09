import pandas as pd

def preprocess_stress_data():
    print("="*60 + "\nPREPROCESSING STRESS DATASET\n" + "="*60)
    df = pd.read_csv('data/raw/Student_Stress_Factors.csv')
    df.columns = ['sleep_quality','headaches_weekly','academic_performance',
                  'study_load','extracurricular_weekly','stress_level']
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()
    for col in df.columns:
        df[col] = df[col].clip(1,5).round().astype(int)
    df['stress_category'] = df['stress_level'].apply(
        lambda x: 0 if x<=2 else (1 if x<=3 else 2))
    df.to_csv('data/processed/stress_processed.csv', index=False)
    print(f"✅ Saved shape={df.shape}")
    return df, ['sleep_quality','headaches_weekly','academic_performance',
                'study_load','extracurricular_weekly']