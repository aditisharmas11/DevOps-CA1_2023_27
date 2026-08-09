"""
Data Augmentation for the Stress Dataset (520 → ~2500 rows)

Techniques:
  1. Gaussian noise injection        – perturbs each sample slightly
  2. SMOTE-style synthetic minority  – already handled in training, but
     here we augment the raw dataset so learning curves are meaningful
  3. Mixup                           – convex combinations of pairs
  4. Boundary-aware perturbation     – keeps samples within valid [1,5] range

All augmentation is purely based on input features + the original
stress_level; the stress_category is re-derived after augmentation
so there is no label inconsistency.
"""

import pandas as pd
import numpy as np


FEATURE_COLS = [
    'sleep_quality', 'headaches_weekly', 'academic_performance',
    'study_load', 'extracurricular_weekly'
]
TARGET_COL = 'stress_level'


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    """Clip all feature columns to [1, 5] and round to nearest integer."""
    for col in FEATURE_COLS:
        df[col] = df[col].clip(1, 5).round().astype(int)
    df[TARGET_COL] = df[TARGET_COL].clip(1, 5).round().astype(int)
    return df


def _categorize(level: int) -> int:
    if level <= 2:   return 0
    elif level <= 3: return 1
    else:            return 2


def gaussian_noise(df: pd.DataFrame, n_copies: int = 2,
                   noise_std: float = 0.35, random_state: int = 42) -> pd.DataFrame:
    """Add Gaussian noise copies of every row."""
    rng = np.random.default_rng(random_state)
    all_cols = FEATURE_COLS + [TARGET_COL]
    copies = []
    for _ in range(n_copies):
        noisy = df[all_cols].copy().astype(float)
        noise = rng.normal(0, noise_std, size=noisy.shape)
        noisy += noise
        noisy = _clip(noisy)
        copies.append(noisy)
    return pd.concat(copies, ignore_index=True)


def mixup(df: pd.DataFrame, n_samples: int = 600,
          alpha: float = 0.4, random_state: int = 42) -> pd.DataFrame:
    """
    Mixup: draw pairs (i, j) and form λ·x_i + (1-λ)·x_j.
    Label is assigned by rounding the mixed target.
    """
    rng = np.random.default_rng(random_state)
    all_cols = FEATURE_COLS + [TARGET_COL]
    arr = df[all_cols].values.astype(float)
    n = len(arr)
    idx_a = rng.integers(0, n, size=n_samples)
    idx_b = rng.integers(0, n, size=n_samples)
    lam   = rng.beta(alpha, alpha, size=(n_samples, 1))
    mixed = lam * arr[idx_a] + (1 - lam) * arr[idx_b]
    mixed_df = pd.DataFrame(mixed, columns=all_cols)
    return _clip(mixed_df)


def class_balanced_noise(df: pd.DataFrame, target_per_class: int = 600,
                         noise_std: float = 0.4, random_state: int = 42) -> pd.DataFrame:
    """
    Oversample each stress_category class to `target_per_class` by adding
    Gaussian noise to randomly sampled rows from that class.
    """
    rng = np.random.default_rng(random_state)
    all_cols = FEATURE_COLS + [TARGET_COL]
    pieces = []
    for cat in [0, 1, 2]:
        subset = df[df['stress_category'] == cat][all_cols].copy()
        n_have = len(subset)
        n_need = max(0, target_per_class - n_have)
        if n_need == 0:
            pieces.append(subset)
            continue
        idx = rng.integers(0, n_have, size=n_need)
        sampled = subset.iloc[idx].copy().astype(float)
        sampled += rng.normal(0, noise_std, size=sampled.shape)
        sampled = _clip(sampled)
        pieces.append(pd.concat([subset, sampled], ignore_index=True))
    return pd.concat(pieces, ignore_index=True)


def augment_stress_dataset(raw_path: str = 'data/raw/Student_Stress_Factors.csv',
                           out_path:  str = 'data/processed/stress_augmented.csv',
                           target_size: int = 2500) -> pd.DataFrame:
    """
    Main entry point.  Returns augmented DataFrame and saves to out_path.
    target_size   ≈ desired total rows (original + synthetic)
    """
    # ── Load & clean ──────────────────────────────────────────────────
    df = pd.read_csv(raw_path)
    df.columns = (
        ['sleep_quality', 'headaches_weekly', 'academic_performance',
         'study_load', 'extracurricular_weekly', 'stress_level']
    )
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()
    for col in FEATURE_COLS + [TARGET_COL]:
        df[col] = df[col].clip(1, 5).round().astype(int)
    df['stress_category'] = df[TARGET_COL].apply(_categorize)

    n_orig = len(df)
    n_need = target_size - n_orig          # how many synthetic rows to add

    # Strategy: ~50 % class-balanced noise, ~25 % gaussian, ~25 % mixup
    n_balanced = int(n_need * 0.50)
    n_gauss    = int(n_need * 0.25)
    n_mix      = n_need - n_balanced - n_gauss

    per_class  = n_orig // 3 + n_balanced // 3   # balanced target per class

    syn_balanced = class_balanced_noise(df, target_per_class=per_class, random_state=0)
    syn_gauss    = gaussian_noise(df, n_copies=1, noise_std=0.35, random_state=1)
    syn_gauss    = syn_gauss.sample(min(n_gauss, len(syn_gauss)), random_state=2)
    syn_mix      = mixup(df, n_samples=n_mix, random_state=3)

    for syn in [syn_balanced, syn_gauss, syn_mix]:
        syn['stress_category'] = syn[TARGET_COL].apply(_categorize)

    augmented = pd.concat([df, syn_balanced, syn_gauss, syn_mix], ignore_index=True)
    augmented  = augmented.sample(frac=1, random_state=42).reset_index(drop=True)

    # ── Report ────────────────────────────────────────────────────────
    print(f"Augmentation complete:")
    print(f"  Original rows : {n_orig}")
    print(f"  Synthetic rows: {len(augmented) - n_orig}")
    print(f"  Total rows    : {len(augmented)}")
    print(f"  Class balance :\n{augmented['stress_category'].value_counts().sort_index()}")

    augmented.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")
    return augmented