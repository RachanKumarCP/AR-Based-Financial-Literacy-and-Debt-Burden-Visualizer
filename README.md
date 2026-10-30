# DebtSight — See Your Debt
### AR-Based Financial Literacy and Debt Burden Visualizer

An AR mobile app that visualizes loan debt as a growing 3D object, using ML-based risk forecasting to help rural, semi-literate borrowers intuitively compare informal vs. formal credit—no numeric literacy required.

---

## 1. Project Objectives

1. **Accept Loan Information**: Principal amount, interest rate, tenure, repayment frequency, lender type, and borrower profile.
2. **Calculate Monthly Outstanding Balances**: Transparent financial mathematics covering multiple rural and institutional lending methods (flat rate, reducing balance EMI, bullet repayment).
3. **Estimate Default Risk**: Machine Learning probability estimation calibrated to borrower and loan characteristics.
4. **Calculate Financial Burden Index**: A combined metric reflecting relative debt level and default risk.
5. **Visualize Burden via 3D AR**: Real-world anchored 3D object (e.g., rice sack or coin stack) whose size, darkness, and shaking intuitively convey burden and risk to low-literacy users.
6. **Compare Loan Alternatives**: Highlight differences between high-interest informal loans (moneylenders) and formal alternatives (Banks, SHGs).
7. **Simulate Prepayments**: Demonstrate how extra monthly payments reduce tenure and interest.
8. **Explain Risks Simply**: Plain-language insights avoiding complex financial jargon.
9. **Support Contacts**: Direct users to verified formal financial institutions and counseling resources.

---

## 2. Team Structure & Module Ownership

| Member | Domain & Modules | Responsibilities |
| :--- | :--- | :--- |
| **Revanth** | ML, Loan Math, Integration | Loan mathematics engine, ML training & evaluation, mobile ML preparation, integration layer, burden index. |
| **Rachan** | Frontend & UI | Android UI screens, input forms, timeline slider, loan comparison, voice & regional language localization. |
| **Rakesh** | Unity AR | AR Foundation / ARCore XR setup, plane detection, 3D object scaling (burden), tinting & shaking (risk). |

---

## 3. Repository Architecture

```text
DebtSight/
├── App/                     # Android / Unity application project files
├── Revanth/                 # Revanth's engineering modules
│   ├── Loan_Math/           # Core financial calculation engine & formulas
│   ├── ML/                  # ML datasets, exploration, pipelines, exported models
│   └── Integration/         # Burden index calculation & cross-module bridge
├── Shared/                  # Team interface contracts and shared test cases
│   ├── contracts/           # API and data structure contracts (PROJECT_INTERFACES.md)
│   └── test_cases/          # Cross-module verification test cases
├── Testing/                 # Automated test suites (unit, integration)
│   ├── unit/                # Unit tests for mathematics, preprocessing, models
│   └── integration/         # End-to-end integration tests
├── Assets_Source/           # 3D models, textures, audio, visual assets
├── Project_Management/      # Status tracking, sprint notes, roadmap
├── README.md                # Project documentation
└── .gitignore               # Ignored build and temporary files
```

---

## 4. Shared Interface Contracts

Shared data contracts between Frontend, Backend (Revanth's modules), and Unity AR are formally specified in [`Shared/contracts/PROJECT_INTERFACES.md`](Shared/contracts/PROJECT_INTERFACES.md).

---

## 5. Branching Strategy

- `main`: Protected production baseline.
- `revanth-dev`: ML, Loan Mathematics, and Integration development.
- `rachan-dev`: Android UI and frontend development.
- `rakesh-dev`: Unity AR scenes, shaders, and interaction.
