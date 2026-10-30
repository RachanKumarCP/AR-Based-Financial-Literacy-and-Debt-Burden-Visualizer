# DebtSight — Development Status Tracker

This tracking sheet records the current state of features, responsible team members, test evidence, and open dependencies across all project modules.

---

## 1. Feature Status Summary Table

| Feature / Module | Owner | Status | Key Files | Test Evidence |
| :--- | :---: | :---: | :--- | :--- |
| **Repo Scaffolding & Git Structure** | Revanth | **COMPLETED** | `README.md`, `.gitignore`, `Shared/contracts/PROJECT_INTERFACES.md` | Verified clean git tracking, initial commit, branch creation |
| **Loan Math — Financial Assumptions Spec** | Revanth | **COMPLETED** | `Revanth/Loan_Math/FINANCIAL_ASSUMPTIONS.md` | Mathematical formulas & edge cases documented |
| **Loan Math — Core Engine & Formulas** | Revanth | **IN PROGRESS** | `Revanth/Loan_Math/engine.py`, `formulas.py` | Unit tests under development |
| **Loan Math — Automated Test Suite** | Revanth | **IN PROGRESS** | `Testing/unit/test_loan_math.py` | Tests with verified manual financial calculations |
| **ML — Dataset Research & Selection** | Revanth | **NOT STARTED** | `Revanth/ML/DATASET_RESEARCH.md` | Awaiting dataset verification |
| **ML — Data Cleaning & Feature Pipeline** | Revanth | **NOT STARTED** | `Revanth/ML/pipeline.py` | None |
| **ML — Baseline Model Training & Eval** | Revanth | **NOT STARTED** | `Revanth/ML/train.py`, `evaluate.py` | None |
| **ML — Mobile Inference (TFLite Prep)** | Revanth | **NOT STARTED** | `Revanth/ML/export.py` | None |
| **Integration — Burden Index Engine** | Revanth | **NOT STARTED** | `Revanth/Integration/burden.py` | None |
| **Integration — Shared Result Builder** | Revanth | **NOT STARTED** | `Revanth/Integration/engine.py` | None |
| **Frontend UI — Loan Input Screen** | Rachan | **NOT STARTED** | External Android UI | None |
| **Frontend UI — Timeline & Comparison** | Rachan | **NOT STARTED** | External Android UI | None |
| **Unity AR — Scene & Plane Detection** | Rakesh | **NOT STARTED** | External Unity AR | None |
| **Unity AR — Visualizer (Burden & Risk)** | Rakesh | **NOT STARTED** | `IDebtVisualizer.cs` | None |

---

## 2. Detailed Milestone Logs

### Milestone 0: Workspace Audit and Repository Initialization
- **Date**: 2026-10-30
- **Action**: Inspected empty directory, initialized Git on `main`, created `.gitignore`, established folder structure, drafted `README.md` and `Shared/contracts/PROJECT_INTERFACES.md`.
- **Status**: **COMPLETED**.

### Milestone 1: Loan Mathematics Engine
- **Objective**: Build a modular, transparent financial calculation engine in Python with zero external math dependencies.
- **Formulas Supported**:
  1. Flat Rate Interest (informal loans).
  2. Reducing Balance EMI (formal bank / MFI loans).
  3. Simple Interest Bullet Repayment (lump sum informal harvest loans).
- **Status**: **IN PROGRESS**.

---

## 3. Outstanding Issues & Dependencies

1. **Frontend Input Schema**: Need confirmation from Rachan on adding `income_bracket` to the UI input form to support ML inference.
2. **ML Dataset Identification**: Need to evaluate authentic Indian microfinance / rural credit datasets (e.g., NABARD / RBI survey tables or public microfinance datasets on Kaggle/UCI) before training.
