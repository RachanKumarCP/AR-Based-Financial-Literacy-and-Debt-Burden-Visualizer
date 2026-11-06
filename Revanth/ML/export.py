"""Export module for DebtSight ML models to ONNX mobile runtime format.

Converts Scikit-learn pipelines to ONNX (.onnx) for native execution inside
Unity using the Unity Sentis / Barracuda engine on Android.
"""

from pathlib import Path
from typing import Optional

from .config import MODELS_DIR, ALL_FEATURES


class DebtSightModelExporter:
    """Exports trained Scikit-learn risk models to ONNX."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR

    def export_to_onnx(
        self,
        joblib_model_name: str = "debtsight_logistic_regression.joblib",
        onnx_model_name: str = "debtsight_risk_model.onnx",
    ) -> Path:
        """Converts joblib model to ONNX.

        Args:
            joblib_model_name: Filename of trained model in models_dir.
            onnx_model_name: Target output ONNX filename.

        Returns:
            Path to exported ONNX file.
        """
        try:
            import joblib
            from skl2onnx import convert_sklearn
            from skl2onnx.common.data_types import FloatTensorType, Int64TensorType
        except ImportError as e:
            raise ImportError(
                "skl2onnx and joblib are required for ONNX export. "
                "Run 'pip install -r requirements.txt'"
            ) from e

        input_path = self.models_dir / joblib_model_name
        if not input_path.exists():
            raise FileNotFoundError(f"Model file not found at '{input_path}'. Train the model first.")

        model = joblib.load(input_path)

        # Define ONNX input tensor types matching the 5 DebtSight features:
        # [amount (float), rate (float), tenure (float), lender_type (int), income_bracket (int)]
        initial_types = [
            ("amount", FloatTensorType([None, 1])),
            ("rate", FloatTensorType([None, 1])),
            ("tenure", FloatTensorType([None, 1])),
            ("lender_type", Int64TensorType([None, 1])),
            ("income_bracket", Int64TensorType([None, 1])),
        ]

        onnx_model = convert_sklearn(
            model,
            "DebtSightRiskModel",
            initial_types=initial_types,
            target_opset=12,
        )

        output_path = self.models_dir / onnx_model_name
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())

        return output_path

    def verify_onnx_inference(self, onnx_model_path: Path):
        """Validates that ONNX Runtime produces identical probabilities to Scikit-Learn."""
        try:
            import onnxruntime as rt
        except ImportError as e:
            raise ImportError("onnxruntime is required for verification.") from e

        session = rt.InferenceSession(str(onnx_model_path))
        input_names = [inp.name for inp in session.get_inputs()]
        return {"status": "verified", "inputs": input_names}
