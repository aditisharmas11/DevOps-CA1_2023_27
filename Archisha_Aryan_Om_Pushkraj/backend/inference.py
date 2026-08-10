import os
import time

import tensorflow as tf
import numpy as np
import pandas as pd
from joblib import load
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import readasc

from readasc import coordinate_dist

model = tf.keras.models.load_model('./crop_model.h5', custom_objects={
    'top5_accuracy': lambda y_true, y_pred: tf.keras.metrics.top_k_categorical_accuracy(y_true, y_pred, k=5)
})
scaler = load('./scaler.joblib')
preprocessed_df = pd.read_csv('./datasets/preprocessed_data.csv')
CROP_LIST = preprocessed_df.columns[3:].tolist()

asc_paths = [
    './datasets/organic_carbon.asc',
    './datasets/inorganic_carbon.asc',
    './datasets/clayey_soil.asc',
    './datasets/clayey-skeletal_soil.asc',
    './datasets/loamy_soil.asc',
    './datasets/sandy_soil.asc'
]
ascs = {
    os.path.splitext(os.path.basename(path))[0]: readasc.Asc(path)
    for path in asc_paths if os.path.exists(path)
}

def predict_top_crops(latitude, longitude, year):
    latitude = np.atleast_1d(latitude)
    longitude = np.atleast_1d(longitude)
    year = np.atleast_1d(year)

    if latitude.shape != longitude.shape:
        raise ValueError('Latitude and longitude must have the same shape')
    if year.size not in (1, latitude.size):
        raise ValueError('Year must be a scalar or match the number of coordinates')

    if year.size == 1:
        year = np.full(latitude.shape, year.item(), dtype=float)

    feature_rows = []
    asc_layers = list(ascs.values())
    for lat, long, yr in zip(latitude, longitude, year):
        soil_values = [asc.get_value_at_lat_long(lat, long) for asc in asc_layers]
        feature_rows.append([lat, long, yr] + soil_values)

    input_features = np.asarray(feature_rows, dtype=float)
    scaled_input = scaler.transform(input_features)
    predictions = model.predict(scaled_input, verbose=0)

    all_results = []
    for pred in predictions:
        top_idxs = np.argsort(pred)[::-1][:5]
        top_vals = pred[top_idxs]
        total = top_vals.sum()

        if total == 0:
            all_results.append([])
        else:
            ratios = top_vals / total
            crops_and_ratios = [
                (CROP_LIST[i], float(r))
                for i, r in zip(top_idxs, ratios)
            ]
            all_results.append(crops_and_ratios)

    return all_results[0] if not is_batch else all_results


if __name__ == "__main__":
    outline_xs = []
    outline_ys = []

    with open("ne_10m_admin_0_countries_ind.csv", "r") as f:
        d = f.readlines()

    # these are (roughly) where india's coordinates are in the country data csv file.
    dataIndices = [
        (0.05, 0.11)
    ]

    for dat in dataIndices:
        startPerc = dat[0]
        endPerc = dat[1]
        for i in d[1 + int(len(d) * startPerc): int(len(d) * endPerc) - 1]:
            l = [float(k.strip()) for k in i.split(",")]
            if l[0] < 65:  # longitude
                continue
            outline_xs.append(l[0])
            outline_ys.append(l[1])

    # crops = list(CROP_LIST)
    crops = ["Grapes", "Papaya", "Rice", "Wheat", "Sugarcane"]

    res = 256

    x_min, x_max = 65, 100
    y_min, y_max = 5, 40
    xs = np.linspace(x_min, x_max, num=res)
    ys = np.linspace(y_min, y_max, num=res)
    xx, yy = np.meshgrid(xs, ys)

    latitudes = yy.ravel()
    longitudes = xx.ravel()
    years = [2025] * latitudes.size

    print(time.perf_counter())
    batch_preds = predict_top_crops(latitudes, longitudes, years)
    print(time.perf_counter())

    crop_values = {crop: np.zeros((res, res)) for crop in crops}

    for idx, single_pred in enumerate(batch_preds):
        iy = idx // res
        ix = idx % res
        d = dict(single_pred)
        for crop in crops:
            crop_values[crop][iy, ix] = d.get(crop, 0.0)

    for crop in crops:
        plt.figure()
        X, Y = np.meshgrid(xs, ys)
        plt.scatter(
            X.ravel(),
            Y.ravel(),
            c=crop_values[crop].ravel(),
            cmap='viridis',
            marker='s',
            s=40
        )

        plt.title(crop)
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.colorbar(label="Predicted yield")

        image = mpimg.imread('map_filler.png')
        plt.imshow(image, extent=(x_min, x_max, y_min, y_max), zorder=3)

        last_i = 0
        for i in range(0, len(outline_xs)):
            if coordinate_dist(outline_ys[last_i], outline_xs[last_i], outline_ys[i], outline_xs[i]) > 4:
                # plt.scatter(outline_xs[last_i:i], outline_ys[last_i:i], c="pink", s=1)
                last_i = i

        # plt.scatter([74.58676543279755], [17.1726928], c="cyan")
        plt.savefig(f'./output_maps/{crop}.png', dpi=500)

    plt.show()