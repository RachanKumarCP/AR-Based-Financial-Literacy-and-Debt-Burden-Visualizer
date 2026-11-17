"""Burden Index calculation module for DebtSight.

Computes the visual burden index sequence over a loan repayment timeline:
    burden(t) = w_debt * normalized_debt(t) + w_risk * risk_probability
where:
    - normalized_debt(t) = monthly_balance[t] / principal  (clamped to [0.0, 1.0])
    - risk_probability in [0.0, 1.0] (from ML model)
    - Default weights: w_debt = 0.6, w_risk = 0.4
"""

from typing import List


DEFAULT_DEBT_WEIGHT: float = 0.6
DEFAULT_RISK_WEIGHT: float = 0.4


def compute_normalized_debt(balance: float, principal: float) -> float:
    """Computes clamped normalized debt ratio between 0.0 and 1.0.

    Args:
        balance: Outstanding debt balance at time t.
        principal: Original starting loan principal.

    Returns:
        Float clamped between 0.0 and 1.0.
    """
    if principal <= 0:
        return 0.0
    return max(0.0, min(1.0, float(balance) / float(principal)))


def compute_burden_timeline(
    monthly_balances: List[float],
    principal: float,
    risk_probability: float,
    debt_weight: float = DEFAULT_DEBT_WEIGHT,
    risk_weight: float = DEFAULT_RISK_WEIGHT,
) -> List[float]:
    """Generates monthly burden index values over the repayment timeline.

    Args:
        monthly_balances: Outstanding balances month by month.
        principal: Starting loan principal amount.
        risk_probability: Calibrated default risk probability in [0.0, 1.0].
        debt_weight: Weight assigned to remaining debt ratio (default 0.6).
        risk_weight: Weight assigned to default risk (default 0.4).

    Returns:
        List of rounded floats in [0.0, 1.0] representing monthly visual burden.
    """
    clamped_risk = max(0.0, min(1.0, float(risk_probability)))

    burden_indices: List[float] = []
    for bal in monthly_balances:
        norm_debt = compute_normalized_debt(bal, principal)
        burden = (debt_weight * norm_debt) + (risk_weight * clamped_risk)
        clamped_burden = max(0.0, min(1.0, burden))
        burden_indices.append(round(clamped_burden, 3))

    return burden_indices
