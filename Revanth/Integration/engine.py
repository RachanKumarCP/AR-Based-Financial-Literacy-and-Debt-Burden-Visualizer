"""Core Integration Engine for DebtSight.

Connects:
  1. Loan Mathematics Engine (amortization schedules, EMI, total interest)
  2. ML Risk Predictor (calibrated default probability)
  3. Visual Burden Timeline (normalized scale values for AR visualizer)
  4. Financial Literacy Explanations & Formal Loan Comparison
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from ..Loan_Math.models import LoanInput, LoanScheduleResult, InterestMethod, RatePeriod
from ..Loan_Math.engine import LoanEngine
from ..Loan_Math.formulas import to_annual_percentage_rate
from .burden import compute_burden_timeline


@dataclass
class DebtSightResult:
    """Consolidated result returned to client interfaces."""

    monthly_balance: List[float]
    total_interest: float
    total_repayment: float
    monthly_payment: float
    debt_free_month: int
    risk_probability: float
    burden_timeline: List[float]
    formal_comparison_savings: float
    explanations: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monthly_balance": self.monthly_balance,
            "total_interest": self.total_interest,
            "total_repayment": self.total_repayment,
            "monthly_payment": self.monthly_payment,
            "debt_free_month": self.debt_free_month,
            "risk_probability": self.risk_probability,
            "burden_timeline": self.burden_timeline,
            "formal_comparison_savings": self.formal_comparison_savings,
            "explanations": self.explanations,
        }


class DebtSightIntegrationEngine:
    """Master engine orchestrating loan math, ML risk assessment, and AR burden indices."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path
        self._onnx_session = None
        self._load_predictor()

    def _load_predictor(self):
        """Attempts to load ONNX runtime session for risk inference."""
        try:
            import onnxruntime as ort

            target_path = self.model_path
            if target_path is None:
                default_onnx = Path(__file__).resolve().parent.parent / "ML/models/debtsight_risk_model.onnx"
                if default_onnx.exists():
                    target_path = default_onnx

            if target_path and Path(target_path).exists():
                self._onnx_session = ort.InferenceSession(str(target_path))
        except Exception:
            self._onnx_session = None

    def predict_risk(
        self,
        principal: float,
        apr: float,
        monthly_payment: float,
        tenure: int,
        lender_type: int,
        income_bracket: int,
        loan_intent: int = 4,
        home_ownership: int = 3,
        default_on_file: int = 0,
    ) -> float:
        """Estimates default risk probability using ONNX model or calibrated fallback heuristic."""
        # Estimate Debt-to-Income (DTI) ratio
        income_map = {0: 96000.0, 1: 216000.0, 2: 420000.0, 3: 780000.0}
        annual_income = income_map.get(income_bracket, 216000.0)
        pct_income = min(1.0, max(0.0, (monthly_payment * 12.0) / annual_income))

        if self._onnx_session is not None:
            try:
                import numpy as np

                features = np.array(
                    [[
                        float(principal),
                        float(apr),
                        float(pct_income),
                        3.0,
                        float(tenure),
                        float(income_bracket),
                        float(lender_type),
                        float(loan_intent),
                        float(home_ownership),
                        float(default_on_file),
                    ]],
                    dtype=np.float32,
                )
                outputs = self._onnx_session.run(None, {"float_input": features})
                probs = outputs[1]  # shape: [1, 2]
                return float(probs[0][1])
            except Exception:
                pass

        # Fallback heuristic if ONNX runtime is unavailable
        score = 0.20
        if apr > 36.0:
            score += 0.35
        elif apr > 24.0:
            score += 0.20
        elif apr > 14.0:
            score += 0.08

        if lender_type == 2:
            score += 0.25
        elif lender_type == 1:
            score += 0.10

        if income_bracket == 0:
            score += 0.15
        elif income_bracket == 1:
            score += 0.08

        if pct_income > 0.40:
            score += 0.20

        return max(0.0, min(1.0, score))

    def evaluate_loan(
        self,
        loan_input: LoanInput,
        lender_type: int = 2,
        income_bracket: int = 1,
    ) -> DebtSightResult:
        """Executes full evaluation pipeline: amortization, risk scoring, burden index, and explanations."""
        # 1. Calculate Primary Loan Schedule
        schedule: LoanScheduleResult = LoanEngine.calculate(loan_input)

        # 2. Compute APR
        apr = to_annual_percentage_rate(loan_input.interest_rate, loan_input.rate_period)

        # 3. Predict ML Default Risk
        risk_prob = self.predict_risk(
            principal=loan_input.principal,
            apr=apr,
            monthly_payment=schedule.monthly_payment,
            tenure=loan_input.tenure_months,
            lender_type=lender_type,
            income_bracket=income_bracket,
        )

        # 4. Compute Visual Burden Timeline
        burden_indices = compute_burden_timeline(
            monthly_balances=schedule.monthly_balance,
            principal=loan_input.principal,
            risk_probability=risk_prob,
        )

        # 5. Formal Loan Comparison (Reference: 12% APR Reducing Balance Bank/SHG Loan)
        formal_input = LoanInput(
            principal=loan_input.principal,
            interest_rate=12.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=loan_input.tenure_months,
            interest_method=InterestMethod.REDUCING_BALANCE,
        )
        formal_schedule = LoanEngine.calculate(formal_input)
        savings = max(0.0, schedule.total_interest - formal_schedule.total_interest)

        # 6. Generate Contextual Plain-English Explanations
        risk_level = "High" if risk_prob >= 0.50 else ("Moderate" if risk_prob >= 0.25 else "Low")
        explanations = {
            "risk_summary": f"{risk_level} default risk ({risk_prob*100:.1f}% estimated probability).",
            "formal_comparison": (
                f"A formal bank or SHG loan at 12% APR would save ₹{savings:,.2f} in total interest."
                if savings > 0
                else "Your loan terms are competitive with standard formal rates."
            ),
        }

        return DebtSightResult(
            monthly_balance=schedule.monthly_balance,
            total_interest=schedule.total_interest,
            total_repayment=schedule.total_repayment,
            monthly_payment=schedule.monthly_payment,
            debt_free_month=schedule.debt_free_month,
            risk_probability=round(risk_prob, 4),
            burden_timeline=burden_indices,
            formal_comparison_savings=round(savings, 2),
            explanations=explanations,
        )
