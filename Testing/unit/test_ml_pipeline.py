"""Unit tests for DebtSight Machine Learning Pipeline Architecture.

Verifies:
- Feature configuration matches shared contract specifications
- DataLoader integrity rules (rejects missing files, never fabricates fake data)
- Preprocessing pipeline structure
"""

import os
import sys
import unittest
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from Revanth.ML.config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_CONSTRAINTS,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)
from Revanth.ML.data_loader import DebtSightDataLoader


class TestMLPipelineArchitecture(unittest.TestCase):
    """Verifies that the ML module enforces project integrity and contracts."""

    def test_feature_definitions_match_contract(self):
        """Features must match [amount, rate, tenure, lender_type, income_bracket]."""
        expected_features = ["amount", "rate", "tenure", "lender_type", "income_bracket"]
        self.assertEqual(ALL_FEATURES, expected_features)
        self.assertEqual(NUMERICAL_FEATURES, ["amount", "rate", "tenure"])
        self.assertEqual(CATEGORICAL_FEATURES, ["lender_type", "income_bracket"])
        self.assertEqual(TARGET_COLUMN, "target")

    def test_feature_constraints(self):
        """Lender type must allow {0, 1, 2} and income bracket {0, 1, 2, 3}."""
        self.assertEqual(FEATURE_CONSTRAINTS["lender_type"]["allowed"], [0, 1, 2])
        self.assertEqual(FEATURE_CONSTRAINTS["income_bracket"]["allowed"], [0, 1, 2, 3])
        self.assertGreater(FEATURE_CONSTRAINTS["amount"]["min"], 0)

    def test_dataloader_rejects_missing_file_without_fabrication(self):
        """DataLoader must raise FileNotFoundError if file is absent, NEVER fabricate fake data."""
        dummy_path = Path("/nonexistent/path/fake_loans.csv")
        loader = DebtSightDataLoader(raw_data_path=dummy_path)

        self.assertFalse(loader.verify_dataset_exists())
        status = loader.get_dataset_status()
        self.assertFalse(status["available"])
        self.assertIn("Dataset file not found", status["message"])

        # Attempting to load missing file must raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            loader.load_raw_data()


if __name__ == "__main__":
    unittest.main()
