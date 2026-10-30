# DebtSight — Machine Learning Dataset Research & Selection

This document establishes the evaluation criteria, candidate sources, and technical requirements for the DebtSight default risk prediction model.

---

## 1. Machine Learning Task Definition

- **Objective**: Binary classification estimating the probability of default or severe repayment distress ($y \in \{0, 1\}$).
- **Output**: Calibrated risk probability $\hat{p} \in [0.0, 1.0]$.
- **Contract Input Features**:
  1. `amount`: Principal loan amount in INR.
  2. `rate`: Standardized Annual Percentage Rate (APR %).
  3. `tenure`: Total duration in months.
  4. `lender_type`: Categorical integer (`0` = Bank / Formal / MUDRA, `1` = SHG / JLG, `2` = Informal Moneylender).
  5. `income_bracket`: Categorical integer (`0` = <₹10k, `1` = ₹10k–₹25k, `2` = ₹25k–₹50k, `3` = >₹50k/mo).

> [!CAUTION] Crucial ML Principles for DebtSight
> - We do **not** claim to predict the exact month of default.
> - Default probability is **not** a guaranteed debt-trap prediction.
> - We must **never** fabricate dataset columns, fake training numbers, or pretend a foreign dataset accurately models rural Indian borrowers without explicit calibration and disclaimers.

---

## 2. Evaluation of Candidate Datasets

| Candidate Dataset | Source | Regional Context | Pros | Cons / Gaps | Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kaggle / RBI Microfinance & SHG Repayment** | Indian Open Data / RBI Research | Rural & Semi-Urban India | Directly represents Indian borrower demographics, loan sizes in INR. | Often aggregated by district rather than individual loan-level records. | **High (if individual micro-level records located)** |
| **NABARD All India Rural Financial Inclusion Survey (NAFIS)** | NABARD / Govt. of India | Rural India (pan-India farm & non-farm households) | Authentic rural Indian credit sources (moneylender vs bank vs SHG), household income. | Survey dataset; default labels must be derived from repayment status questions. | **High (Gold standard for ground truth context)** |
| **Kiva Microfinance Loans** | Kiva Open Data | Developing economies (global microfinance) | Real microfinance loans, loan amounts, repayment terms, borrower groups. | Primarily formal/partner MFIs; lacks informal high-rate moneylenders; international mix. | **Moderate (useful for synthetic transfer / benchmark)** |
| **LendingClub / Home Credit** | Kaggle (US / Eastern Europe) | Urban / International Formal Credit | High volume, clean feature set. | **Inappropriate for primary rural Indian inference**: Different lending mechanics, credit scoring infrastructure (FICO/bureau vs unbanked). | **Not Recommended for Production** |

---

## 3. Dataset Preconditions Before Model Training

Before Phase 2 training begins:
1. **Verified Dataset Source**: Must obtain and verify raw CSV / Parquet data with verifiable provenance.
2. **Feature Mapping**: Verify that features can be cleanly mapped to `[amount, rate, tenure, lender_type, income_bracket]` without data leakage.
3. **Target Label Definition**: Clarify target definition (e.g., 90+ days past due `DPD90`, loan write-off, or self-reported default).
4. **Class Imbalance**: Measure default class ratio (typically 3%–15% in microfinance) and establish evaluation metrics (PR-AUC, ROC-AUC, Brier score calibration rather than plain accuracy).
