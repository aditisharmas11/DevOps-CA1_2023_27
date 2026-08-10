import os

import pandas as pd
import numpy as np
import sklearn.utils
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import ADASYN
from joblib import dump

DATA_FILE = './datasets/preprocessed_data.csv'
MODEL_FILE = './crop_model.h5'
SCALER_FILE = './scaler.joblib'

def main():
    df = pd.read_csv(DATA_FILE)

    seed = 2
    np.random.seed(seed)
    tf.random.set_seed(seed)
    tf.keras.utils.set_random_seed(seed)

    train_params = [
        'lat', 'long', 'Crop_Year',
        'organic_carbon', 'inorganic_carbon', 'clayey_soil',
        'clayey-skeletal_soil', 'loamy_soil', 'sandy_soil'
    ]

    df_subset = df[df["Papaya"] > 0]
    for i in range(0, 2):
        df = pd.concat([df, df_subset], ignore_index=True, sort=False)
    df_subset = df[(df["Grapes"]) > 0]
    for i in range(0, 2):
        df = pd.concat([df, df_subset], ignore_index=True, sort=False)

    df = sklearn.utils.shuffle(df, random_state=seed)

    X = df[train_params].values
    y = df.drop(columns=[*train_params, 'Crop_Year']).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    dump(scaler, SCALER_FILE)

    model = tf.keras.Sequential([
        tf.keras.layers.Dense(120, activation='relu', input_shape=(len(train_params),)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(200, activation='relu'),
        tf.keras.layers.Dense(y.shape[1], activation='softmax')
    ])

    def top5_accuracy(y_true, y_pred):
        return tf.keras.metrics.top_k_categorical_accuracy(y_true, y_pred, k=5)

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=[top5_accuracy]
    )

    history = model.fit(
        X_train, y_train,
        epochs=2000,
        batch_size=16,
        validation_split=0.1,
        verbose=1,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(patience=100, restore_best_weights=True)
        ]
    )

    results = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test Loss: {results[0]:.4f}")
    print(f"Test Top-5 Accuracy: {results[1]:.4f}")

    model.save(MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")

if __name__ == '__main__':
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    main()