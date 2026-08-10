import pandas as pd
from geopy.geocoders import Nominatim
import json
import os
import numpy as np
import readasc

CACHE_FILE = './datasets/geocode_cache.json'
DATA_FILE = './datasets/crop_data.csv'
OUTPUT_FILE = './datasets/preprocessed_data.csv'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def geocode_location(state, district, cache, geolocator):
    key = f"{state}|{district}"
    if key in cache:
        return cache[key]

    try:
        location = geolocator.geocode(f"{district}, {state}, India")
        if not location:
            location = geolocator.geocode(f"{state}, India")
    except Exception:
        location = None

    cache[key] = (location.latitude, location.longitude) if location else (None, None)
    return cache[key]

def main():
    df = pd.read_csv(DATA_FILE)

    cache = load_cache()
    geolocator = Nominatim(user_agent="crop_prediction")

    locations = [
        geocode_location(state, district, cache, geolocator)
        for state, district in zip(df['State_Name'], df['District_Name'])
    ]
    df[['lat', 'long']] = pd.DataFrame(locations, index=df.index)
    save_cache(cache)

    df = df.dropna(subset=['lat', 'long'])
    
    df = df[(df['Area'] > 0) & (df['Production'] > 0)]
    df['Yield'] = df['Production'] / df['Area']
    
    def remove_outliers(group):
        q1 = group['Yield'].quantile(0.05)
        q3 = group['Yield'].quantile(0.95)
        iqr = q3 - q1
        return group[(group['Yield'] >= q1 - 1.5*iqr) & (group['Yield'] <= q3 + 1.5*iqr)]

    df_subset_idx = df["Crop"] == "Grapes"
    df_new = df[~df_subset_idx].groupby('Crop').apply(remove_outliers).reset_index(drop=True)
    df = pd.concat([df_new, df[df_subset_idx]], ignore_index=True, sort=False)

    # since andaman islands are separate from mainland india, it causes mispredictions
    df = df[df['State_Name'] != 'Andaman and Nicobar Islands']
    # df = df[df['District_Name'] != 'NICOBARS']

    agg_df = (
        df.groupby(['lat', 'long', 'Crop_Year', 'Crop'])
        .agg({'Production': 'sum', 'Area': 'sum'})
        .reset_index()
    )
    agg_df['Yield'] = agg_df['Production'] / agg_df['Area']
    agg_df['crop_mean_yield'] = agg_df.groupby('Crop')['Yield'].transform('mean')
    agg_df['Rel_Yield'] = agg_df['Yield'] / agg_df['crop_mean_yield']
    agg_df['Yield'] = agg_df['Rel_Yield']
    add_df = agg_df.drop(columns=['crop_mean_yield', 'Rel_Yield'])
    
    grouped = agg_df.groupby(['lat', 'long', 'Crop_Year'])
    top_crops = []
    
    for name, group in grouped:
        group = group.sort_values('Yield', ascending=False).head(5)
        total_yield = group['Yield'].sum()
        group['Ratio'] = group['Yield'] / total_yield
        top_crops.append(group[['lat', 'long', 'Crop_Year', 'Crop', 'Ratio']])
    
    top_crops_df = pd.concat(top_crops)
    
    pivot_df = top_crops_df.pivot_table(
        index=['lat', 'long', 'Crop_Year'],
        columns='Crop',
        values='Ratio',
        fill_value=0
    ).reset_index()

    ascs = [
        'organic_carbon', 'inorganic_carbon', 'clayey_soil',
        'clayey-skeletal_soil', 'loamy_soil', 'sandy_soil'
    ]

    for asc_name in ascs:
        asc = readasc.Asc(f"./datasets/{asc_name}.asc")

        pivot_df[asc_name] = pivot_df.apply(
            lambda row: asc.get_value_at_lat_long(row['lat'], row['long']),
            axis=1
        )
    
    pivot_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Preprocessing complete. Data saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
