"""Loan Mathematics Engine for DebtSight.

Provides modular, transparent loan schedule calculations supporting:
- Reducing Balance (standard bank/MFI EMI)
- Flat Rate Interest (informal moneylender style)
- Simple Interest Bullet Repayment (crop season / lump sum harvest)

Zero external dependencies; fully testable in any standard Python environment.
"""

from typing import List, Optional
from .models import (
    InterestMethod,
    LoanInput,
    LoanScheduleResult,
    MonthlyRecord,
    RatePeriod,
)
from .formulas import (
    calculate_approx_reducing_apr_from_flat,
    calculate_flat_monthly_payment,
    calculate_flat_total_interest,
    calculate_reducing_emi,
    to_annual_percentage_rate,
    to_monthly_fractional_rate,
)


class LoanEngine:
    """Core calculation engine for loan amortization schedules."""

    @classmethod
    def calculate(cls, loan_input: LoanInput) -> LoanScheduleResult:
        """Calculates amortization schedule and totals for the given loan input.

        Args:
            loan_input: Validated LoanInput instance.

        Returns:
            LoanScheduleResult with monthly balances, payments, and totals.
        """
        method = loan_input.interest_method

        if method == InterestMethod.REDUCING_BALANCE:
            return cls._calculate_reducing_balance(loan_input)
        elif method == InterestMethod.FLAT_RATE:
            return cls._calculate_flat_rate(loan_input)
        elif method == InterestMethod.SIMPLE_INTEREST_BULLET:
            return cls._calculate_bullet_repayment(loan_input)
        else:
            raise ValueError(f"Unsupported interest method: {method}")

    @classmethod
    def _calculate_reducing_balance(cls, loan_input: LoanInput) -> LoanScheduleResult:
        """Standard Equated Monthly Installment (EMI) reducing balance schedule."""
        p = loan_input.principal
        r = to_monthly_fractional_rate(loan_input.interest_rate, loan_input.rate_period)
        apr = to_annual_percentage_rate(loan_input.interest_rate, loan_input.rate_period)
        n = loan_input.tenure_months
        prepayment = loan_input.monthly_prepayment

        base_emi = calculate_reducing_emi(p, r, n)

        current_balance = p
        amortization: List[MonthlyRecord] = []
        monthly_balances: List[float] = []
        total_interest = 0.0
        total_repayment = 0.0
        debt_free_month = n

        for m in range(1, n + 1):
            if current_balance <= 0.0001:
                # Loan already fully paid off in earlier months
                record = MonthlyRecord(
                    month=m,
                    opening_balance=0.0,
                    payment=0.0,
                    principal_paid=0.0,
                    interest_paid=0.0,
                    closing_balance=0.0,
                )
                amortization.append(record)
                monthly_balances.append(0.0)
                continue

            opening = current_balance
            month_interest = opening * r

            # Total contractual payment + extra prepayment
            planned_payment = base_emi + prepayment

            # Ensure we never overpay past the remaining balance + interest
            max_needed = opening + month_interest
            actual_payment = min(planned_payment, max_needed)

            principal_portion = max(0.0, actual_payment - month_interest)
            closing = max(0.0, opening - principal_portion)

            # Round closing balance if within fractions of a rupee
            if closing < 0.01:
                closing = 0.0

            total_interest += month_interest
            total_repayment += actual_payment

            amortization.append(
                MonthlyRecord(
                    month=m,
                    opening_balance=round(opening, 2),
                    payment=round(actual_payment, 2),
                    principal_paid=round(principal_portion, 2),
                    interest_paid=round(month_interest, 2),
                    closing_balance=round(closing, 2),
                )
            )
            monthly_balances.append(round(closing, 2))
            current_balance = closing

            if closing == 0.0 and debt_free_month == n:
                debt_free_month = m

        return LoanScheduleResult(
            monthly_balance=monthly_balances,
            monthly_payment=round(base_emi, 2),
            total_interest=round(total_interest, 2),
            total_repayment=round(total_repayment, 2),
            debt_free_month=debt_free_month,
            effective_annual_rate=round(apr, 2),
            amortization_table=amortization,
        )

    @classmethod
    def _calculate_flat_rate(cls, loan_input: LoanInput) -> LoanScheduleResult:
        """Flat rate interest schedule where interest is based on full original principal."""
        p = loan_input.principal
        apr = to_annual_percentage_rate(loan_input.interest_rate, loan_input.rate_period)
        n = loan_input.tenure_months
        prepayment = loan_input.monthly_prepayment

        total_interest_contracted = calculate_flat_total_interest(p, apr, n)
        base_monthly_payment = calculate_flat_monthly_payment(p, apr, n)
        base_monthly_interest = total_interest_contracted / n
        base_monthly_principal = p / n

        current_balance = p
        amortization: List[MonthlyRecord] = []
        monthly_balances: List[float] = []
        accumulated_interest = 0.0
        accumulated_repayment = 0.0
        debt_free_month = n

        for m in range(1, n + 1):
            if current_balance <= 0.0001:
                record = MonthlyRecord(
                    month=m,
                    opening_balance=0.0,
                    payment=0.0,
                    principal_paid=0.0,
                    interest_paid=0.0,
                    closing_balance=0.0,
                )
                amortization.append(record)
                monthly_balances.append(0.0)
                continue

            opening = current_balance
            month_interest = base_monthly_interest
            principal_paid = min(opening, base_monthly_principal + prepayment)
            actual_payment = principal_paid + month_interest
            closing = max(0.0, opening - principal_paid)

            if closing < 0.01:
                closing = 0.0

            accumulated_interest += month_interest
            accumulated_repayment += actual_payment

            amortization.append(
                MonthlyRecord(
                    month=m,
                    opening_balance=round(opening, 2),
                    payment=round(actual_payment, 2),
                    principal_paid=round(principal_paid, 2),
                    interest_paid=round(month_interest, 2),
                    closing_balance=round(closing, 2),
                )
            )
            monthly_balances.append(round(closing, 2))
            current_balance = closing

            if closing == 0.0 and debt_free_month == n:
                debt_free_month = m

        effective_apr = calculate_approx_reducing_apr_from_flat(apr, n)

        return LoanScheduleResult(
            monthly_balance=monthly_balances,
            monthly_payment=round(base_monthly_payment, 2),
            total_interest=round(accumulated_interest, 2),
            total_repayment=round(accumulated_repayment, 2),
            debt_free_month=debt_free_month,
            effective_annual_rate=round(effective_apr, 2),
            amortization_table=amortization,
        )

    @classmethod
    def _calculate_bullet_repayment(cls, loan_input: LoanInput) -> LoanScheduleResult:
        """Simple interest bullet repayment schedule (monthly interest, principal at end)."""
        p = loan_input.principal
        r = to_monthly_fractional_rate(loan_input.interest_rate, loan_input.rate_period)
        apr = to_annual_percentage_rate(loan_input.interest_rate, loan_input.rate_period)
        n = loan_input.tenure_months
        prepayment = loan_input.monthly_prepayment

        current_balance = p
        amortization: List[MonthlyRecord] = []
        monthly_balances: List[float] = []
        total_interest = 0.0
        total_repayment = 0.0
        debt_free_month = n

        regular_monthly_interest = p * r

        for m in range(1, n + 1):
            if current_balance <= 0.0001:
                record = MonthlyRecord(
                    month=m,
                    opening_balance=0.0,
                    payment=0.0,
                    principal_paid=0.0,
                    interest_paid=0.0,
                    closing_balance=0.0,
                )
                amortization.append(record)
                monthly_balances.append(0.0)
                continue

            opening = current_balance
            month_interest = opening * r
            total_interest += month_interest

            if m < n:
                # Monthly interest payment + optional prepayment against principal
                principal_portion = min(opening, prepayment)
                actual_payment = month_interest + principal_portion
                closing = max(0.0, opening - principal_portion)
            else:
                # Final month: Pay all remaining principal + month interest
                principal_portion = opening
                actual_payment = month_interest + principal_portion
                closing = 0.0

            if closing < 0.01:
                closing = 0.0

            total_repayment += actual_payment

            amortization.append(
                MonthlyRecord(
                    month=m,
                    opening_balance=round(opening, 2),
                    payment=round(actual_payment, 2),
                    principal_paid=round(principal_portion, 2),
                    interest_paid=round(month_interest, 2),
                    closing_balance=round(closing, 2),
                )
            )
            monthly_balances.append(round(closing, 2))
            current_balance = closing

            if closing == 0.0 and debt_free_month == n:
                debt_free_month = m

        return LoanScheduleResult(
            monthly_balance=monthly_balances,
            monthly_payment=round(regular_monthly_interest, 2),
            total_interest=round(total_interest, 2),
            total_repayment=round(total_repayment, 2),
            debt_free_month=debt_free_month,
            effective_annual_rate=round(apr, 2),
            amortization_table=amortization,
        )
