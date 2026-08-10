import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

data = pd.read_csv('./datasets/crop_yield.csv')
data['Crop_Year'] = data['Crop_Year'] + 4
plt.figure(figsize=(10, 4))
plt.hist(data['Crop_Year'], edgecolor='black', bins=23)
plt.xticks(range(int(data['Crop_Year'].min()), int(data['Crop_Year'].max()) + 1))
plt.xlabel('Crop Year')
plt.ylabel('Count')
plt.title('Distribution of Crop Years')
plt.tight_layout()
plt.savefig('crop_year_histogram.png', dpi=180)
plt.show()
