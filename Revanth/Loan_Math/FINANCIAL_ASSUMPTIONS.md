# DebtSight — Loan Mathematics & Financial Assumptions

This document defines the mathematical models, formulas, assumptions, and edge cases implemented in DebtSight's Loan Mathematics Engine (`Revanth/Loan_Math/`).

---

## 1. Context: Rural and Informal Lending in India

Rural and low-income borrowers in India navigate two very different credit worlds:

1. **Formal Lenders (Banks, RRBs, NBFC-MFIs, SHGs)**:
   - Regulated under Reserve Bank of India (RBI) guidelines.
   - Use **Reducing Balance Amortization** (Equated Monthly Installment / EMI).
   - Annual Percentage Rates (APR) are clearly declared, typically ranging from 7%–14% for agricultural/priority loans and 18%–26% for microfinance loans.
   - Transparent repayment schedules where every repayment reduces outstanding principal.

2. **Informal Lenders (Moneylenders, *Sahukars*, Traders, Pawn Brokers)**:
   - Unregulated, often operating without written contracts or with promissory notes (*dastavej*).
   - Quote interest on a **monthly basis** (e.g., "₹2 per ₹100 per month" = 2% per month = 24% p.a.; "₹3 per ₹100 per month" = 3% per month = 36% p.a.; "₹5 per ₹100 per month" = 60% p.a.).
   - Frequently use **Flat Rate Interest** or **Interest-Only Bullet Repayment**.
   - With flat rate interest, the borrower continues paying interest on the initial loan amount even when most of the principal has been repaid, resulting in an effective APR that is nearly **double** the nominal stated rate.
   - With bullet loans, borrowers pay only monthly interest and struggle to repay the lump-sum principal at harvest time, leading to cyclical debt traps.

---

## 2. Core Mathematical Models

### 2.1 Model A: Reducing Balance (EMI)
**Used by**: Commercial Banks, Self-Help Groups (SHGs), NBFC-MFIs.

#### Formulas:
- Let $P$ = Principal amount.
- Let $r$ = Periodic monthly interest rate = $\frac{\text{APR}}{12 \times 100}$.
- Let $n$ = Total tenure in months.

The Equated Monthly Installment ($\text{EMI}$) is calculated using the standard annuity formula:

$$\text{EMI} = P \times \frac{r(1 + r)^n}{(1 + r)^n - 1} \quad (\text{for } r > 0)$$

If $r = 0$ (interest-free loan):
$$\text{EMI} = \frac{P}{n}$$

#### Monthly Amortization Schedule (for month $t \in [1, n]$):
1. **Interest for month $t$**:
   $$I_t = B_{t-1} \times r$$
2. **Principal repaid in month $t$**:
   $$P_t = \text{EMI} - I_t + \text{Prepayment}_t$$
3. **Closing balance for month $t$**:
   $$B_t = \max(0, B_{t-1} - P_t)$$
   Where $B_0 = P$.

---

### 2.2 Model B: Flat Rate Interest
**Used by**: Informal moneylenders, small retail finance.

#### Formulas:
- Total interest is calculated once on the initial principal for the full duration:
  $$I_{\text{total}} = P \times \frac{\text{APR}}{100} \times \frac{n}{12}$$
- Total amount to repay:
  $$A_{\text{total}} = P + I_{\text{total}}$$
- Fixed Monthly Installment:
  $$\text{Payment} = \frac{A_{\text{total}}}{n} = \frac{P}{n} + \frac{I_{\text{total}}}{n}$$
- In each month $t$:
  - Principal portion: $P_t = \frac{P}{n} + \text{Prepayment}_t$
  - Interest portion: $I_t = \frac{I_{\text{total}}}{n}$
  - Outstanding principal balance: $B_t = \max(0, B_{t-1} - P_t)$

> [!IMPORTANT] The Flat Rate Trap
> In a flat rate loan, because interest is charged on the original $P$ throughout, the borrower is paying interest on money they have already repaid. For a 12-month loan with a stated 24% flat rate, the effective reducing balance APR is approximately **41.7%**!

---

### 2.3 Model C: Simple Interest Bullet / Balloon Repayment
**Used by**: Agricultural moneylenders during sowing/harvest cycles.

#### Schedule:
- Months $1$ to $n-1$: Borrower pays monthly interest only.
  $$\text{Payment}_t = P \times r$$
  $$B_t = P$$
- Month $n$ (Harvest / Maturity): Borrower pays the final monthly interest plus the full principal:
  $$\text{Payment}_n = P + (P \times r)$$
  $$B_n = 0$$

If borrower is unable to repay $P$ in month $n$, the loan is rolled over, compounding the debt.

---

## 3. Explicit Financial Assumptions Identified

1. **Rate Periodicity**:
   - The user must explicitly indicate whether the entered interest rate is **Annual** or **Monthly**.
   - If entered as monthly (e.g. 3% / month), it is converted to Annual Percentage Rate: $\text{APR} = \text{rate}_{\text{monthly}} \times 12$.
2. **First Payment Timing**:
   - Month 0 represents loan disbursement ($B_0 = P$).
   - Month 1 represents the first payment due date, exactly 30 days / 1 month after disbursement.
3. **Prepayment Allocation**:
   - Any extra prepayment is applied directly toward reducing outstanding principal.
   - Prepayments reduce total interest and shorten the loan payoff timeline (`debt_free_month`).
4. **Rounding and Precision**:
   - Intermediate calculations use standard 64-bit floating point precision.
   - Final currency outputs are rounded to 2 decimal places (paise).
5. **Edge Cases**:
   - Principal $\le 0$: Rejected with `ValueError`.
   - Tenure $\le 0$: Rejected with `ValueError`.
   - Interest rate $< 0$: Rejected with `ValueError`.
   - Interest rate $= 0$: Handled cleanly (Principal divided evenly by tenure, zero interest).
   - Prepayment > remaining balance: Final payment clamped to exact remaining balance plus accrued interest; loan marked paid off.
