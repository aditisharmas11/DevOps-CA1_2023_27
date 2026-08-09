import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

def load_data():
    url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
    return pd.read_csv(url)

def preprocess_data(df):
    features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare']
    X = df[features].copy()
    y = df['Survived']

    X['Sex'] = X['Sex'].map({'male': 0, 'female': 1})
    X['Age'] = X['Age'].fillna(X['Age'].median())
    X['Fare'] = X['Fare'].fillna(X['Fare'].median())
    return X, y

def train_and_evaluate():
    df = load_data()
    X, y = preprocess_data(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)

    joblib.dump(model, 'model.joblib')

    with open('metrics.txt', 'w') as f:
        f.write("## 📊 Kaggle Titanic Model Performance Metrics\n")
        f.write(f"- **Accuracy:** {acc:.4f}\n")
        f.write(f"- **Precision:** {prec:.4f}\n")
        f.write(f"- **Recall:** {rec:.4f}\n")
        f.write(f"- **F1 Score:** {f1:.4f}\n")

    print("Training complete. model.joblib and metrics.txt generated.")

if __name__ == '__main__':
    train_and_evaluate()
