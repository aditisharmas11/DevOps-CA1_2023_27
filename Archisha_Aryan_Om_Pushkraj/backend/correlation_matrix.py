import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import readasc

asc_root = './datasets'
asc_files = [os.path.join(asc_root, f) for f in os.listdir(asc_root) if f.endswith('.asc')]
ascs = [readasc.Asc(path) for path in asc_files]

data = pd.read_csv("./datasets/preprocessed_data.csv")

for asc in ascs:
    data[asc.get_asc_name()] = data.apply(
        lambda row: asc.get_value_at_lat_long(row['lat'], row['long']),
        axis=1
    )

data = data.rename(columns={"lat": "Latitude", "long": "Longitude"})
correlation_matrix = data.corr()
OUTPUT_FILE = 'correlation_matrix.tiff'

sns.set(font_scale=0.25)
plt.figure(figsize=(12, 10))
sns.heatmap(
    correlation_matrix,
    annot=False,
    cmap='coolwarm',
    fmt='.2f',
    square=True,
    linewidths=0.5,
    xticklabels=1,
    yticklabels=1
)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=250, bbox_inches='tight')
plt.close()
print(f'Saved correlation matrix to {OUTPUT_FILE}')
