"""Loan Mathematics Engine for DebtSight."""

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
from .engine import LoanEngine

__all__ = [
    "LoanEngine",
    "LoanInput",
    "LoanScheduleResult",
    "MonthlyRecord",
    "InterestMethod",
    "RatePeriod",
    "calculate_reducing_emi",
    "calculate_flat_total_interest",
    "calculate_flat_monthly_payment",
    "calculate_approx_reducing_apr_from_flat",
    "to_annual_percentage_rate",
    "to_monthly_fractional_rate",
]
