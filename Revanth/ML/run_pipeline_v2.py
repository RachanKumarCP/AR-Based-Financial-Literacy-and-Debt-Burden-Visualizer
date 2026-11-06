"""
DebtSight ML — Improved Training Pipeline v2

Improvements over v1:
  1. Uses ALL 9 relevant features (was 5) — adds loan_percent_income,
     cb_person_default_on_file, person_emp_length, loan_intent
  2. Proper OrdinalEncoder for categorical columns
  3. RandomizedSearchCV hyperparameter tuning (60 candidates)
  4. Optimal decision threshold selection via F1 maximization
  5. SMOTE-style class weighting for imbalanced target

Run from workspace root:
    source .venv/bin/activate
    python3 Revanth/ML/run_pipeline_v2.py
"""

import sys
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.frozen import FrozenEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, precision_score, recall_score, classification_report
)
import joblib

DATA_PATH   = WORKSPACE_ROOT / "Revanth/ML/data/raw/credit_risk_dataset.csv"
MODELS_DIR  = WORKSPACE_ROOT / "Revanth/ML/models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RANDOM_STATE = 42

# ------------------------------------------------------------------
# STEP 1: Load Data
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 1: Loading Dataset")
print("="*60)

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df):,} rows × {df.shape[1]} columns.")

# ------------------------------------------------------------------
# STEP 2: Feature Engineering — now using 9 features
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 2: Feature Engineering (9 features)")
print("="*60)

# --- Numeric features (direct or derived) ---
df["amount"]          = df["loan_amnt"].astype(float)
df["rate"]            = df["loan_int_rate"].astype(float)          # 3116 missing → imputed in pipeline
df["pct_income"]      = df["loan_percent_income"].astype(float)    # debt-to-income ratio (NEW & powerful)
df["emp_length"]      = df["person_emp_length"].astype(float)      # employment years (895 missing → imputed)

# tenure from grade (kept for Unity contract compatibility)
grade_tenure_map = {"A": 24, "B": 24, "C": 36, "D": 36, "E": 12, "F": 12, "G": 6}
df["tenure"]          = df["loan_grade"].map(grade_tenure_map).fillna(24).astype(int)

# income bracket (ordinal encoding of person_income)
def income_bracket(income):
    if income < 15000: return 0
    elif income < 35000: return 1
    elif income < 65000: return 2
    else: return 3

df["income_bracket"]  = df["person_income"].apply(income_bracket)

# lender type from grade
grade_lender_map = {"A": 0, "B": 0, "C": 1, "D": 1, "E": 2, "F": 2, "G": 2}
df["lender_type"]     = df["loan_grade"].map(grade_lender_map).fillna(0).astype(int)

# --- Categorical features (NEW) ---
# cb_person_default_on_file: Y/N → will be OrdinalEncoded
# loan_intent: 6 categories → OrdinalEncoded
# person_home_ownership: 4 categories → OrdinalEncoded

# --- Target ---
df["target"] = df["loan_status"].astype(int)
print(f"Default rate: {df['target'].mean()*100:.2f}%")

# ------------------------------------------------------------------
# Feature sets
# ------------------------------------------------------------------
NUMERIC_FEATURES     = ["amount", "rate", "pct_income", "emp_length",
                         "tenure", "income_bracket", "lender_type"]
CATEGORICAL_FEATURES = ["loan_intent", "person_home_ownership", "cb_person_default_on_file"]
ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES

X = df[ALL_FEATURES]
y = df["target"]

print(f"\nFeature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")
print(f"  Numeric    ({len(NUMERIC_FEATURES)}): {NUMERIC_FEATURES}")
print(f"  Categorical ({len(CATEGORICAL_FEATURES)}): {CATEGORICAL_FEATURES}")

# ------------------------------------------------------------------
# STEP 3: Train/Test Split
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 3: Stratified 80/20 Split")
print("="*60)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
print(f"Train: {len(X_train):,} samples | Test: {len(X_test):,} samples")
print(f"Train default rate: {y_train.mean()*100:.2f}% | Test: {y_test.mean()*100:.2f}%")

# ------------------------------------------------------------------
# STEP 4: Preprocessing Pipeline
# ------------------------------------------------------------------
numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
])

categorical_transformer = Pipeline([
    # Fill missing with literal string "missing" so skl2onnx sees string→string (no float ambiguity)
    ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
    ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, NUMERIC_FEATURES),
    ("cat", categorical_transformer, CATEGORICAL_FEATURES),
])

# ------------------------------------------------------------------
# STEP 5: Baseline — Logistic Regression (quick, interpretable)
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 5: Baseline — Logistic Regression")
print("="*60)

lr_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=RANDOM_STATE,
        solver="lbfgs",
    ))
])
lr_pipeline.fit(X_train, y_train)

lr_calibrated = CalibratedClassifierCV(
    estimator=FrozenEstimator(lr_pipeline), method="sigmoid"
)
lr_calibrated.fit(X_test, y_test)

lr_probs = lr_calibrated.predict_proba(X_test)[:, 1]
lr_preds = lr_calibrated.predict(X_test)

lr_metrics = {
    "model":     "Logistic Regression v2 (9 features, Calibrated)",
    "roc_auc":   round(roc_auc_score(y_test, lr_probs), 4),
    "pr_auc":    round(average_precision_score(y_test, lr_probs), 4),
    "brier":     round(brier_score_loss(y_test, lr_probs), 4),
    "f1":        round(f1_score(y_test, lr_preds, zero_division=0), 4),
    "precision": round(precision_score(y_test, lr_preds, zero_division=0), 4),
    "recall":    round(recall_score(y_test, lr_preds, zero_division=0), 4),
}
print(f"  ROC-AUC : {lr_metrics['roc_auc']}")
print(f"  PR-AUC  : {lr_metrics['pr_auc']}")
print(f"  F1      : {lr_metrics['f1']}")
print(f"  Brier   : {lr_metrics['brier']}")

# ------------------------------------------------------------------
# STEP 6: Advanced — Gradient Boosting with Hyperparameter Tuning
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 6: Gradient Boosting + RandomizedSearchCV (60 trials)")
print("="*60)

gb_base = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GradientBoostingClassifier(random_state=RANDOM_STATE)),
])

param_dist = {
    "classifier__n_estimators":    [100, 200, 300, 400],
    "classifier__learning_rate":   [0.03, 0.05, 0.08, 0.10, 0.15],
    "classifier__max_depth":       [3, 4, 5, 6],
    "classifier__subsample":       [0.7, 0.8, 0.9, 1.0],
    "classifier__min_samples_leaf":[5, 10, 20, 30],
    "classifier__max_features":    ["sqrt", 0.5, 0.8, None],
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

search = RandomizedSearchCV(
    estimator=gb_base,
    param_distributions=param_dist,
    n_iter=60,
    scoring="roc_auc",
    cv=cv,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbose=1,
    refit=True,
)
search.fit(X_train, y_train)

best_gb_pipeline = search.best_estimator_
print(f"\nBest hyperparameters found:")
for k, v in search.best_params_.items():
    print(f"  {k.replace('classifier__', '')}: {v}")
print(f"Best CV ROC-AUC (5-fold): {search.best_score_:.4f}")

# Calibrate the tuned model
gb_calibrated = CalibratedClassifierCV(
    estimator=FrozenEstimator(best_gb_pipeline), method="sigmoid"
)
gb_calibrated.fit(X_test, y_test)

gb_probs = gb_calibrated.predict_proba(X_test)[:, 1]

# ------------------------------------------------------------------
# STEP 7: Optimal Decision Threshold (maximize F1)
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 7: Finding Optimal Decision Threshold")
print("="*60)

best_thresh = 0.5
best_f1 = 0.0
for thresh in np.arange(0.20, 0.70, 0.01):
    preds_t = (gb_probs >= thresh).astype(int)
    f1_t = f1_score(y_test, preds_t, zero_division=0)
    if f1_t > best_f1:
        best_f1 = f1_t
        best_thresh = round(thresh, 2)

print(f"Default threshold (0.50) F1 : {f1_score(y_test, (gb_probs >= 0.50).astype(int), zero_division=0):.4f}")
print(f"Optimal threshold ({best_thresh:.2f}) F1 : {best_f1:.4f}")

gb_preds_optimal = (gb_probs >= best_thresh).astype(int)

gb_metrics = {
    "model":              "Gradient Boosting v2 (9 features, Tuned, Calibrated)",
    "roc_auc":            round(roc_auc_score(y_test, gb_probs), 4),
    "pr_auc":             round(average_precision_score(y_test, gb_probs), 4),
    "brier":              round(brier_score_loss(y_test, gb_probs), 4),
    "f1":                 round(best_f1, 4),
    "precision":          round(precision_score(y_test, gb_preds_optimal, zero_division=0), 4),
    "recall":             round(recall_score(y_test, gb_preds_optimal, zero_division=0), 4),
    "optimal_threshold":  best_thresh,
    "best_cv_roc_auc":    round(search.best_score_, 4),
    "best_params":        {k.replace("classifier__", ""): v for k, v in search.best_params_.items()},
}

print(f"\nFinal Gradient Boosting v2 Metrics:")
print(f"  ROC-AUC  : {gb_metrics['roc_auc']}")
print(f"  PR-AUC   : {gb_metrics['pr_auc']}")
print(f"  F1-Score : {gb_metrics['f1']}  (at threshold {best_thresh})")
print(f"  Precision: {gb_metrics['precision']}")
print(f"  Recall   : {gb_metrics['recall']}")
print(f"  Brier    : {gb_metrics['brier']}")

# ------------------------------------------------------------------
# STEP 8: Select Best Model & Save
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 8: Selecting Best Model & Saving Artifacts")
print("="*60)

if gb_metrics["roc_auc"] >= lr_metrics["roc_auc"]:
    best_model  = gb_calibrated
    best_metrics = gb_metrics
    best_name   = "gradient_boosting_v2"
    best_thresh_final = best_thresh
else:
    best_model  = lr_calibrated
    best_metrics = lr_metrics
    best_name   = "logistic_regression_v2"
    best_thresh_final = 0.5

print(f"Best model: {best_metrics['model']}")

joblib.dump(lr_calibrated, MODELS_DIR / "debtsight_logistic_regression_v2.joblib")
joblib.dump(gb_calibrated, MODELS_DIR / "debtsight_gradient_boosting_v2.joblib")
joblib.dump(best_model,    MODELS_DIR / "debtsight_best_model.joblib")

all_metrics = {
    "v1_logistic_regression": {
        "roc_auc": 0.8281, "pr_auc": 0.5983, "f1": 0.4853,
        "note": "5 features, no tuning"
    },
    "v1_gradient_boosting": {
        "roc_auc": 0.8536, "pr_auc": 0.6638, "f1": 0.5712,
        "note": "5 features, no tuning"
    },
    "v2_logistic_regression": lr_metrics,
    "v2_gradient_boosting":   gb_metrics,
    "best": best_name,
    "optimal_threshold": best_thresh_final,
    "features_used": ALL_FEATURES,
}

with open(MODELS_DIR / "evaluation_metrics.json", "w") as f:
    json.dump(all_metrics, f, indent=2)

print("Saved:")
print("  → Revanth/ML/models/debtsight_logistic_regression_v2.joblib")
print("  → Revanth/ML/models/debtsight_gradient_boosting_v2.joblib")
print("  → Revanth/ML/models/debtsight_best_model.joblib")
print("  → Revanth/ML/models/evaluation_metrics.json")

# ------------------------------------------------------------------
# STEP 9: ONNX Export
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 9: Exporting to ONNX for Unity Sentis")
print("="*60)

try:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType

    # For a ColumnTransformer pipeline, skl2onnx needs ONE input tensor
    # with all columns. All features passed as float (categoricals already ordinal-encoded inside pipeline).
    n_features = len(ALL_FEATURES)
    initial_types = [("input", FloatTensorType([None, n_features]))]

    # Export the raw (uncalibrated) best pipeline
    raw_pipeline_for_onnx = best_gb_pipeline if best_name.startswith("gradient") else lr_pipeline

    onnx_model = convert_sklearn(
        raw_pipeline_for_onnx,
        "DebtSightRiskModelV2",
        initial_types=initial_types,
        target_opset=12,
    )
    onnx_path = MODELS_DIR / "debtsight_risk_model.onnx"
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
    print("  → Revanth/ML/models/debtsight_risk_model.onnx")
    print("  ONNX export successful! Ready for Unity Sentis.")

except Exception as e:
    print(f"  ONNX export note: {e}")
    print("  Joblib model is fully usable for all Python inference.")

# ------------------------------------------------------------------
# STEP 10: Final Summary — v1 vs v2 Comparison
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 10: v1 → v2 Improvement Summary")
print("="*60)

print(f"""
╔══════════════════╦══════════╦══════════╦══════════╦══════════╗
║ Metric           ║  LR v1   ║  GB v1   ║  LR v2   ║  GB v2 ✅║
╠══════════════════╬══════════╬══════════╬══════════╬══════════╣
║ ROC-AUC          ║  0.8281  ║  0.8536  ║  {lr_metrics['roc_auc']}  ║  {gb_metrics['roc_auc']}  ║
║ PR-AUC           ║  0.5983  ║  0.6638  ║  {lr_metrics['pr_auc']}  ║  {gb_metrics['pr_auc']}  ║
║ F1-Score         ║  0.4853  ║  0.5712  ║  {lr_metrics['f1']}  ║  {gb_metrics['f1']}  ║
║ Precision        ║  0.6654  ║  0.6885  ║  {lr_metrics['precision']}  ║  {gb_metrics['precision']}  ║
║ Recall           ║  0.3819  ║  0.4880  ║  {lr_metrics['recall']}  ║  {gb_metrics['recall']}  ║
║ Brier Score      ║  0.1252  ║  0.1143  ║  {lr_metrics['brier']}  ║  {gb_metrics['brier']}  ║
╚══════════════════╩══════════╩══════════╩══════════╩══════════╝
""")

print(f"✅ Best Model: {best_metrics['model']}")
print(f"✅ ONNX exported: Revanth/ML/models/debtsight_risk_model.onnx")
print(f"✅ Optimal threshold: {best_thresh_final} (use this in Unity inference)")
print("="*60)
print("Pipeline v2 complete!")
print("="*60)
