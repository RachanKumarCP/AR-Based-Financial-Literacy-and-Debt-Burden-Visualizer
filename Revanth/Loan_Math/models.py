"""Data models and enums for the DebtSight Loan Mathematics Engine.

Defines input contracts, validation constraints, and structured output
types for loan amortization schedules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class InterestMethod(str, Enum):
    """Interest calculation method."""
    REDUCING_BALANCE = "reducing_balance"  # Bank / MFI standard EMI
    FLAT_RATE = "flat_rate"                # Moneylender flat interest
    SIMPLE_INTEREST_BULLET = "simple_interest_bullet"  # Interest monthly, principal at end


class RatePeriod(str, Enum):
    """Periodicity of the declared interest rate."""
    ANNUAL = "annual"    # e.g., 24.0% per annum
    MONTHLY = "monthly"  # e.g., 2.0% or 3.0% per month


@dataclass(frozen=True)
class LoanInput:
    """Validated input parameters for a loan calculation.

    Attributes:
        principal: Total loan principal amount in INR (must be > 0).
        interest_rate: Declared interest percentage (e.g. 24.0 for 24%, must be >= 0).
        rate_period: Whether interest_rate is ANNUAL or MONTHLY.
        tenure_months: Total duration of the loan in months (must be integer >= 1).
        interest_method: Calculation methodology (Reducing balance, Flat, Bullet).
        monthly_prepayment: Optional additional payment applied to principal each month (>= 0).
    """
    principal: float
    interest_rate: float
    rate_period: RatePeriod = RatePeriod.ANNUAL
    tenure_months: int = 12
    interest_method: InterestMethod = InterestMethod.REDUCING_BALANCE
    monthly_prepayment: float = 0.0

    def __post_init__(self):
        # Validation checks
        if self.principal <= 0:
            raise ValueError(f"Principal must be strictly positive (> 0), got ₹{self.principal:,.2f}")
        if self.interest_rate < 0:
            raise ValueError(f"Interest rate cannot be negative, got {self.interest_rate}%")
        if self.tenure_months < 1:
            raise ValueError(f"Tenure must be at least 1 month, got {self.tenure_months}")
        if self.monthly_prepayment < 0:
            raise ValueError(f"Monthly prepayment cannot be negative, got ₹{self.monthly_prepayment:,.2f}")


@dataclass
class MonthlyRecord:
    """Represents financial values for a single payment cycle."""
    month: int
    opening_balance: float
    payment: float
    principal_paid: float
    interest_paid: float
    closing_balance: float


@dataclass
class LoanScheduleResult:
    """Complete calculation result and schedule from LoanEngine.

    Attributes:
        monthly_balance: Sequence of closing principal balances at each month [B_1, B_2, ...].
        monthly_payment: Scheduled monthly installment amount (before prepayments).
        total_interest: Total interest paid across the loan tenure in INR.
        total_repayment: Total payments made (principal + interest) in INR.
        debt_free_month: The month number in which outstanding principal reached 0.
        effective_annual_rate: The effective annual percentage rate (APR).
        amortization_table: Detailed month-by-month record breakdown.
    """
    monthly_balance: List[float]
    monthly_payment: float
    total_interest: float
    total_repayment: float
    debt_free_month: int
    effective_annual_rate: float
    amortization_table: List[MonthlyRecord] = field(default_factory=list)
