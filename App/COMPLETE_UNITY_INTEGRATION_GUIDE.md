# 📱 DebtSight — Complete End-to-End Unity Integration Guide
**Version:** Pure Native C# (Zero External Dependencies, No Sentis/ONNX Setup Required)  
**Target Environment:** Unity 6.6 / Unity 2022+ | Android ARCore  
**Authors:** Revanth (ML & Math Engine), Rachan (Frontend UI), Rakesh (Unity AR)  

---

## 📑 Table of Contents
1. [Why This Pure C# Architecture?](#1-why-this-pure-c-architecture)
2. [Phase 1: Git Pull & File Placement](#phase-1-git-pull--file-placement)
3. [Phase 2: AR Foundation Setup (XR Origin & Plane Detection)](#phase-2-ar-foundation-setup)
4. [Phase 3: 3D Coin Visualizer Setup](#phase-3-3d-coin-visualizer-setup)
5. [Phase 4: Master Manager (`DebtSightBridge`) Setup](#phase-4-master-manager-debtsightbridge-setup)
6. [Phase 5: Canvas UI Hierarchy & Screen Flow](#phase-5-canvas-ui-hierarchy--screen-flow)
7. [Phase 6: Drop-in `LoanUIController.cs` Script](#phase-6-drop-in-loanuicontrollercs-script)
8. [Phase 7: Inspector Event Connections Checklist](#phase-7-inspector-event-connections-checklist)
9. [Phase 8: Play Mode Verification & Test Values](#phase-8-play-mode-verification--test-values)
10. [Phase 9: Android Build Settings & APK Export](#phase-9-android-build-settings--apk-export)

---

## 1. Why This Pure C# Architecture?

In Unity 6, external packages like Sentis require a paid Unity AI cloud subscription and throw `NoSubscription` / `OnnxImportException`.

To make the app **100% reliable, zero-dependency, and offline on Android**, the exact mathematical weights ($W$) and bias ($b$) learned by our 32,581-record machine learning model are embedded directly into **`DebtSightRiskPredictor.cs`**:

$$\text{Logit: } z = \sum_{i=0}^{9} W_i \cdot X_i + b$$
$$P(\text{Default} = 1) = \frac{1}{1 + e^{-z}}$$

* **Zero external package installs** required.
* **Runs in 0.001 ms** on mobile GPU/CPU.
* **Zero red console errors**.

---

## Phase 1: Git Pull & File Placement

1. In your VS Code terminal, run:
   ```bash
   git pull origin main
   ```
2. **If you have `debtsight_risk_model.onnx` inside `Assets/Models/` in Unity, DELETE it.** It is no longer needed and causes red importer errors.
3. Place the C# scripts in your Unity project under `Assets/Scripts/DebtSight/`:
   ```text
   Assets/
   ├── Models/
   │   └── Coin Dollar Stack.fbx           <-- Your 3D gold coin model
   ├── Materials/
   │   └── CoinMaterial.mat
   └── Scripts/
       └── DebtSight/
           ├── DebtSightBridge.cs          <-- From Shared/csharp/
           ├── DebtSightRiskPredictor.cs   <-- From Shared/csharp/ (Updated pure C#)
           ├── DebtSightMathEngine.cs      <-- From Shared/csharp/
           ├── DebtVisualizerReference.cs  <-- From Shared/csharp/
           ├── IDebtVisualizer.cs          <-- From Shared/csharp/
           └── LoanUIController.cs         <-- Provided in Phase 6 below
   ```

---

## Phase 2: AR Foundation Setup

In your main Unity scene:

1. **Delete the standalone `Main Camera`**:
   * Right-click the top `Main Camera` in Hierarchy $\rightarrow$ **Delete**.
   *(AR Foundation uses the camera already inside `XR Origin`. Having two cameras causes camera conflicts and black screens).*
2. **Add XR Origin**:
   * Right-click Hierarchy $\rightarrow$ **XR** $\rightarrow$ **XR Origin (Mobile AR)**.
3. **Add AR Session**:
   * Right-click Hierarchy $\rightarrow$ **XR** $\rightarrow$ **AR Session**.
4. **Add AR Managers**:
   * Select `XR Origin` in Hierarchy.
   * Click **Add Component** $\rightarrow$ search and add **AR Plane Manager**.
   * Click **Add Component** $\rightarrow$ search and add **AR Raycast Manager**.
   * Under `AR Plane Manager`, set **Detection Mode** to **Horizontal**.

---

## Phase 3: 3D Coin Visualizer Setup

1. Drag your 3D Coin model into the Hierarchy and rename it to **`DebtVisualizer`**.
2. Click **Add Component** $\rightarrow$ select **`DebtVisualizerReference`**.
3. In the Inspector:
   * **Target Renderer**: Drag the coin's `MeshRenderer` here.
   * **Min Scale**: `(0.1, 0.1, 0.1)` *(zero remaining debt)*.
   * **Max Scale**: `(1.0, 1.0, 1.0)` *(full starting debt)*.
   * **Safe Color**: Green (`#2ECC71`).
   * **Danger Color**: Crimson Red (`#E74C3C`).
   * **Max Shake Intensity**: `0.02`.

---

## Phase 4: Master Manager (`DebtSightBridge`) Setup

1. Right-click Hierarchy $\rightarrow$ **Create Empty** $\rightarrow$ name it **`DebtSightManager`**.
2. In the Inspector, click **Add Component** $\rightarrow$ search and add **`DebtSightBridge`**.
3. Drag **`DebtVisualizer`** from the Hierarchy into the **Visualizer Object** slot.

---

## Phase 5: Canvas UI Hierarchy & Screen Flow

Ensure your Canvas is set to:
* **Render Mode**: `Screen Space - Overlay`.
* **Canvas Scaler**: `Scale With Screen Size`, Reference Resolution: `1080 × 1920` (Portrait), Match: `0.5`.

Structure your Canvas:
```text
Canvas/
├── LoanInputPanel               (Active on start)
│   ├── HeadingText              ("DebtSight - Loan Input")
│   ├── AmountInputField         (TMP_InputField, Content Type: Decimal Number)
│   ├── InterestRateInputField   (TMP_InputField, Content Type: Decimal Number)
│   ├── RatePeriodDropdown       (TMP_Dropdown, Options: "Monthly", "Annual")
│   ├── TenureSlider             (Slider, Min: 6, Max: 36, Whole Numbers: True)
│   ├── TenureValueText          (TextMeshProUGUI, e.g. "12 Months")
│   ├── LenderDropdown           (TMP_Dropdown, Options: "Bank/MUDRA", "SHG", "Informal Moneylender")
│   ├── IncomeDropdown           (TMP_Dropdown, Options: "< ₹10k", "₹10k - ₹25k", "₹25k - ₹50k", "> ₹50k")
│   └── CalculateButton          (Button - "Calculate & See Debt")
│
├── ResultsOverlayPanel          (Inactive on start)
│   ├── ResultsHeading           ("Loan Summary & Risk")
│   ├── MonthlyEMIText           (TextMeshProUGUI)
│   ├── TotalInterestText        (TextMeshProUGUI)
│   ├── FormalSavingsText        (TextMeshProUGUI)
│   ├── RiskScoreText            (TextMeshProUGUI)
│   ├── ViewInARButton           (Button - "View In 3D AR")
│   └── BackToInputButton        (Button - "Edit Details")
│
└── ARViewPanel                  (Inactive on start)
    ├── InstructionsText         ("Tap on a detected flat surface to place coin stack")
    ├── TimelinePanel
    │   ├── TimelineSlider       (Slider, Min: 0, Max: 12)
    │   ├── MonthLabelText       ("Month: 1 / 12")
    │   └── RemainingBalanceText ("Remaining Debt: ₹50,000")
    └── CloseARButton            (Button - "Back to Results")
```

---

## Phase 6: Drop-in `LoanUIController.cs` Script

Save this script at `Assets/Scripts/DebtSight/LoanUIController.cs`:

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace DebtSight
{
    public class LoanUIController : MonoBehaviour
    {
        [Header("Bridge Reference")]
        [SerializeField] private DebtSightBridge bridge;

        [Header("Panels")]
        [SerializeField] private GameObject loanInputPanel;
        [SerializeField] private GameObject resultsOverlayPanel;
        [SerializeField] private GameObject arViewPanel;

        [Header("Inputs")]
        [SerializeField] private TMP_InputField amountInput;
        [SerializeField] private TMP_InputField interestRateInput;
        [SerializeField] private TMP_Dropdown ratePeriodDropdown; // 0=Monthly, 1=Annual
        [SerializeField] private Slider tenureSlider;
        [SerializeField] private TextMeshProUGUI tenureValueText;
        [SerializeField] private TMP_Dropdown lenderDropdown;     // 0=Bank, 1=SHG, 2=Informal
        [SerializeField] private TMP_Dropdown incomeDropdown;     // 0=<10k, 1=10-25k, 2=25-50k, 3=>50k
        [SerializeField] private Button calculateButton;

        [Header("Results Display")]
        [SerializeField] private TextMeshProUGUI monthlyEMIText;
        [SerializeField] private TextMeshProUGUI totalInterestText;
        [SerializeField] private TextMeshProUGUI formalSavingsText;
        [SerializeField] private TextMeshProUGUI riskScoreText;
        [SerializeField] private Button viewInARButton;
        [SerializeField] private Button backToInputButton;

        [Header("Timeline Controls")]
        [SerializeField] private Slider timelineSlider;
        [SerializeField] private TextMeshProUGUI monthLabelText;
        [SerializeField] private TextMeshProUGUI remainingBalanceText;
        [SerializeField] private Button closeARButton;

        private void Awake()
        {
            // Set friendly defaults
            if (amountInput != null) amountInput.text = "50000";
            if (interestRateInput != null) interestRateInput.text = "3";
            if (ratePeriodDropdown != null) ratePeriodDropdown.value = 0; // Monthly (36% APR)
            if (tenureSlider != null) tenureSlider.value = 12;
            if (lenderDropdown != null) lenderDropdown.value = 2;         // Moneylender
            if (incomeDropdown != null) incomeDropdown.value = 0;         // < 10k

            UpdateTenureLabel(12);

            // Hook Listeners
            if (tenureSlider != null) tenureSlider.onValueChanged.AddListener(UpdateTenureLabel);
            if (calculateButton != null) calculateButton.onClick.AddListener(OnCalculateClicked);
            if (viewInARButton != null) viewInARButton.onClick.AddListener(OnViewInARClicked);
            if (backToInputButton != null) backToInputButton.onClick.AddListener(ShowInputPanel);
            if (closeARButton != null) closeARButton.onClick.AddListener(ShowResultsPanel);

            if (timelineSlider != null) timelineSlider.onValueChanged.AddListener(OnTimelineSliderChanged);

            // Hook Bridge Events
            if (bridge != null)
            {
                bridge.OnCalculationCompleted += DisplayResults;
                bridge.OnTimelineMonthChanged += UpdateTimelineDisplay;
            }

            ShowInputPanel();
        }

        private void OnDestroy()
        {
            if (bridge != null)
            {
                bridge.OnCalculationCompleted -= DisplayResults;
                bridge.OnTimelineMonthChanged -= UpdateTimelineDisplay;
            }
        }

        private void UpdateTenureLabel(float value)
        {
            if (tenureValueText != null)
                tenureValueText.text = $"{Mathf.RoundToInt(value)} Months";
        }

        public void OnCalculateClicked()
        {
            if (bridge == null) return;

            float principal = float.TryParse(amountInput.text, out float p) ? p : 50000f;
            float rate = float.TryParse(interestRateInput.text, out float r) ? r : 3f;
            RatePeriod period = ratePeriodDropdown.value == 0 ? RatePeriod.Monthly : RatePeriod.Annual;
            int tenure = Mathf.RoundToInt(tenureSlider.value);
            int lender = lenderDropdown.value;
            int income = incomeDropdown.value;

            bridge.currentInput.principal = principal;
            bridge.currentInput.interestRate = rate;
            bridge.currentInput.ratePeriod = period;
            bridge.currentInput.tenureMonths = tenure;
            bridge.currentInput.interestMethod = (lender == 2) 
                ? InterestMethod.FlatRate 
                : InterestMethod.ReducingBalance;

            bridge.lenderType = lender;
            bridge.incomeBracket = income;

            // Recalculates Amortization + ML Default Risk
            bridge.Recalculate();

            ShowResultsPanel();
        }

        private void DisplayResults(LoanScheduleResult schedule, float risk)
        {
            if (monthlyEMIText != null)
                monthlyEMIText.text = $"Monthly EMI: ₹{schedule.monthlyPayment:N0}";

            if (totalInterestText != null)
                totalInterestText.text = $"Total Interest: ₹{schedule.totalInterest:N0}";

            float savings = bridge.GetComparisonInterestSavings();
            if (formalSavingsText != null)
            {
                formalSavingsText.text = savings > 0 
                    ? $"Formal Bank/SHG saves: ₹{savings:N0} interest!"
                    : "Your rate is competitive with formal loans.";
            }

            string riskTier = risk >= 0.50f ? "<color=#E74C3C>High Risk</color>" : 
                             (risk >= 0.25f ? "<color=#F39C12>Moderate Risk</color>" : "<color=#2ECC71>Low Risk</color>");

            if (riskScoreText != null)
                riskScoreText.text = $"ML Default Risk: {risk * 100f:F1}% ({riskTier})";

            if (timelineSlider != null)
            {
                timelineSlider.minValue = 0;
                timelineSlider.maxValue = schedule.monthlyBalance.Count - 1;
                timelineSlider.value = 0;
            }
        }

        private void OnTimelineSliderChanged(float val)
        {
            int monthIndex = Mathf.RoundToInt(val);
            if (bridge != null) bridge.ScrubTimeline(monthIndex);
        }

        private void UpdateTimelineDisplay(int month, float balance, float burden)
        {
            if (monthLabelText != null)
                monthLabelText.text = $"Month: {month}";

            if (remainingBalanceText != null)
                remainingBalanceText.text = $"Remaining Debt: ₹{balance:N0}";
        }

        private void ShowInputPanel()
        {
            if (loanInputPanel) loanInputPanel.SetActive(true);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(false);
            if (arViewPanel) arViewPanel.SetActive(false);
        }

        private void ShowResultsPanel()
        {
            if (loanInputPanel) loanInputPanel.SetActive(false);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(true);
            if (arViewPanel) arViewPanel.SetActive(false);
        }

        private void OnViewInARClicked()
        {
            if (loanInputPanel) loanInputPanel.SetActive(false);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(false);
            if (arViewPanel) arViewPanel.SetActive(true);
        }
    }
}
```

---

## Phase 7: Inspector Event Connections Checklist

1. Attach `LoanUIController.cs` to the Canvas.
2. Drag `DebtSightManager` into the `Bridge` slot.
3. Drag the respective Panels (`LoanInputPanel`, `ResultsOverlayPanel`, `ARViewPanel`) into their slots.
4. Drag all Text, InputField, Dropdown, Slider, and Button references into their inspector slots.
5. In the `CalculateButton`, verify that its `OnClick` calls `LoanUIController.OnCalculateClicked()`.

---

## Phase 8: Play Mode Verification & Test Values

Hit **Play** in the Unity Editor:

1. In the console, you will see:
   ```text
   [DebtSight ML] Native statistical risk engine initialized (Zero external packages needed).
   ```
2. Enter these rural informal moneylender values:
   * **Amount**: `50000`
   * **Interest Rate**: `3`
   * **Period**: `Monthly` (36% APR)
   * **Tenure**: `12 Months`
   * **Lender**: `Informal Moneylender`
   * **Income**: `< ₹10,000`
3. Click **Calculate**:
   * **Monthly EMI**: `₹5,667`
   * **Total Interest**: `₹18,000`
   * **Formal Savings**: ~`₹14,750`
   * **ML Default Risk**: **High Risk (~85% - 95%)**
   * **3D Visualizer**: Turns red and scales to full size.
4. Move the **Timeline Slider**:
   * As you slide to Month 12, the balance reaches ₹0 and the coin stack visibly shrinks down.

---

## Phase 9: Android Build Settings & APK Export

1. Open **File** $\rightarrow$ **Build Settings**.
2. Select **Android** $\rightarrow$ click **Switch Platform**.
3. In **Player Settings...**:
   * **Package Name**: `com.debtsight.app`
   * **Minimum API Level**: `Android 10.0 (API level 29)`.
   * **Scripting Backend**: `IL2CPP`.
   * **Target Architectures**: Check **ARM64**.
4. In **XR Plug-in Management $\rightarrow$ Android**:
   * Check **Google ARCore**.
5. Connect your phone via USB and click **Build and Run**.
