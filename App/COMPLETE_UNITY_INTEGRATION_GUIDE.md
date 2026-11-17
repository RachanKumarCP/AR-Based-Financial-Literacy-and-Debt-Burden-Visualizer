# 📱 DebtSight — Complete End-to-End Unity Integration & Completion Guide
**Target Environment:** Unity 6.6 | Android ARCore | Unity Sentis (ONNX Runtime)  
**Authors:** Revanth (ML & Math Engine), Rachan (Frontend UI), Rakesh (Unity AR)  

---

## 📑 Table of Contents
1. [Phase 1: Git Pull & File Placement](#phase-1-git-pull--file-placement)
2. [Phase 2: Unity Sentis & Project Settings](#phase-2-unity-sentis--project-settings)
3. [Phase 3: AR Scene Setup (XR Origin & Plane Detection)](#phase-3-ar-scene-setup)
4. [Phase 4: 3D Coin Visualizer Setup](#phase-4-3d-coin-visualizer-setup)
5. [Phase 5: Master Manager (`DebtSightBridge`) Setup](#phase-5-master-manager-debtsightbridge-setup)
6. [Phase 6: Complete UI Hierarchy & Screen Flow](#phase-6-complete-ui-hierarchy--screen-flow)
7. [Phase 7: Drop-in `LoanUIController.cs` Script](#phase-7-drop-in-loanuicontrollercs-script)
8. [Phase 8: Inspector Event Connections Checklist](#phase-8-inspector-event-connections-checklist)
9. [Phase 9: Play Mode Verification & Test Values](#phase-9-play-mode-verification--test-values)
10. [Phase 10: Android Build Settings & APK Export](#phase-10-android-build-settings--apk-export)

---

## Phase 1: Git Pull & File Placement

1. Open your terminal in the cloned repository folder and run:
   ```bash
   git pull origin main
   ```
2. Verify that **`Revanth/ML/models/debtsight_risk_model.onnx`** is present on your machine.
3. In your Unity project, organize your `Assets/` folder to match this structure:
   ```text
   Assets/
   ├── Models/
   │   ├── ML/
   │   │   └── debtsight_risk_model.onnx   <-- Drag ONNX model here
   │   └── 3D/
   │       └── CoinStack.fbx (or prefab)   <-- 3D coin stack / sack model
   ├── Materials/
   │   └── CoinMaterial.mat
   ├── Prefabs/
   │   ├── DebtVisualizer.prefab
   │   └── ARFeatheredPlane.prefab
   └── Scripts/
       └── DebtSight/
           ├── DebtSightBridge.cs          <-- From Shared/csharp/
           ├── DebtSightRiskPredictor.cs   <-- From Shared/csharp/
           ├── DebtSightMathEngine.cs      <-- From Shared/csharp/
           ├── DebtVisualizerReference.cs  <-- From Shared/csharp/
           ├── IDebtVisualizer.cs          <-- From Shared/csharp/
           └── LoanUIController.cs         <-- Provided in Phase 7 below
   ```

---

## Phase 2: Unity Sentis & Project Settings

1. **Install Sentis**:
   * In Unity, go to **Window** $\rightarrow$ **Package Manager**.
   * Click the **`+`** icon (top-left) $\rightarrow$ select **Add package by name...**.
   * Type: `com.unity.sentis` and click **Add**.
2. **Enable Scripting Define Symbol**:
   * Go to **Edit** $\rightarrow$ **Project Settings** $\rightarrow$ **Player**.
   * Select the **Android** tab $\rightarrow$ expand **Other Settings**.
   * Under **Scripting Define Symbols**, add: `SENTIS_INSTALLED` and click **Apply**.
   *(This unlocks native GPU compute tensor execution inside `DebtSightRiskPredictor.cs`)*.
3. **Verify the ONNX Asset**:
   * In Unity's Project view, click on `debtsight_risk_model.onnx`.
   * In the Inspector, you should see the Unity Sentis Model preview showing **`float_input [1, 10]`** and **`probabilities [1, 2]`**.

---

## Phase 3: AR Scene Setup

In your main Unity scene (e.g., `SampleScene` or `ARScene`):

1. **Remove Main Camera**: Delete the default `Main Camera` from the Hierarchy.
2. **Add XR Origin**:
   * Right-click Hierarchy $\rightarrow$ **XR** $\rightarrow$ **XR Origin (Mobile AR)**.
   * Verify that the child `Main Camera` has the **AR Camera**, **Tracked Pose Driver**, and **AR Camera Background** components attached.
3. **Add AR Session**:
   * Right-click Hierarchy $\rightarrow$ **XR** $\rightarrow$ **AR Session**.
4. **Add AR Managers**:
   * Select `XR Origin` in the Hierarchy.
   * In the Inspector, click **Add Component** $\rightarrow$ **AR Plane Manager**.
   * Click **Add Component** $\rightarrow$ **AR Raycast Manager**.
   * Under `AR Plane Manager`, set **Detection Mode** to **Horizontal**.

---

## Phase 4: 3D Coin Visualizer Setup

1. Drag your 3D Coin Stack model or prefab into the scene and name it **`DebtVisualizer`**.
2. Click **Add Component** $\rightarrow$ select **`DebtVisualizerReference`**.
3. In the `DebtVisualizerReference` Inspector:
   * **Target Renderer**: Drag the coin stack's `MeshRenderer` here.
   * **Min Scale**: `(0.1, 0.1, 0.1)` *(represents zero debt)*.
   * **Max Scale**: `(1.0, 1.0, 1.0)` *(represents full starting debt)*.
   * **Safe Color**: Green or Soft Yellow (`#2ECC71`).
   * **Danger Color**: Crimson Red (`#E74C3C`).
   * **Max Shake Intensity**: `0.02`.
4. Deactivate this object by default in the scene (or make it a prefab so the AR Raycast manager can instantiate it on plane tap).

---

## Phase 5: Master Manager (`DebtSightBridge`) Setup

1. In the Hierarchy, create an empty GameObject named **`DebtSightManager`**.
2. Add the **`DebtSightBridge`** component to it.
3. In the Inspector:
   * **Visualizer Object**: Drag your `DebtVisualizer` GameObject here.
   * **Risk Model Asset**: Drag `debtsight_risk_model.onnx` from `Assets/Models/ML/` here.

---

## Phase 6: Complete UI Hierarchy & Screen Flow

Create a **Canvas** set to **Screen Space - Overlay**:
* **Canvas Scaler**: `Scale With Screen Size`, Reference Resolution: `1080 × 1920` (Portrait), Match: `0.5`.

Structure your Canvas children like this:

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
    └── BackToResultsButton      (Button - "Close AR")
```

---

## Phase 7: Drop-in `LoanUIController.cs` Script

Create this script at `Assets/Scripts/DebtSight/LoanUIController.cs`. It connects all UI fields, handles panel switching, triggers calculations, and controls the timeline:

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
            // Initial default inputs
            if (amountInput != null) amountInput.text = "50000";
            if (interestRateInput != null) interestRateInput.text = "3";
            if (ratePeriodDropdown != null) ratePeriodDropdown.value = 0; // Monthly
            if (tenureSlider != null) tenureSlider.value = 12;
            if (lenderDropdown != null) lenderDropdown.value = 2;         // Informal Moneylender
            if (incomeDropdown != null) incomeDropdown.value = 1         // 10k-25k

            UpdateTenureLabel(12);

            // Hook UI Listeners
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

            // Read Inputs
            float principal = float.TryParse(amountInput.text, out float p) ? p : 50000f;
            float rate = float.TryParse(interestRateInput.text, out float r) ? r : 3f;
            RatePeriod period = ratePeriodDropdown.value == 0 ? RatePeriod.Monthly : RatePeriod.Annual;
            int tenure = Mathf.RoundToInt(tenureSlider.value);
            int lender = lenderDropdown.value;
            int income = incomeDropdown.value;

            // Pass to Bridge
            bridge.currentInput.principal = principal;
            bridge.currentInput.interestRate = rate;
            bridge.currentInput.ratePeriod = period;
            bridge.currentInput.tenureMonths = tenure;
            bridge.currentInput.interestMethod = (lender == 2) 
                ? InterestMethod.FlatRate 
                : InterestMethod.ReducingBalance;

            bridge.lenderType = lender;
            bridge.incomeBracket = income;

            // Trigger ML & Math Engine
            bridge.Recalculate();

            ShowResultsPanel();
        }

        private void DisplayResults(LoanScheduleResult schedule, float risk)
        {
            if (monthlyEMIText != null)
                monthlyEMIText.text = $"Monthly Payment: ₹{schedule.monthlyPayment:N0}";

            if (totalInterestText != null)
                totalInterestText.text = $"Total Interest: ₹{schedule.totalInterest:N0}";

            float savings = bridge.GetComparisonInterestSavings();
            if (formalSavingsText != null)
            {
                formalSavingsText.text = savings > 0 
                    ? $"Formal Bank/SHG would save: ₹{savings:N0} in interest!"
                    : "Your rate is competitive with formal loans.";
            }

            string riskTier = risk >= 0.50f ? "<color=#E74C3C>High Risk</color>" : 
                             (risk >= 0.25f ? "<color=#F39C12>Moderate Risk</color>" : "<color=#2ECC71>Low Risk</color>");

            if (riskScoreText != null)
                riskScoreText.text = $"ML Default Risk: {risk * 100f:F1}% ({riskTier})";

            // Configure Timeline Slider range
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

## Phase 8: Inspector Event Connections Checklist

1. Attach `LoanUIController.cs` to an empty GameObject named **`LoanUIController`** (or to the Canvas).
2. Drag **`DebtSightManager`** into the `Bridge` slot.
3. Drag the respective Panels (`LoanInputPanel`, `ResultsOverlayPanel`, `ARViewPanel`) into their slots.
4. Drag all Text, InputField, Dropdown, Slider, and Button references into the inspector slots.
5. In the `CalculateButton`, verify that its `OnClick` calls `LoanUIController.OnCalculateClicked()`.

---

## Phase 9: Play Mode Verification & Test Values

Hit **Play** in Unity Editor and run this test case:

| Field | Enter This Value | Expected Output |
| :--- | :--- | :--- |
| **Principal** | `50000` | — |
| **Rate** | `3` | — |
| **Rate Period** | `Monthly` (36% APR) | — |
| **Tenure** | `12 Months` | — |
| **Lender** | `Informal Moneylender` | Uses Flat Rate formula |
| **Income** | `< ₹10,000` | High financial strain |

### Expected Results:
* **Monthly EMI**: `₹5,667`
* **Total Interest**: `₹18,000` (Total repayment: ₹68,000)
* **Formal Savings**: ~`₹14,750` interest saved if borrowing from Bank/SHG at 12% APR!
* **ML Default Risk**: **High Risk (~70% - 85%)**
* **3D Visualizer**: The coin stack scales to full size and turns red.
* **Timeline Scrubbing**: Dragging the slider to Month 12 reduces the balance to ₹0 and visibly shrinks the 3D coin stack.

---

## Phase 10: Android Build Settings & APK Export

1. Open **File** $\rightarrow$ **Build Settings**.
2. Select **Android** $\rightarrow$ click **Switch Platform**.
3. Click **Player Settings...**:
   * **Company Name**: `DebtSight`
   * **Product Name**: `DebtSight`
   * **Identification $\rightarrow$ Package Name**: `com.debtsight.app`
   * **Minimum API Level**: `Android 10.0 (API level 29)` or higher.
   * **Target API Level**: `Automatic (highest installed)`.
   * **Configuration $\rightarrow$ Scripting Backend**: `IL2CPP`.
   * **Target Architectures**: Check **ARM64**.
4. In **Project Settings $\rightarrow$ XR Plug-in Management**:
   * Select the **Android** tab.
   * Check **Google ARCore**.
5. Connect your Android phone via USB (with USB Debugging enabled).
6. Return to **Build Settings** $\rightarrow$ click **Build and Run**.
