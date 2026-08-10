import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

DATA_FILE = './datasets/crop_yield.csv'
OUTPUT_FILE = 'crop_year_histogram.png'


def plot_crop_year_histogram():
    data = pd.read_csv(DATA_FILE)
    data['Crop_Year'] = data['Crop_Year'] + 4

    plt.figure(figsize=(10, 4))
    plt.hist(data['Crop_Year'], edgecolor='black', bins=23)
    plt.xticks(range(int(data['Crop_Year'].min()), int(data['Crop_Year'].max()) + 1))
    plt.xlabel('Crop Year')
    plt.ylabel('Count')
    plt.title('Distribution of Crop Years')
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=180)
    plt.close()
    print(f'Saved crop year histogram to {OUTPUT_FILE}')


if __name__ == '__main__':
    plot_crop_year_histogram()
