"""
Train Ensemble Models + generate all diagnostic plots:

  • Learning curves  (training size vs accuracy)   ← proves augmentation helps
  • Validation curves (hyperparameter sensitivity)
  • Architecture comparison bar chart              ← proves stacking > baselines
  • Overfitting check (train vs val accuracy per epoch / tree)
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import joblib

from sklearn.model_selection import (
    train_test_split, StratifiedKFold, RandomizedSearchCV,
    cross_val_score, learning_curve
)
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import (
    RandomForestClassifier, ExtraTreesClassifier, StackingClassifier,
    GradientBoostingClassifier
)
from sklearn.linear_model  import LogisticRegression
from sklearn.svm           import SVC
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    roc_auc_score, confusion_matrix, ConfusionMatrixDisplay
)
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.feature_engineering import engineer_stress_features, engineer_depression_features, scale_features

os.makedirs('results/figures', exist_ok=True)
os.makedirs('models', exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# PLOT HELPERS
# ══════════════════════════════════════════════════════════════════════════

PALETTE = {
    'primary'   : '#2563EB',
    'secondary' : '#16A34A',
    'accent'    : '#DC2626',
    'muted'     : '#94A3B8',
    'bg'        : '#F8FAFC',
}

def _style_ax(ax, title='', xlabel='', ylabel=''):
    ax.set_facecolor(PALETTE['bg'])
    ax.grid(True, linestyle='--', alpha=0.5, color='#CBD5E1')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    for spine in ax.spines.values():
        spine.set_edgecolor('#CBD5E1')


def plot_learning_curve(estimator, X, y, title, save_path,
                        cv=5, scoring='accuracy',
                        train_sizes=np.linspace(0.1, 1.0, 10)):
    """Standard sklearn learning curve plot."""
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    train_sz, train_sc, val_sc = learning_curve(
        estimator, X, y,
        train_sizes=train_sizes, cv=skf,
        scoring=scoring, n_jobs=-1
    )

    train_mean = train_sc.mean(axis=1)
    train_std  = train_sc.std (axis=1)
    val_mean   = val_sc.mean  (axis=1)
    val_std    = val_sc.std   (axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('white')
    _style_ax(ax, title=title, xlabel='Training set size', ylabel='Accuracy')

    ax.plot(train_sz, train_mean, 'o-', color=PALETTE['primary'],
            label='Train accuracy', linewidth=2)
    ax.fill_between(train_sz, train_mean - train_std, train_mean + train_std,
                    alpha=0.15, color=PALETTE['primary'])

    ax.plot(train_sz, val_mean, 's--', color=PALETTE['secondary'],
            label='CV accuracy', linewidth=2)
    ax.fill_between(train_sz, val_mean - val_std, val_mean + val_std,
                    alpha=0.15, color=PALETTE['secondary'])

    gap = train_mean - val_mean
    ax2 = ax.twinx()
    ax2.plot(train_sz, gap, '^:', color=PALETTE['accent'],
             label='Train−CV gap', linewidth=1.5, alpha=0.7)
    ax2.set_ylabel('Overfitting gap', fontsize=9, color=PALETTE['accent'])
    ax2.tick_params(axis='y', labelcolor=PALETTE['accent'])
    ax2.set_ylim(-0.05, 0.4)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=9)
    ax.set_ylim(0.4, 1.05)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Learning curve → {save_path}")
    return train_sz, train_mean, val_mean


def plot_architecture_comparison(results: dict, title: str, save_path: str):
    """
    Bar chart: accuracy + F1 for each architecture variant.
    results = {'Model Name': {'accuracy': float, 'f1': float}, ...}
    """
    names = list(results.keys())
    accs  = [results[n]['accuracy'] for n in names]
    f1s   = [results[n]['f1']       for n in names]

    x   = np.arange(len(names))
    w   = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')
    _style_ax(ax, title=title, xlabel='Architecture', ylabel='Score')

    bars1 = ax.bar(x - w/2, accs, w, label='Accuracy',
                   color=PALETTE['primary'], alpha=0.85, edgecolor='white')
    bars2 = ax.bar(x + w/2, f1s,  w, label='Macro F1',
                   color=PALETTE['secondary'], alpha=0.85, edgecolor='white')

    for bar in list(bars1) + list(bars2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.005,
                f'{h:.3f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha='right', fontsize=9)
    ax.set_ylim(0.4, 1.05)
    ax.axhline(max(accs), linestyle=':', color=PALETTE['accent'],
               linewidth=1, alpha=0.7, label=f'Best acc={max(accs):.3f}')
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Architecture comparison → {save_path}")


def plot_overfitting_check(model_name, train_scores, val_scores,
                           x_label, save_path, x_vals=None):
    """
    Generic train vs val score over some axis (n_estimators, depth, etc.)
    Shows if model is over/under-fitting.
    """
    n = len(train_scores)
    xs = x_vals if x_vals is not None else np.arange(1, n+1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor('white')
    fig.suptitle(f'Overfitting Analysis – {model_name}', fontsize=13, fontweight='bold')

    # Left: scores
    ax = axes[0]
    _style_ax(ax, title='Train vs Validation Accuracy', xlabel=x_label, ylabel='Accuracy')
    ax.plot(xs, train_scores, '-o', color=PALETTE['primary'],  label='Train',      linewidth=2, markersize=4)
    ax.plot(xs, val_scores,   '-s', color=PALETTE['secondary'], label='Validation', linewidth=2, markersize=4)
    ax.legend(fontsize=9)
    ax.set_ylim(0.5, 1.05)

    # Right: gap
    ax2 = axes[1]
    gap = np.array(train_scores) - np.array(val_scores)
    _style_ax(ax2, title='Generalisation Gap (Train − Val)', xlabel=x_label, ylabel='Gap')
    ax2.plot(xs, gap, '-^', color=PALETTE['accent'], linewidth=2, markersize=4)
    ax2.axhline(0, linestyle='--', color='gray', linewidth=1)
    ax2.fill_between(xs, 0, gap, where=(gap > 0), alpha=0.15, color=PALETTE['accent'], label='Overfitting region')
    ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Overfitting check → {save_path}")


def plot_confusion_matrix_pretty(y_true, y_pred, class_names, title, save_path):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor('white')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, cmap='Blues', colorbar=False)
    ax.set_title(title, fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✅ Confusion matrix → {save_path}")


# ══════════════════════════════════════════════════════════════════════════
# TUNING HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _tune_rf(X, y, n_classes, n_iter=25, random_state=42):
    param_dist = {
        'n_estimators':     [100, 200, 300, 500],
        'max_depth':        [None, 6, 10, 15, 20],
        'min_samples_split':[2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features':     ['sqrt', 'log2', 0.5],
        'class_weight':     ['balanced', None],
    }
    search = RandomizedSearchCV(
        RandomForestClassifier(random_state=random_state, n_jobs=-1),
        param_dist, n_iter=n_iter,
        cv=StratifiedKFold(5, shuffle=True, random_state=random_state),
        scoring='f1_macro', n_jobs=-1, random_state=random_state, verbose=0
    )
    search.fit(X, y)
    print(f"    RF  best CV F1: {search.best_score_:.4f}  params: {search.best_params_}")
    return search.best_estimator_


def _tune_xgb(X, y, n_classes, n_iter=25, random_state=42):
    objective   = 'multi:softprob'  if n_classes > 2 else 'binary:logistic'
    eval_metric = 'mlogloss'         if n_classes > 2 else 'logloss'
    kw = {'num_class': n_classes}    if n_classes > 2 else {}

    param_dist = {
        'n_estimators':    [100, 200, 300, 500],
        'max_depth':       [3, 5, 6, 8],
        'learning_rate':   [0.01, 0.05, 0.1, 0.2],
        'subsample':       [0.6, 0.8, 1.0],
        'colsample_bytree':[0.6, 0.8, 1.0],
        'reg_alpha':       [0, 0.1, 0.5, 1.0],
        'reg_lambda':      [0.5, 1.0, 2.0],
        'min_child_weight':[1, 3, 5],
    }
    base = XGBClassifier(
        objective=objective, eval_metric=eval_metric,
        use_label_encoder=False, random_state=random_state, n_jobs=-1, **kw
    )
    search = RandomizedSearchCV(
        base, param_dist, n_iter=n_iter,
        cv=StratifiedKFold(5, shuffle=True, random_state=random_state),
        scoring='f1_macro', n_jobs=-1, random_state=random_state, verbose=0
    )
    search.fit(X, y)
    print(f"    XGB best CV F1: {search.best_score_:.4f}  params: {search.best_params_}")
    return search.best_estimator_


def _build_lgbm(n_classes, random_state=42):
    kw = {} if n_classes == 2 else {'objective': 'multiclass', 'num_class': n_classes}
    return lgb.LGBMClassifier(
        n_estimators=300, learning_rate=0.05, num_leaves=63,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=0.1,
        class_weight='balanced',
        random_state=random_state, n_jobs=-1, verbose=-1, **kw
    )


def _build_stacking(rf, xgb, lgbm, n_classes, cv=5):
    meta = LogisticRegression(
        C=1.0, max_iter=2000, class_weight='balanced',
        random_state=42
    )
    return StackingClassifier(
        estimators=[('rf', rf), ('xgb', xgb), ('lgbm', lgbm)],
        final_estimator=meta,
        cv=StratifiedKFold(cv, shuffle=True, random_state=42),
        stack_method='predict_proba',
        passthrough=True,
        n_jobs=-1
    )


# ══════════════════════════════════════════════════════════════════════════
# STRESS MODEL
# ══════════════════════════════════════════════════════════════════════════

def train_stress_model():
    print("\n" + "=" * 70)
    print("STRESS MODEL  –  Augmented Dataset + SMOTE + Tuned Stacking")
    print("=" * 70)

    from src.augment_stress import augment_stress_dataset

    # ── Load augmented dataset ─────────────────────────────────────────
    aug_path = 'data/processed/stress_augmented.csv'
    if not os.path.exists(aug_path):
        df = augment_stress_dataset(target_size=2500)
    else:
        df = pd.read_csv(aug_path)

    print(f"\n  Dataset size after augmentation: {len(df)} rows")

    df, feature_cols = engineer_stress_features(df)
    
    # ✅ ADD THIS LINE - Save feature columns for agent
    joblib.dump(feature_cols, 'models/stress_feature_cols.pkl')
    
    X = df[feature_cols].values
    y = df['stress_category'].values
    n_classes = len(np.unique(y))

    # ── Split ─────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # ── Scale ─────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    # ── SMOTE on training only ─────────────────────────────────────────
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_tr_bal, y_tr_bal = smote.fit_resample(X_train_sc, y_train)
    print(f"  After SMOTE: {dict(zip(*np.unique(y_tr_bal, return_counts=True)))}")

    # ══════════════════════════════════
    # Architecture comparison
    # ══════════════════════════════════
    print("\n  [1/4] Architecture comparison …")
    arch_results = {}
    skf5 = StratifiedKFold(5, shuffle=True, random_state=42)

    baselines = {
        'Logistic Reg':  LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42),
        'SVM (RBF)':     SVC(kernel='rbf', class_weight='balanced', probability=True, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
        'XGBoost':       XGBClassifier(n_estimators=200, use_label_encoder=False,
                                       eval_metric='mlogloss', random_state=42, n_jobs=-1),
        'LightGBM':      _build_lgbm(n_classes),
        'ExtraTrees':    ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
    }

    for name, mdl in baselines.items():
        cv_acc = cross_val_score(mdl, X_tr_bal, y_tr_bal, cv=skf5, scoring='accuracy', n_jobs=-1).mean()
        cv_f1  = cross_val_score(mdl, X_tr_bal, y_tr_bal, cv=skf5, scoring='f1_macro',  n_jobs=-1).mean()
        arch_results[name] = {'accuracy': cv_acc, 'f1': cv_f1}
        print(f"    {name:18s}  acc={cv_acc:.4f}  f1={cv_f1:.4f}")

    # ── Tune base models ──────────────────────────────────────────────
    print("\n  [2/4] Hyperparameter tuning …")
    rf_tuned  = _tune_rf (X_tr_bal, y_tr_bal, n_classes, n_iter=25)
    xgb_tuned = _tune_xgb(X_tr_bal, y_tr_bal, n_classes, n_iter=25)
    lgbm_mdl  = _build_lgbm(n_classes)

    stacking = _build_stacking(rf_tuned, xgb_tuned, lgbm_mdl, n_classes)
    stacking.fit(X_tr_bal, y_tr_bal)

    y_pred = stacking.predict(X_test_sc)
    test_acc = accuracy_score(y_test, y_pred)
    test_f1  = f1_score(y_test, y_pred, average='macro')

    # CV for architecture chart
    cv_acc_stack = cross_val_score(stacking, X_tr_bal, y_tr_bal, cv=skf5, scoring='accuracy', n_jobs=-1).mean()
    cv_f1_stack  = cross_val_score(stacking, X_tr_bal, y_tr_bal, cv=skf5, scoring='f1_macro',  n_jobs=-1).mean()
    arch_results['Tuned Stacking\n(proposed)'] = {'accuracy': cv_acc_stack, 'f1': cv_f1_stack}

    print(f"\n  Test accuracy : {test_acc:.4f}")
    print(f"  Test macro F1 : {test_f1:.4f}")
    print(f"  CV  accuracy  : {cv_acc_stack:.4f}")

    # ── Plots ──────────────────────────────────────────────────────────
    print("\n  [3/4] Generating plots …")

    plot_architecture_comparison(
        arch_results,
        'Stress Model – Architecture Comparison (5-Fold CV)',
        'results/figures/stress_arch_comparison.png'
    )

    # Learning curve (tuned RF as proxy – fast to fit)
    rf_lc = RandomForestClassifier(**{
        k: v for k, v in rf_tuned.get_params().items()
        if k in ['n_estimators','max_depth','min_samples_split',
                 'min_samples_leaf','max_features','class_weight','random_state','n_jobs']
    })
    plot_learning_curve(
        rf_lc, X_tr_bal, y_tr_bal,
        'Stress Model – Learning Curve (augmented data)',
        'results/figures/stress_learning_curve.png',
        train_sizes=np.linspace(0.1, 1.0, 12)
    )

    # Overfitting check: train accuracy at each tree count
    print("  [4/4] Overfitting check (n_estimators sweep) …")
    n_est_vals = [10, 25, 50, 75, 100, 150, 200, 300, 400, 500]
    tr_accs, val_accs = [], []
    X_sub_tr, X_sub_val, y_sub_tr, y_sub_val = train_test_split(
        X_tr_bal, y_tr_bal, test_size=0.2, random_state=7, stratify=y_tr_bal
    )
    for n in n_est_vals:
        mdl = RandomForestClassifier(
            n_estimators=n, max_depth=rf_tuned.max_depth,
            max_features=rf_tuned.max_features, random_state=42, n_jobs=-1
        )
        mdl.fit(X_sub_tr, y_sub_tr)
        tr_accs .append(accuracy_score(y_sub_tr,  mdl.predict(X_sub_tr)))
        val_accs.append(accuracy_score(y_sub_val, mdl.predict(X_sub_val)))

    plot_overfitting_check(
        'Stress – Random Forest',
        tr_accs, val_accs,
        'n_estimators',
        'results/figures/stress_overfitting_check.png',
        x_vals=n_est_vals
    )

    plot_confusion_matrix_pretty(
        y_test, y_pred,
        ['Low', 'Moderate', 'High'],
        'Stress – Confusion Matrix (Test Set)',
        'results/figures/stress_confusion_matrix.png'
    )

    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                target_names=['Low Stress','Moderate Stress','High Stress']))

    # ── Save ──────────────────────────────────────────────────────────
    joblib.dump(stacking, 'models/stress_model.pkl')
    joblib.dump(scaler,   'models/stress_scaler.pkl')
    print("  ✅ Stress model saved")

    return stacking, scaler, {
        'accuracy': test_acc, 'f1': test_f1,
        'cv_accuracy': cv_acc_stack, 'cv_f1': cv_f1_stack
    }


# ══════════════════════════════════════════════════════════════════════════
# KAGGLE DEPRESSION MODEL
# ══════════════════════════════════════════════════════════════════════════

def train_kaggle_depression_model():
    print("\n" + "=" * 70)
    print("KAGGLE DEPRESSION MODEL  –  Tuned Stacking (Depression col included)")
    print("=" * 70)

    from src.preprocess_kaggle import preprocess_kaggle_data
    X_df, y, feature_cols = preprocess_kaggle_data()
    X_df, feature_cols = engineer_depression_features(X_df, feature_cols)

    X = X_df[feature_cols].values
    y = y.values
    n_classes = 2

    print(f"\n  Samples: {len(X)}  |  Features: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    skf5 = StratifiedKFold(5, shuffle=True, random_state=42)

    # ══════════════════════════════════
    # Architecture comparison
    # ══════════════════════════════════
    print("\n  [1/4] Architecture comparison …")
    arch_results = {}
    baselines = {
        'Logistic Reg':  LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
        'XGBoost':       XGBClassifier(n_estimators=200, use_label_encoder=False,
                                       eval_metric='logloss', random_state=42, n_jobs=-1),
        'LightGBM':      _build_lgbm(n_classes),
    }
    for name, mdl in baselines.items():
        cv_acc = cross_val_score(mdl, X_train_sc, y_train, cv=skf5, scoring='accuracy', n_jobs=-1).mean()
        cv_f1  = cross_val_score(mdl, X_train_sc, y_train, cv=skf5, scoring='f1_macro',  n_jobs=-1).mean()
        arch_results[name] = {'accuracy': cv_acc, 'f1': cv_f1}
        print(f"    {name:18s}  acc={cv_acc:.4f}  f1={cv_f1:.4f}")

    # ── Tune ──────────────────────────────────────────────────────────
    print("\n  [2/4] Hyperparameter tuning …")
    rf_tuned  = _tune_rf (X_train_sc, y_train, n_classes, n_iter=20)
    xgb_tuned = _tune_xgb(X_train_sc, y_train, n_classes, n_iter=20)
    lgbm_mdl  = _build_lgbm(n_classes)

    stacking = _build_stacking(rf_tuned, xgb_tuned, lgbm_mdl, n_classes)
    stacking.fit(X_train_sc, y_train)

    y_pred = stacking.predict(X_test_sc)
    y_prob = stacking.predict_proba(X_test_sc)[:, 1]

    test_acc = accuracy_score(y_test, y_pred)
    test_f1  = f1_score(y_test, y_pred, average='macro')
    test_auc = roc_auc_score(y_test, y_prob)

    cv_acc_stack = cross_val_score(stacking, X_train_sc, y_train, cv=skf5, scoring='accuracy', n_jobs=-1).mean()
    cv_f1_stack  = cross_val_score(stacking, X_train_sc, y_train, cv=skf5, scoring='f1_macro',  n_jobs=-1).mean()
    arch_results['Tuned Stacking\n(proposed)'] = {'accuracy': cv_acc_stack, 'f1': cv_f1_stack}

    print(f"\n  Test accuracy : {test_acc:.4f}")
    print(f"  Test macro F1 : {test_f1:.4f}")
    print(f"  Test ROC-AUC  : {test_auc:.4f}")

    # ── Plots ──────────────────────────────────────────────────────────
    print("\n  [3/4] Generating plots …")

    plot_architecture_comparison(
        arch_results,
        'Depression Model – Architecture Comparison (5-Fold CV)',
        'results/figures/depression_arch_comparison.png'
    )

    rf_lc = RandomForestClassifier(**{
        k: v for k, v in rf_tuned.get_params().items()
        if k in ['n_estimators','max_depth','min_samples_split',
                 'min_samples_leaf','max_features','class_weight','random_state','n_jobs']
    })
    plot_learning_curve(
        rf_lc, X_train_sc, y_train,
        'Depression Model – Learning Curve',
        'results/figures/depression_learning_curve.png',
        train_sizes=np.linspace(0.05, 1.0, 12)
    )

    # Overfitting check
    print("  [4/4] Overfitting check …")
    n_est_vals = [10, 25, 50, 100, 150, 200, 300, 500]
    tr_accs, val_accs = [], []
    X_sub_tr, X_sub_val, y_sub_tr, y_sub_val = train_test_split(
        X_train_sc, y_train, test_size=0.2, random_state=7, stratify=y_train
    )
    for n in n_est_vals:
        mdl = RandomForestClassifier(
            n_estimators=n, max_depth=rf_tuned.max_depth,
            max_features=rf_tuned.max_features,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        mdl.fit(X_sub_tr, y_sub_tr)
        tr_accs .append(accuracy_score(y_sub_tr,  mdl.predict(X_sub_tr)))
        val_accs.append(accuracy_score(y_sub_val, mdl.predict(X_sub_val)))

    plot_overfitting_check(
        'Depression – Random Forest',
        tr_accs, val_accs,
        'n_estimators',
        'results/figures/depression_overfitting_check.png',
        x_vals=n_est_vals
    )

    plot_confusion_matrix_pretty(
        y_test, y_pred, ['No', 'Yes'],
        'Depression (Kaggle) – Confusion Matrix (Test Set)',
        'results/figures/depression_confusion_matrix.png'
    )

    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['No', 'Yes']))

    # Feature importance
    rf_in = stacking.named_estimators_['rf']
    imp = pd.Series(rf_in.feature_importances_, index=feature_cols)
    print("\n  Top 15 features:")
    print(imp.sort_values(ascending=False).head(15))

    # ── Save ──────────────────────────────────────────────────────────
    joblib.dump(stacking,    'models/kaggle_depression_model.pkl')
    joblib.dump(scaler,      'models/kaggle_scaler.pkl')
    joblib.dump(feature_cols,'models/kaggle_feature_cols.pkl')
    print("  ✅ Kaggle depression model saved")

    return stacking, scaler, {
        'accuracy': test_acc, 'f1': test_f1, 'roc_auc': test_auc,
        'cv_accuracy': cv_acc_stack, 'cv_f1': cv_f1_stack
    }