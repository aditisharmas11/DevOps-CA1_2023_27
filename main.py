import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils import create_folder_structure
from src.preprocess_stress import preprocess_stress_data
from src.preprocess_kaggle import preprocess_kaggle_data
from src.augment_stress import augment_stress_dataset
from src.train_models import train_stress_model, train_kaggle_depression_model

def main():
    print("🚀 Starting Mental Health Screening Project\n")
    create_folder_structure()

    print("\n" + "="*70 + "\nSTEP 1: PREPROCESSING\n" + "="*70)
    preprocess_stress_data()
    preprocess_kaggle_data()

    print("\n" + "="*70 + "\nSTEP 2: DATA AUGMENTATION (Stress)\n" + "="*70)
    augment_stress_dataset(target_size=2500)

    print("\n" + "="*70 + "\nSTEP 3: MODEL TRAINING\n" + "="*70)
    _, _, sm = train_stress_model()
    _, _, dm = train_kaggle_depression_model()

    print("\n" + "="*70 + "\n📊 FINAL RESULTS\n" + "="*70)
    print(f"Stress   Accuracy={sm['accuracy']:.4f}  CV-Acc={sm['cv_accuracy']:.4f}  F1={sm['f1']:.4f}")
    print(f"Kaggle   Accuracy={dm['accuracy']:.4f}  CV-Acc={dm['cv_accuracy']:.4f}  F1={dm['f1']:.4f}  AUC={dm['roc_auc']:.4f}")
    print("\n✅ PROJECT COMPLETED")

if __name__ == "__main__":
    main()