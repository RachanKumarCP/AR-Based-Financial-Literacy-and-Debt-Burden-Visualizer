"""Mathematical formulas for loan interest and repayment schedules.

This module provides pure mathematical functions without external dependencies.
All formulas are documented with their financial derivation and domain context.
"""

from typing import Tuple
from .models import RatePeriod


def to_annual_percentage_rate(rate: float, period: RatePeriod) -> float:
    """Converts declared rate to standard Annual Percentage Rate (APR %).

    In informal Indian credit, interest is often quoted monthly:
    "3% vaddi" means 3% per month -> 3 * 12 = 36% p.a.
    """
    if period == RatePeriod.MONTHLY:
        return rate * 12.0
    return rate


def to_monthly_fractional_rate(rate: float, period: RatePeriod) -> float:
    """Converts declared percentage rate into a monthly decimal fraction (r).

    Example:
        Annual 24%  -> (24 / 12) / 100 = 0.02
        Monthly 2%  -> 2 / 100 = 0.02
    """
    if period == RatePeriod.MONTHLY:
        return rate / 100.0
    return (rate / 12.0) / 100.0


def calculate_reducing_emi(principal: float, monthly_rate: float, tenure_months: int) -> float:
    """Calculates Equated Monthly Installment (EMI) for reducing balance loans.

    Formula:
        EMI = P * [r * (1 + r)^n] / [(1 + r)^n - 1]

    Derivation:
        The present value of an annuity of n payments of amount E at monthly
        interest rate r is:
        P = E * [1 - (1 + r)^(-n)] / r
        Solving for E gives the standard EMI formula.

    Special case:
        If monthly_rate == 0, EMI = P / n.
    """
    if tenure_months < 1:
        raise ValueError(f"Tenure must be >= 1 month, got {tenure_months}")
    if principal < 0:
        raise ValueError(f"Principal cannot be negative, got {principal}")
    if monthly_rate < 0:
        raise ValueError(f"Interest rate cannot be negative, got {monthly_rate}")

    if monthly_rate == 0.0:
        return principal / tenure_months

    # Standard annuity formula
    factor = (1.0 + monthly_rate) ** tenure_months
    emi = principal * (monthly_rate * factor) / (factor - 1.0)
    return emi


def calculate_flat_total_interest(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Calculates total interest for a flat rate loan.

    Formula:
        I = P * (APR / 100) * (tenure_months / 12)

    In flat rate lending, interest is charged on the initial principal for the entire
    term regardless of how much principal has already been repaid each month.
    """
    if principal < 0 or annual_rate_pct < 0 or tenure_months < 1:
        raise ValueError("Invalid parameters for flat rate calculation")

    return principal * (annual_rate_pct / 100.0) * (tenure_months / 12.0)


def calculate_flat_monthly_payment(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Calculates fixed monthly installment under flat rate interest.

    Formula:
        Payment = (P + Total_Interest) / tenure_months
    """
    total_interest = calculate_flat_total_interest(principal, annual_rate_pct, tenure_months)
    return (principal + total_interest) / tenure_months


def calculate_approx_reducing_apr_from_flat(flat_annual_rate_pct: float, tenure_months: int) -> float:
    """Approximates the true reducing balance APR corresponding to a flat rate.

    Financial insight:
        Because the borrower repays principal steadily over n months, the average
        principal balance outstanding is approximately P * (n + 1) / (2n), or about
        half the original loan. Charging flat interest on the full P therefore results
        in an effective APR nearly double the stated flat rate:
        Effective APR ~= Flat_Rate * [2n / (n + 1)]
    """
    if tenure_months <= 1:
        return flat_annual_rate_pct
    return flat_annual_rate_pct * (2.0 * tenure_months / (tenure_months + 1.0))
