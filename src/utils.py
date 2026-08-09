import os, joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_score, recall_score, f1_score

def create_folder_structure():
    for f in ['data/raw','data/processed','models','results/figures','notebooks','src']:
        os.makedirs(f, exist_ok=True)
    print("✅ Folder structure ready")

def save_model(model, scaler, name):
    joblib.dump(model,  f'models/{name}_model.pkl')
    joblib.dump(scaler, f'models/{name}_scaler.pkl')

def plot_confusion_matrix(y_true, y_pred, title, save_path):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(title); plt.ylabel('True'); plt.xlabel('Predicted')
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150); plt.close()

def plot_feature_importance(feature_names, importance_values, title, save_path, top_n=15):
    imp = pd.DataFrame({'feature': feature_names, 'importance': importance_values})
    imp = imp.sort_values('importance', ascending=False).head(top_n)
    plt.figure(figsize=(10,6))
    plt.barh(imp['feature'], imp['importance'])
    plt.xlabel('Importance'); plt.title(title); plt.gca().invert_yaxis()
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150); plt.close()
    return imp

def print_metrics_report(y_true, y_pred, model_name, class_names):
    print(f"\n{'='*60}\n{model_name} – CLASSIFICATION REPORT\n{'='*60}")
    print(classification_report(y_true, y_pred, target_names=class_names))
    m = {
        'accuracy':  accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall':    recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1':        f1_score(y_true, y_pred, average='weighted', zero_division=0),
    }
    print(f"Accuracy: {m['accuracy']:.4f}  F1: {m['f1']:.4f}")
    return m