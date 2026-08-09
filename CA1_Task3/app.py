from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI(title="Kaggle Titanic Predictor API")

model = joblib.load('model.joblib')

class PassengerData(BaseModel):
    Pclass: int
    Sex: str
    Age: float
    SibSp: int
    Parch: int
    Fare: float

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Kaggle Titanic API"}

@app.post("/predict")
def predict(passenger: PassengerData):
    sex_num = 1 if passenger.Sex.lower() == 'female' else 0
    input_data = pd.DataFrame([{
        'Pclass': passenger.Pclass,
        'Sex': sex_num,
        'Age': passenger.Age,
        'SibSp': passenger.SibSp,
        'Parch': passenger.Parch,
        'Fare': passenger.Fare
    }])

    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]

    return {
        "survived": int(prediction),
        "survival_probability": round(float(probability), 4)
    }
