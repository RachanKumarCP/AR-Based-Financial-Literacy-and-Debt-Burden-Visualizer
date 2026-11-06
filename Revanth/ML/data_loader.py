"""Data loader and integrity checker for DebtSight ML datasets.

Adheres strictly to the project rule:
Never fabricates fake training data or synthetic labels.
Requires an authentic, verified dataset file.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import os

from .config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    DATA_RAW_DIR,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)


class DebtSightDataLoader:
    """Loads and validates loan default datasets for DebtSight."""

    def __init__(self, raw_data_path: Optional[Path] = None):
        self.raw_data_path = Path(raw_data_path) if raw_data_path else (DATA_RAW_DIR / "loans.csv")

    def verify_dataset_exists(self) -> bool:
        """Checks if the dataset file is present on disk."""
        return self.raw_data_path.exists() and self.raw_data_path.is_file()

    def get_dataset_status(self) -> Dict[str, any]:
        """Inspects dataset availability and reports metadata."""
        if not self.verify_dataset_exists():
            return {
                "available": False,
                "path": str(self.raw_data_path),
                "message": (
                    f"Dataset file not found at '{self.raw_data_path}'. "
                    f"Please place an authentic CSV dataset into '{DATA_RAW_DIR}/' "
                    f"before running model training."
                ),
            }

        file_size_kb = self.raw_data_path.stat().st_size / 1024.0
        return {
            "available": True,
            "path": str(self.raw_data_path),
            "size_kb": round(file_size_kb, 2),
            "message": "Dataset file located. Ready for schema validation.",
        }

    def load_raw_data(self):
        """Loads dataset using pandas.

        Raises:
            FileNotFoundError: If the dataset file does not exist.
            ImportError: If pandas is not installed.
        """
        if not self.verify_dataset_exists():
            raise FileNotFoundError(
                f"No dataset found at '{self.raw_data_path}'.\n"
                f"Per project guidelines, synthetic or fabricated datasets are not generated.\n"
                f"Please acquire an authentic dataset (e.g. Kaggle LTFS, Microfinance, or NAFIS) "
                f"and place it at '{self.raw_data_path}'."
            )

        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required to load tabular datasets. "
                "Install dependencies via 'pip install -r requirements.txt'."
            ) from e

        df = pd.read_csv(self.raw_data_path)
        return df

    def validate_schema(self, df) -> Tuple[bool, list]:
        """Verifies that the DataFrame contains required features and target.

        Returns:
            Tuple of (is_valid: bool, missing_columns: list)
        """
        required = set(ALL_FEATURES + [TARGET_COLUMN])
        existing = set(df.columns)
        missing = list(required - existing)
        return len(missing) == 0, missing
