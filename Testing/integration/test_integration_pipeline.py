"""Integration tests for DebtSight master pipeline.

Tests end-to-end evaluation:
  Loan Input -> Loan Math -> ML Risk Scoring -> Burden Timeline -> Formal Savings
"""

import unittest
from pathlib import Path

from Revanth.Loan_Math.models import LoanInput, InterestMethod, RatePeriod
from Revanth.Integration.burden import compute_normalized_debt, compute_burden_timeline
from Revanth.Integration.engine import DebtSightIntegrationEngine, DebtSightResult


class TestIntegrationPipeline(unittest.TestCase):
    """Verifies end-to-end integration between loan math, ML risk, and burden timeline."""

    def setUp(self):
        self.engine = DebtSightIntegrationEngine()

    def test_burden_calculation_bounds_and_decay(self):
        """Verifies that burden index stays within [0.0, 1.0] and decreases as balance is paid off."""
        principal = 50000.0
        balances = [50000.0, 37500.0, 25000.0, 12500.0, 0.0]
        risk = 0.50

        burden_timeline = compute_burden_timeline(balances, principal, risk)

        self.assertEqual(len(burden_timeline), len(balances))
        for val in burden_timeline:
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

        # Monotonically non-increasing as debt decreases
        for i in range(len(burden_timeline) - 1):
            self.assertGreaterEqual(burden_timeline[i], burden_timeline[i + 1])

        # Terminal month burden is strictly driven by risk component alone: 0.4 * 0.5 = 0.2
        self.assertAlmostEqual(burden_timeline[-1], 0.20, delta=0.01)

    def test_informal_moneylender_loan_evaluation(self):
        """Simulates high-interest rural moneylender loan: 3% per month (36% APR), Flat Rate."""
        loan_input = LoanInput(
            principal=50000.0,
            interest_rate=3.0,
            rate_period=RatePeriod.MONTHLY,
            tenure_months=12,
            interest_method=InterestMethod.FLAT_RATE,
        )

        result: DebtSightResult = self.engine.evaluate_loan(
            loan_input=loan_input,
            lender_type=2,      # Informal moneylender
            income_bracket=0,   # Low income (< 10k/month)
        )

        # Verify Loan Math totals
        self.assertEqual(result.total_interest, 18000.0)
        self.assertEqual(result.total_repayment, 68000.0)
        self.assertAlmostEqual(result.monthly_payment, 5666.67, places=2)
        self.assertEqual(result.debt_free_month, 12)

        # High risk expected due to high APR + informal lender + low income
        self.assertGreater(result.risk_probability, 0.40)

        # Substantial savings expected compared to formal 12% loan
        self.assertGreater(result.formal_comparison_savings, 10000.0)

        # Explanations generated
        self.assertIn("risk_summary", result.explanations)
        self.assertIn("formal_comparison", result.explanations)

    def test_formal_shg_loan_evaluation(self):
        """Simulates formal SHG loan: 12% APR, Reducing Balance, moderate income."""
        loan_input = LoanInput(
            principal=8000.0,
            interest_rate=12.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=12,
            interest_method=InterestMethod.REDUCING_BALANCE,
        )

        result: DebtSightResult = self.engine.evaluate_loan(
            loan_input=loan_input,
            lender_type=0,      # Formal Bank / Scheme
            income_bracket=2,   # 25k-50k income
        )

        # Lower risk expected for formal loan with healthy income
        self.assertLess(result.risk_probability, 0.40)

        # Formal savings should be ~0 since loan is already at formal benchmark
        self.assertAlmostEqual(result.formal_comparison_savings, 0.0, delta=1.0)

    def test_result_dictionary_serialization(self):
        """Verifies dictionary representation matches interface contract."""
        loan_input = LoanInput(
            principal=20000.0,
            interest_rate=18.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=6,
            interest_method=InterestMethod.REDUCING_BALANCE,
        )
        result = self.engine.evaluate_loan(loan_input, lender_type=0, income_bracket=1)
        data = result.to_dict()

        expected_keys = {
            "monthly_balance",
            "total_interest",
            "total_repayment",
            "monthly_payment",
            "debt_free_month",
            "risk_probability",
            "burden_timeline",
            "formal_comparison_savings",
            "explanations",
        }
        self.assertTrue(expected_keys.issubset(data.keys()))


if __name__ == "__main__":
    unittest.main()
