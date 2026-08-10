# DevOps-CA1_2023_27

## Group (PRN -> name)

23070122144: Sreehari Nair
23070122161: Parth Damle
23070122166: Pratik Lakra
23070122202: Aryan Sheladia

## Challenge worked on

Type: Kaggle Competition
Title: Housing Prices Competition for Kaggle Learn Users
Link: https://www.kaggle.com/competitions/home-data-for-ml-course

## Result

Final Leaderboard Rank: 292 / 4000+ participants

## Repository

Link: https://github.com/pratiklakra38/home-data-for-ml-course-challenge

## Brief description of the work

Objective: Predict `SalePrice` for houses in the Ames, Iowa housing dataset
using 80 numeric, categorical, and ordinal property features, evaluated on
RMSE between `log(predicted price)` and `log(actual price)`.

Approach: Built an iterative experiment pipeline - starting from a Linear
Regression baseline, then Ridge regression, then a tuned Gradient Boosting
model with 5 targeted engineered features (`TotalSF`, `HouseAge`,
`RemodAge`, `TotalBath`, `QualxGrLivArea`) added on top of the raw encoded
features. Every experiment used the same 5-fold `KFold(shuffle=True,
random_state=42)` cross-validation protocol for direct comparability.

Final model: Gradient Boosting + feature engineering, achieving a CV RMSE
of 0.1302 +/- 0.0192 (log space) - a 13.8% relative improvement over the
baseline and a 54% reduction in standard deviation.

## Local testing instructions

1. Clone the repository:
   ```
   git clone https://github.com/pratiklakra38/home-data-for-ml-course-challenge.git
   cd home-data-for-ml-course-challenge
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run any experiment script from the project root, e.g.:
   ```
   python scripts/08_final_model.py
   ```
4. This regenerates `submission.csv`, trained on the full training set and
   verified against `Data/sample_submission.csv` for row count, column
   names, `Id` order, and no missing values.
