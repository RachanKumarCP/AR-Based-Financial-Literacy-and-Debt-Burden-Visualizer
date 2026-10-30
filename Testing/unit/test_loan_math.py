"""Unit tests for DebtSight Loan Mathematics Engine.

Contains manually verified financial test cases for:
- Reducing Balance EMI calculation
- Flat Rate moneylender interest calculation
- Simple Interest Bullet harvest loan calculation
- Prepayment acceleration scenarios
- Zero-interest and boundary validation
"""

import math
import unittest
import sys
import os

# Add workspace root to sys.path to ensure modules are discoverable
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from Revanth.Loan_Math.models import (
    InterestMethod,
    LoanInput,
    LoanScheduleResult,
    RatePeriod,
)
from Revanth.Loan_Math.formulas import (
    calculate_approx_reducing_apr_from_flat,
    calculate_flat_monthly_payment,
    calculate_flat_total_interest,
    calculate_reducing_emi,
    to_annual_percentage_rate,
    to_monthly_fractional_rate,
)
from Revanth.Loan_Math.engine import LoanEngine


class TestLoanFormulas(unittest.TestCase):
    """Direct tests for individual mathematical functions."""

    def test_rate_conversions(self):
        """Verify monthly to annual and percentage to fractional conversions."""
        # Annual 24% -> APR 24%, monthly r = 0.02
        apr = to_annual_percentage_rate(24.0, RatePeriod.ANNUAL)
        r = to_monthly_fractional_rate(24.0, RatePeriod.ANNUAL)
        self.assertAlmostEqual(apr, 24.0)
        self.assertAlmostEqual(r, 0.02)

        # Monthly 3% -> APR 36%, monthly r = 0.03
        apr_m = to_annual_percentage_rate(3.0, RatePeriod.MONTHLY)
        r_m = to_monthly_fractional_rate(3.0, RatePeriod.MONTHLY)
        self.assertAlmostEqual(apr_m, 36.0)
        self.assertAlmostEqual(r_m, 0.03)

    def test_reducing_emi_manual_example(self):
        """Verify reducing EMI matches standard financial calculator for ₹100,000 at 12% APR for 12 months.

        Manual formula verification:
        P = 100,000
        r = 0.01 (1% per month)
        n = 12
        EMI = 100000 * [0.01 * (1.01)^12] / [(1.01)^12 - 1]
        (1.01)^12 = 1.12682503
        EMI = 100000 * 0.01126825 / 0.12682503 = 8884.88
        """
        emi = calculate_reducing_emi(100000.0, 0.01, 12)
        self.assertAlmostEqual(emi, 8884.88, places=2)

    def test_flat_rate_manual_example(self):
        """Verify flat rate interest for ₹50,000 at 36% APR for 12 months.

        Total Interest = 50,000 * 0.36 * 1 = ₹18,000.
        Monthly payment = (50,000 + 18,000) / 12 = ₹5,666.67.
        """
        interest = calculate_flat_total_interest(50000.0, 36.0, 12)
        monthly_pay = calculate_flat_monthly_payment(50000.0, 36.0, 12)
        self.assertAlmostEqual(interest, 18000.0, places=2)
        self.assertAlmostEqual(monthly_pay, 5666.67, places=2)

    def test_effective_apr_from_flat(self):
        """Verify approximate effective reducing APR for a 24% flat 12-month loan.

        Effective APR ~= 24 * (2 * 12 / 13) = 24 * 24 / 13 = 44.31%
        """
        eff_apr = calculate_approx_reducing_apr_from_flat(24.0, 12)
        expected = 24.0 * (24.0 / 13.0)
        self.assertAlmostEqual(eff_apr, expected, places=2)


class TestLoanEngine(unittest.TestCase):
    """End-to-end amortization schedule tests using LoanEngine."""

    def test_reducing_balance_schedule(self):
        """Test complete 12-month schedule for ₹100,000 at 12% APR."""
        loan = LoanInput(
            principal=100000.0,
            interest_rate=12.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=12,
            interest_method=InterestMethod.REDUCING_BALANCE,
            monthly_prepayment=0.0,
        )
        result = LoanEngine.calculate(loan)

        # 1. Output structure check
        self.assertEqual(len(result.monthly_balance), 12)
        self.assertEqual(len(result.amortization_table), 12)

        # 2. Financial totals
        self.assertAlmostEqual(result.monthly_payment, 8884.88, places=2)
        self.assertAlmostEqual(result.total_repayment, 106618.55, delta=1.0)
        self.assertAlmostEqual(result.total_interest, 6618.55, delta=1.0)

        # 3. Payoff month and zero closing balance
        self.assertEqual(result.debt_free_month, 12)
        self.assertAlmostEqual(result.monthly_balance[-1], 0.0, places=2)

        # 4. Monotonic decline of balance
        for i in range(len(result.monthly_balance) - 1):
            self.assertGreater(result.monthly_balance[i], result.monthly_balance[i + 1])

    def test_flat_rate_informal_loan_schedule(self):
        """Test informal moneylender loan: ₹50,000 at 3% per month (36% APR) for 12 months."""
        loan = LoanInput(
            principal=50000.0,
            interest_rate=3.0,
            rate_period=RatePeriod.MONTHLY,
            tenure_months=12,
            interest_method=InterestMethod.FLAT_RATE,
            monthly_prepayment=0.0,
        )
        result = LoanEngine.calculate(loan)

        self.assertEqual(len(result.monthly_balance), 12)
        self.assertAlmostEqual(result.monthly_payment, 5666.67, places=2)
        self.assertAlmostEqual(result.total_interest, 18000.0, places=2)
        self.assertAlmostEqual(result.total_repayment, 68000.0, places=2)
        self.assertEqual(result.debt_free_month, 12)
        self.assertAlmostEqual(result.monthly_balance[-1], 0.0, places=2)

        # Principal component is 50000 / 12 = 4166.67 per month
        # Month 1 closing balance: 50000 - 4166.67 = 45833.33
        self.assertAlmostEqual(result.monthly_balance[0], 45833.33, places=2)

    def test_simple_interest_bullet_schedule(self):
        """Test crop / harvest loan: ₹40,000 at 2% per month for 6 months."""
        loan = LoanInput(
            principal=40000.0,
            interest_rate=2.0,
            rate_period=RatePeriod.MONTHLY,
            tenure_months=6,
            interest_method=InterestMethod.SIMPLE_INTEREST_BULLET,
            monthly_prepayment=0.0,
        )
        result = LoanEngine.calculate(loan)

        self.assertEqual(len(result.monthly_balance), 6)
        # Months 1 to 5: Principal remains intact at ₹40,000
        for m in range(5):
            self.assertAlmostEqual(result.monthly_balance[m], 40000.0, places=2)
            self.assertAlmostEqual(result.amortization_table[m].payment, 800.0, places=2)
            self.assertAlmostEqual(result.amortization_table[m].interest_paid, 800.0, places=2)

        # Month 6 (Harvest maturity): Full ₹40,000 + ₹800 interest paid
        self.assertAlmostEqual(result.monthly_balance[5], 0.0, places=2)
        self.assertAlmostEqual(result.amortization_table[5].payment, 40800.0, places=2)
        self.assertAlmostEqual(result.total_interest, 4800.0, places=2)
        self.assertAlmostEqual(result.total_repayment, 44800.0, places=2)
        self.assertEqual(result.debt_free_month, 6)

    def test_prepayment_shortens_tenure(self):
        """Verify that adding monthly prepayment reduces tenure and total interest."""
        base_loan = LoanInput(
            principal=100000.0,
            interest_rate=18.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=24,
            interest_method=InterestMethod.REDUCING_BALANCE,
            monthly_prepayment=0.0,
        )
        prepaid_loan = LoanInput(
            principal=100000.0,
            interest_rate=18.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=24,
            interest_method=InterestMethod.REDUCING_BALANCE,
            monthly_prepayment=2000.0,  # extra ₹2,000 per month
        )

        base_res = LoanEngine.calculate(base_loan)
        prepaid_res = LoanEngine.calculate(prepaid_loan)

        # Prepayment must clear the loan earlier
        self.assertLess(prepaid_res.debt_free_month, base_res.debt_free_month)
        # Prepayment must result in less total interest
        self.assertLess(prepaid_res.total_interest, base_res.total_interest)

    def test_zero_interest_loan(self):
        """Zero interest loan (e.g. friendly loan or 0% subsidy scheme)."""
        loan = LoanInput(
            principal=12000.0,
            interest_rate=0.0,
            rate_period=RatePeriod.ANNUAL,
            tenure_months=12,
            interest_method=InterestMethod.REDUCING_BALANCE,
        )
        result = LoanEngine.calculate(loan)

        self.assertAlmostEqual(result.monthly_payment, 1000.0, places=2)
        self.assertAlmostEqual(result.total_interest, 0.0, places=2)
        self.assertAlmostEqual(result.total_repayment, 12000.0, places=2)
        self.assertAlmostEqual(result.monthly_balance[-1], 0.0, places=2)

    def test_input_validation(self):
        """Invalid inputs should raise descriptive ValueError."""
        # Zero or negative principal
        with self.assertRaises(ValueError):
            LoanInput(principal=0, interest_rate=10)
        with self.assertRaises(ValueError):
            LoanInput(principal=-5000, interest_rate=10)

        # Negative interest rate
        with self.assertRaises(ValueError):
            LoanInput(principal=10000, interest_rate=-2)

        # Zero or negative tenure
        with self.assertRaises(ValueError):
            LoanInput(principal=10000, interest_rate=10, tenure_months=0)

        # Negative prepayment
        with self.assertRaises(ValueError):
            LoanInput(principal=10000, interest_rate=10, monthly_prepayment=-100)


if __name__ == "__main__":
    unittest.main()
