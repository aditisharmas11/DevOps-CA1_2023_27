import os

import pandas as pd
import matplotlib.pyplot as plt

OUTPUT_DIR = './output_maps'
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv('./datasets/preprocessed_data.csv')

crops = ["Grapes", "Papaya", "Rice", "Wheat", "Sugarcane"]
agg_df = df.groupby(['lat', 'long'])[crops].sum().div(19).reset_index()

crop_params = {
    crop: {'color': '#6FEDB9', 'size_mult': 400}
    for crop in crops
}

outline_xs = []
outline_ys = []

with open("ne_10m_admin_0_countries_ind.csv", "r") as f:
    d = f.readlines()

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

for crop in crops:
    plt.figure()

    plt.scatter(
        x=agg_df['long'],
        y=agg_df['lat'],
        s=agg_df[crop] * crop_params[crop]['size_mult'],
        c=crop_params[crop]['color'],
        alpha=1,
        edgecolor='none',
        label=f'{crop}'
    )

    plt.scatter(outline_xs, outline_ys, c="black", s=1)

    plt.legend(markerscale=1.2, frameon=False,
               labelspacing=1.5, loc='lower left')

    # plt.scatter([74.58676543279755], [17.1726928], c="black", s = 1)
    plt.savefig(os.path.join(OUTPUT_DIR, f'{crop}.png'), dpi=220, bbox_inches='tight')
    plt.close()

print(f'Plots saved to {OUTPUT_DIR}')