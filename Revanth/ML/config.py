"""Configuration settings for the DebtSight Machine Learning Pipeline.

Centralizes feature definitions, data validation boundaries, categorical encodings,
and model hyperparameters.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# Shared Contract Feature Names
NUMERICAL_FEATURES = ["amount", "rate", "tenure"]
CATEGORICAL_FEATURES = ["lender_type", "income_bracket"]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "target"

# Feature Constraints & Domain Bounds
FEATURE_CONSTRAINTS = {
    "amount": {"min": 500.0, "max": 10000000.0, "type": float},
    "rate": {"min": 0.0, "max": 300.0, "type": float},  # APR %
    "tenure": {"min": 1, "max": 360, "type": int},       # months
    "lender_type": {"allowed": [0, 1, 2], "type": int},   # 0: Bank, 1: SHG, 2: Informal
    "income_bracket": {"allowed": [0, 1, 2, 3], "type": int},  # 0: <10k, 1: 10-25k, 2: 25-50k, 3: >50k
}

# Categorical Value Mappings
LENDER_TYPE_MAP = {
    0: "Bank / Formal / MUDRA",
    1: "Self-Help Group (SHG)",
    2: "Informal Moneylender",
}

INCOME_BRACKET_MAP = {
    0: "< ₹10,000 / month",
    1: "₹10,000 – ₹25,000 / month",
    2: "₹25,000 – ₹50,000 / month",
    3: "> ₹50,000 / month",
}

# Modeling Settings
RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5

# Candidate Models
MODEL_CANDIDATES = [
    "logistic_regression",
    "gradient_boosting",
    "random_forest",
]
