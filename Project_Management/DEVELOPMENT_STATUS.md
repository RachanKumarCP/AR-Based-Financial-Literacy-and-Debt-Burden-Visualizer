# DebtSight — Development Status Tracker

This tracking sheet records the current state of features, responsible team members, test evidence, and open dependencies across all project modules.

---

## 1. Feature Status Summary Table

| Feature / Module | Owner | Status | Key Files | Test Evidence |
| :--- | :---: | :---: | :--- | :--- |
| **Repo Scaffolding & Git Structure** | Revanth | **COMPLETED** | `README.md`, `.gitignore`, `Shared/contracts/PROJECT_INTERFACES.md` | Verified clean git tracking, initial commit, branch creation |
| **Loan Math — Financial Assumptions Spec** | Revanth | **COMPLETED** | `Revanth/Loan_Math/FINANCIAL_ASSUMPTIONS.md` | Mathematical formulas & edge cases documented |
| **Loan Math — Core Engine & Formulas** | Revanth | **COMPLETED** | `Revanth/Loan_Math/engine.py`, `formulas.py`, `models.py` | 10 unit tests passing (100% pass rate) |
| **Loan Math — Automated Test Suite** | Revanth | **COMPLETED** | `Testing/unit/test_loan_math.py` | Verified against manual calculations (Reducing, Flat, Bullet) |
| **Unity C# Math & AR Bridge** | Revanth | **COMPLETED** | `Shared/csharp/DebtSightMathEngine.cs`, `DebtSightBridge.cs`, `DebtSightRiskPredictor.cs`, `IDebtVisualizer.cs` | Drop-in C# scripts ready with Unity Sentis support |
| **ML — Dataset Research & Selection** | Revanth | **COMPLETED** | `Revanth/ML/DATASET_RESEARCH.md` | Selected `credit_risk_dataset.csv` (32,581 records, 21.8% default rate) |
| **ML — Data Cleaning & Feature Pipeline** | Revanth | **COMPLETED** | `Revanth/ML/data_loader.py`, `preprocessor.py`, `run_pipeline_v2.py` | 10 predictive features with median imputation and scaling |
| **ML — Baseline Model Training & Eval** | Revanth | **COMPLETED** | `Revanth/ML/train.py`, `evaluate.py`, `run_pipeline_v2.py` | Tuned GB: ROC-AUC 0.9246, PR-AUC 0.868, F1 0.7956, Precision 0.9063 |
| **ML — Mobile Inference (ONNX / Sentis)** | Revanth | **COMPLETED** | `Revanth/ML/models/debtsight_risk_model.onnx` | Pure float tensor exported and verified for Unity Sentis |
| **Integration — Burden Index Engine** | Revanth | **COMPLETED** | `Revanth/Integration/burden.py` | Verified decay: `0.6 * debt + 0.4 * risk` |
| **Integration — Master Engine & Results** | Revanth | **COMPLETED** | `Revanth/Integration/engine.py`, `__init__.py` | Full pipeline: Math + ML + Burden + Formal comparison |
| **Integration — Automated Test Suite** | Revanth | **COMPLETED** | `Testing/integration/test_integration_pipeline.py` | 4 end-to-end integration tests (100% pass rate) |
| **Frontend UI — Loan Input Screen** | Rachan | **IN PROGRESS** | Unity UI Canvas, `LoanUIController.cs` | In active Unity development |
| **Frontend UI — Timeline & Comparison** | Rachan | **IN PROGRESS** | Unity UI `ResultsOverlayPanel`, Timeline Slider | In active Unity development |
| **Unity AR — Scene & Plane Detection** | Rakesh | **IN PROGRESS** | XR Origin, AR Plane Manager, Raycast Manager | In active Unity development |
| **Unity AR — Visualizer (Burden & Risk)** | Rakesh | **IN PROGRESS** | `DebtVisualizerReference.cs` | 3D object scaling and danger tinting |

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
