# DebtSight — Unity C# Integration Scripts

This directory contains production-ready, pure C# scripts designed for **Rachan** (Frontend UI) and **Rakesh** (Unity AR), coordinated by **Parthiv** and implemented by **Revanth**.

All scripts are written in standard C# (.NET Standard 2.0 / 2.1) with zero third-party dependencies, compatible with **Unity 2021, 2022, 2023, and Unity 6**.

---

## 1. Files in this Directory

| File | Primary Owner | Description |
| :--- | :---: | :--- |
| [`DebtSightMathEngine.cs`](DebtSightMathEngine.cs) | **Rachan** | Pure C# loan engine calculating Reducing Balance (EMI), Flat Rate, and Simple Interest schedules. |
| [`IDebtVisualizer.cs`](IDebtVisualizer.cs) | **Rakesh** | Shared interface defining `SetBurden(float)` and `SetRisk(float)`. |
| [`DebtVisualizerReference.cs`](DebtVisualizerReference.cs) | **Rakesh** | Reference MonoBehaviour to attach to the 3D Rice Sack or Coin Stack (handles scaling, tinting, and shaking). |
| [`DebtSightBridge.cs`](DebtSightBridge.cs) | **Rachan / Parthiv** | Master coordinator that takes UI inputs, calculates schedules, computes burden indices, and drives the visualizer. |

---

## 2. Quick Setup in Unity (For Rachan & Rakesh)

1. Open your Unity Project (inside `App/` or your Unity root).
2. Create a folder: `Assets/Scripts/DebtSight/`.
3. Copy all 4 `.cs` files from `Shared/csharp/` into that folder.
4. Unity will compile them automatically in ~2 seconds with zero errors!

---

## 3. How Rachan Uses the Math Engine & Bridge in UI

### Option A: Using `DebtSightBridge` (Recommended)
1. Add an empty GameObject in your scene named `DebtSightManager` and attach `DebtSightBridge.cs`.
2. When the user taps the **"Calculate"** or **"See My Debt"** button:
```csharp
using DebtSight;
using UnityEngine;
using UnityEngine.UI;

public class LoanUIController : MonoBehaviour
{
    public DebtSightBridge bridge;
    public InputField amountInput;
    public InputField rateInput;
    public Slider tenureSlider;
    public Dropdown methodDropdown;

    public void OnCalculateClicked()
    {
        bridge.currentInput.principal = float.Parse(amountInput.text);
        bridge.currentInput.interestRate = float.Parse(rateInput.text);
        bridge.currentInput.tenureMonths = (int)tenureSlider.value;
        bridge.currentInput.interestMethod = (InterestMethod)methodDropdown.value;

        // Recalculate everything
        bridge.Recalculate();

        // Access results
        Debug.Log($"Monthly EMI: ₹{bridge.currentSchedule.monthlyPayment:N2}");
        Debug.Log($"Total Interest: ₹{bridge.currentSchedule.totalInterest:N2}");
        Debug.Log($"Risk: {bridge.currentRisk * 100f:F1}%");
    }

    public void OnTimelineSliderChanged(float monthVal)
    {
        // When user scrubs month 1..N
        bridge.ScrubTimeline((int)monthVal - 1);
    }
}
```

---

## 4. How Rakesh Uses `IDebtVisualizer` on the 3D Object

1. Select your 3D prefab (e.g. Rice Sack, Grain Bag, or Coin Stack) placed on the detected AR plane.
2. Attach [`DebtVisualizerReference.cs`](DebtVisualizerReference.cs).
3. Drag the Mesh Renderer into the `Target Renderer` slot in the Inspector.
4. Drag that 3D object into the `Visualizer Object` field on `DebtSightBridge`.
5. Now:
   - When burden increases, the sack grows larger.
   - When risk increases, the sack darkens and begins to visibly shake/vibrate.

---

## 5. Verification Test Parity

The calculations in `DebtSightMathEngine.cs` have been mathematically aligned with Revanth's Python unit tests in `Testing/unit/test_loan_math.py`:
- ₹100,000 at 12% APR (Reducing EMI) = ₹8,884.88 / month.
- ₹50,000 at 3% / month flat (Moneylender) = ₹18,000 total interest, ₹5,666.67 / month.
- ₹40,000 at 2% / month (Bullet harvest) = ₹800 / month interest, ₹40,800 final month.
