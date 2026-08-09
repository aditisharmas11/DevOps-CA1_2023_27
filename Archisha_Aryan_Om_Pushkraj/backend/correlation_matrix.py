import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import readasc

files = [i for i in os.listdir() if i.endswith(".asc")]
ascs = []
for file in files:
    ascs.append(readasc.Asc(file))

data = pd.read_csv("./datasets/preprocessed_data.csv")

for rowIdx in range(len(data)):
    row = data.iloc[rowIdx]
    for asc in ascs:
        data.loc[rowIdx, asc.get_asc_name()] = asc.get_value_at_lat_long(row["lat"], row["long"])

data = data.rename(columns = {"lat": "Latitude", "long": "Longitude"})
correlation_matrix = data.corr()

sns.set(font_scale=0.25)
sns.heatmap(correlation_matrix, annot=False, cmap='coolwarm', fmt=".2f", square=True, linewidths=0.5,  xticklabels=1, yticklabels=1)
plt.savefig('correlation_matrix.tiff', dpi=250)
sns.set(font_scale=1)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.show()
