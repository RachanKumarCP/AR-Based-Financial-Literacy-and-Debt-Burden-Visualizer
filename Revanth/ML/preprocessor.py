"""Feature preprocessing and transformation pipeline for DebtSight.

Builds standard Scikit-learn pipelines with column transformers for numerical
scaling and categorical encoding.
"""

from typing import Tuple
from .config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)


def build_preprocessor_pipeline():
    """Constructs a Scikit-Learn ColumnTransformer for DebtSight features.

    Numerical pipeline:
        - SimpleImputer(strategy='median')
        - StandardScaler()

    Categorical pipeline:
        - SimpleImputer(strategy='most_frequent')
        - OneHotEncoder(handle_unknown='ignore')
    """
    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
    except ImportError as e:
        raise ImportError(
            "scikit-learn is required for preprocessing. "
            "Install dependencies via 'pip install -r requirements.txt'."
        ) from e

    num_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    cat_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, NUMERICAL_FEATURES),
            ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    return preprocessor


def extract_features_and_target(df) -> Tuple[any, any]:
    """Splits DataFrame into feature matrix X and target vector y."""
    X = df[ALL_FEATURES].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y
