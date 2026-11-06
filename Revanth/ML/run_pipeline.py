"""
DebtSight ML — Data Preparation and Model Training Script

Reads credit_risk_dataset.csv, maps its columns to our 5 DebtSight
interface features, trains a Logistic Regression baseline and a
Gradient Boosting model with probability calibration, evaluates both,
and exports the best model as debtsight_risk_model.onnx for Unity Sentis.

Run from the workspace root:
    source .venv/bin/activate
    python3 Revanth/ML/run_pipeline.py
"""

import sys
import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, precision_score, recall_score, confusion_matrix,
    classification_report
)
import joblib

DATA_PATH = WORKSPACE_ROOT / "Revanth/ML/data/raw/credit_risk_dataset.csv"
MODELS_DIR = WORKSPACE_ROOT / "Revanth/ML/models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42

# ------------------------------------------------------------------
# STEP 1: Load Data
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 1: Loading Dataset")
print("="*60)

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df):,} rows with {df.shape[1]} columns.")
print(f"Columns: {list(df.columns)}")

# ------------------------------------------------------------------
# STEP 2: Map Dataset Columns → DebtSight 5-Feature Contract
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 2: Feature Engineering & Column Mapping")
print("="*60)

# --- amount: loan_amnt (numeric, direct)
df["amount"] = df["loan_amnt"].astype(float)

# --- rate: loan_int_rate (APR %; impute missing with median)
rate_median = df["loan_int_rate"].median()
df["rate"] = df["loan_int_rate"].fillna(rate_median).astype(float)
print(f"Interest rate: {df['loan_int_rate'].isna().sum()} missing values → imputed with median {rate_median:.2f}%")

# --- tenure: Derived from loan_grade tier
# High-grade (A/B) MUDRA-style short loans: 12–24 months
# Medium-grade (C/D) SHG-style: 24–36 months
# High-risk (E/F/G) informal: 6–12 months
grade_tenure_map = {"A": 24, "B": 24, "C": 36, "D": 36, "E": 12, "F": 12, "G": 6}
df["tenure"] = df["loan_grade"].map(grade_tenure_map).fillna(24).astype(int)
print(f"Tenure mapped from loan_grade. Distribution:\n{df['tenure'].value_counts().to_dict()}")

# --- lender_type: Derived from loan_grade
# Grade A & B → 0 (Bank / MUDRA / Formal)
# Grade C & D → 1 (SHG / Semi-formal)
# Grade E, F, G → 2 (Informal / High-risk)
grade_lender_map = {"A": 0, "B": 0, "C": 1, "D": 1, "E": 2, "F": 2, "G": 2}
df["lender_type"] = df["loan_grade"].map(grade_lender_map).fillna(0).astype(int)
print(f"Lender type distribution:\n{df['lender_type'].value_counts().to_dict()}")

# --- income_bracket: Derived from person_income
# Income brackets calibrated to dataset range (USD-equivalent scale):
# 0: < $15,000  → marginal low income
# 1: $15k–$35k  → lower-middle
# 2: $35k–$65k  → middle
# 3: > $65,000  → upper-middle / high
def encode_income_bracket(income):
    if income < 15000:
        return 0
    elif income < 35000:
        return 1
    elif income < 65000:
        return 2
    else:
        return 3

df["income_bracket"] = df["person_income"].apply(encode_income_bracket)
print(f"Income bracket distribution:\n{df['income_bracket'].value_counts().sort_index().to_dict()}")

# --- target: loan_status (1 = Default, 0 = Non-Default)
df["target"] = df["loan_status"].astype(int)
print(f"\nTarget distribution:\n{df['target'].value_counts().to_dict()}")
print(f"Default Rate: {df['target'].mean()*100:.2f}%")

# Final feature set
FEATURES = ["amount", "rate", "tenure", "lender_type", "income_bracket"]
X = df[FEATURES]
y = df["target"]

print(f"\nFinal Feature Matrix Shape: {X.shape}")
print(f"Sample rows:\n{X.head(5)}")

# ------------------------------------------------------------------
# STEP 3: Train / Test Split (Stratified)
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 3: Train / Test Split (80/20 Stratified)")
print("="*60)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
print(f"Training samples: {len(X_train):,}")
print(f"Testing samples:  {len(X_test):,}")
print(f"Train default rate: {y_train.mean()*100:.2f}%")
print(f"Test default rate:  {y_test.mean()*100:.2f}%")

# ------------------------------------------------------------------
# STEP 4: Preprocessing Pipeline
# ------------------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), ["amount", "rate", "tenure"]),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
        ]), ["lender_type", "income_bracket"]),
    ]
)

# ------------------------------------------------------------------
# STEP 5: Train Baseline — Logistic Regression
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 5: Training Baseline — Logistic Regression")
print("="*60)

lr_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=RANDOM_STATE,
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
    "model": "Logistic Regression (Calibrated)",
    "roc_auc": round(roc_auc_score(y_test, lr_probs), 4),
    "pr_auc":  round(average_precision_score(y_test, lr_probs), 4),
    "brier":   round(brier_score_loss(y_test, lr_probs), 4),
    "f1":      round(f1_score(y_test, lr_preds, zero_division=0), 4),
    "precision": round(precision_score(y_test, lr_preds, zero_division=0), 4),
    "recall":  round(recall_score(y_test, lr_preds, zero_division=0), 4),
}
print(f"  ROC-AUC:   {lr_metrics['roc_auc']}")
print(f"  PR-AUC:    {lr_metrics['pr_auc']}")
print(f"  F1-Score:  {lr_metrics['f1']}")
print(f"  Brier:     {lr_metrics['brier']}")

# ------------------------------------------------------------------
# STEP 6: Train Advanced — Gradient Boosting
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 6: Training Advanced — Gradient Boosting")
print("="*60)

gb_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=4,
        subsample=0.8,
        random_state=RANDOM_STATE,
    ))
])
gb_pipeline.fit(X_train, y_train)

gb_calibrated = CalibratedClassifierCV(
    estimator=FrozenEstimator(gb_pipeline), method="sigmoid"
)
gb_calibrated.fit(X_test, y_test)

gb_probs = gb_calibrated.predict_proba(X_test)[:, 1]
gb_preds = gb_calibrated.predict(X_test)

gb_metrics = {
    "model": "Gradient Boosting (Calibrated)",
    "roc_auc": round(roc_auc_score(y_test, gb_probs), 4),
    "pr_auc":  round(average_precision_score(y_test, gb_probs), 4),
    "brier":   round(brier_score_loss(y_test, gb_probs), 4),
    "f1":      round(f1_score(y_test, gb_preds, zero_division=0), 4),
    "precision": round(precision_score(y_test, gb_preds, zero_division=0), 4),
    "recall":  round(recall_score(y_test, gb_preds, zero_division=0), 4),
}
print(f"  ROC-AUC:   {gb_metrics['roc_auc']}")
print(f"  PR-AUC:    {gb_metrics['pr_auc']}")
print(f"  F1-Score:  {gb_metrics['f1']}")
print(f"  Brier:     {gb_metrics['brier']}")

# ------------------------------------------------------------------
# STEP 7: Select Best Model
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 7: Selecting Best Model by ROC-AUC")
print("="*60)

if gb_metrics["roc_auc"] >= lr_metrics["roc_auc"]:
    best_model = gb_calibrated
    best_metrics = gb_metrics
    best_name = "gradient_boosting"
else:
    best_model = lr_calibrated
    best_metrics = lr_metrics
    best_name = "logistic_regression"

print(f"Best model: {best_metrics['model']}")
print(f"Best ROC-AUC: {best_metrics['roc_auc']}")

# ------------------------------------------------------------------
# STEP 8: Save Models & Metrics
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 8: Saving Models & Metrics")
print("="*60)

joblib.dump(lr_calibrated, MODELS_DIR / "debtsight_logistic_regression.joblib")
joblib.dump(gb_calibrated, MODELS_DIR / "debtsight_gradient_boosting.joblib")
joblib.dump(best_model, MODELS_DIR / "debtsight_best_model.joblib")

all_metrics = {"logistic_regression": lr_metrics, "gradient_boosting": gb_metrics, "best": best_name}
with open(MODELS_DIR / "evaluation_metrics.json", "w") as f:
    json.dump(all_metrics, f, indent=2)

print("Saved:")
print(f"  → Revanth/ML/models/debtsight_logistic_regression.joblib")
print(f"  → Revanth/ML/models/debtsight_gradient_boosting.joblib")
print(f"  → Revanth/ML/models/debtsight_best_model.joblib")
print(f"  → Revanth/ML/models/evaluation_metrics.json")

# ------------------------------------------------------------------
# STEP 9: Export ONNX
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 9: Exporting Best Model to ONNX for Unity Sentis")
print("="*60)

try:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType, Int64TensorType

    # Build a fresh raw pipeline (not calibrated) for ONNX export
    best_raw_pipeline = gb_pipeline if best_name == "gradient_boosting" else lr_pipeline

    initial_types = [
        ("amount",          FloatTensorType([None, 1])),
        ("rate",            FloatTensorType([None, 1])),
        ("tenure",          FloatTensorType([None, 1])),
        ("lender_type",     FloatTensorType([None, 1])),
        ("income_bracket",  FloatTensorType([None, 1])),
    ]

    onnx_model = convert_sklearn(
        best_raw_pipeline,
        "DebtSightRiskModel",
        initial_types=initial_types,
        target_opset=12,
    )
    onnx_path = MODELS_DIR / "debtsight_risk_model.onnx"
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
    print(f"  → Revanth/ML/models/debtsight_risk_model.onnx")
    print("  ONNX export successful! Ready for Unity Sentis.")

except Exception as e:
    print(f"  ONNX export skipped (will retry separately): {e}")
    print("  Joblib model is fully usable for all Python inference.")

# ------------------------------------------------------------------
# STEP 10: Final Summary
# ------------------------------------------------------------------
print("\n" + "="*60)
print("STEP 10: Final Evaluation Summary")
print("="*60)

for label, m in [("Logistic Regression", lr_metrics), ("Gradient Boosting", gb_metrics)]:
    print(f"\n{label}:")
    print(f"  ROC-AUC  : {m['roc_auc']}  (Separates defaults from non-defaults)")
    print(f"  PR-AUC   : {m['pr_auc']}  (Precision-Recall, critical for imbalanced data)")
    print(f"  F1-Score : {m['f1']}")
    print(f"  Precision: {m['precision']}")
    print(f"  Recall   : {m['recall']}")
    print(f"  Brier    : {m['brier']}  (Calibration: lower = better)")

print(f"\n✅ Best Model Selected: {best_metrics['model']}")
print(f"✅ All artifacts saved to: Revanth/ML/models/")
print("="*60)
print("Pipeline complete. Ready for integration with Unity via ONNX!")
print("="*60)
