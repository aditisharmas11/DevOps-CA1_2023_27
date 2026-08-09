import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

data = pd.read_csv('./datasets/crop_yield.csv')
data["Crop_Year"] = data["Crop_Year"] + 4
plt.hist(data["Crop_Year"], edgecolor = "black", bins = 23)
plt.xticks(range(min(data["Crop_Year"]), max(data["Crop_Year"]) + 1))
plt.show()
