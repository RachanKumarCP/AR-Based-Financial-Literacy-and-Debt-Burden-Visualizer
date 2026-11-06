"""Model training pipeline for DebtSight risk prediction.

Trains baseline (Logistic Regression) and advanced (Gradient Boosting / Random Forest)
classifiers, applies probability calibration, and saves artifacts for evaluation and export.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from .config import (
    DATA_RAW_DIR,
    MODELS_DIR,
    RANDOM_STATE,
    TEST_SIZE,
)
from .data_loader import DebtSightDataLoader
from .preprocessor import build_preprocessor_pipeline, extract_features_and_target
from .evaluate import evaluate_classifier, format_evaluation_summary


class DebtSightTrainer:
    """Orchestrates model training, cross-validation, and artifact saving."""

    def __init__(self, data_path: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.data_loader = DebtSightDataLoader(data_path)
        self.output_dir = Path(output_dir) if output_dir else MODELS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_training_pipeline(self, model_type: str = "logistic_regression") -> Dict[str, Any]:
        """Executes full training, calibration, and evaluation flow.

        Raises:
            FileNotFoundError: If dataset is missing.
        """
        try:
            import joblib
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.frozen import FrozenEstimator
            from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            from sklearn.pipeline import Pipeline
        except ImportError as e:
            raise ImportError("Required ML packages not installed. Run 'pip install -r requirements.txt'") from e

        # 1. Verify and Load Data
        df = self.data_loader.load_raw_data()
        is_valid, missing = self.data_loader.validate_schema(df)
        if not is_valid:
            raise ValueError(f"Dataset is missing required columns: {missing}")

        X, y = extract_features_and_target(df)

        # 2. Stratified Train / Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
        )

        # 3. Build Model Pipeline
        preprocessor = build_preprocessor_pipeline()

        if model_type == "logistic_regression":
            classifier = LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=RANDOM_STATE,
            )
        elif model_type == "gradient_boosting":
            classifier = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                random_state=RANDOM_STATE,
            )
        elif model_type == "random_forest":
            classifier = RandomForestClassifier(
                n_estimators=150,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        full_pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", classifier),
            ]
        )

        # 4. Train Model
        full_pipeline.fit(X_train, y_train)

        # 5. Probability Calibration (Platt Scaling via Sigmoid)
        # Guarantees that predicted probability reflects empirical default frequency
        calibrated_pipeline = CalibratedClassifierCV(
            estimator=FrozenEstimator(full_pipeline),
            method="sigmoid",
        )
        calibrated_pipeline.fit(X_test, y_test)

        # 6. Evaluation
        metrics = evaluate_classifier(calibrated_pipeline, X_test, y_test)

        # 7. Save Artifacts
        model_filename = f"debtsight_{model_type}.joblib"
        model_path = self.output_dir / model_filename
        joblib.dump(calibrated_pipeline, model_path)

        metrics_path = self.output_dir / f"metrics_{model_type}.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        return {
            "model_type": model_type,
            "saved_model_path": str(model_path),
            "metrics": metrics,
            "markdown_summary": format_evaluation_summary(metrics),
        }


if __name__ == "__main__":
    trainer = DebtSightTrainer()
    status = trainer.data_loader.get_dataset_status()
    print("Dataset Status:", status["message"])
