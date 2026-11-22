using UnityEngine;
using TMPro;
using UnityEngine.UI;
using DebtSight;
using System.Globalization;

public class LoanUIController : MonoBehaviour
{
    [Header("DebtSight Connection")]
    public DebtSightBridge bridge;

    [Header("Input Controls")]
    public TMP_InputField amountInput;
    public TMP_InputField rateInput;
    public TMP_Dropdown periodDropdown;
    public Slider tenureSlider;
    public TextMeshProUGUI tenureValueText;

    [Header("Lender Toggles")]
    public Toggle bankMUDRAToggle;
    public Toggle shgToggle;
    public Toggle informalToggle;

    [Header("Income Toggles")]
    public Toggle incomeBelow10k;
    public Toggle income10kTo25k;
    public Toggle income25kTo50k;
    public Toggle incomeAbove50k;

    [Header("Output Displays")]
    public TextMeshProUGUI emiText;
    public TextMeshProUGUI interestText;
    public TextMeshProUGUI savingsText;
    public Slider timelineSlider;
    public TextMeshProUGUI timelineMonthText;

    [Header("Screen Panels")]
    public GameObject loanInputPanel;
    public GameObject resultsOverlayPanel;
    public GameObject arViewPanel;

    // --------------------------------------------------
    // INITIALIZATION & SCREEN SETUP
    // --------------------------------------------------

    private void Awake()
    {
        // Auto-detect bridge in scene if not dragged into inspector
        if (bridge == null)
        {
            bridge = FindFirstObjectByType<DebtSightBridge>();
            if (bridge == null)
            {
                #pragma warning disable CS0618
                bridge = FindObjectOfType<DebtSightBridge>();
                #pragma warning restore CS0618
            }
        }
    }

    private void Start()
    {
        ShowLoanInputScreen();

        if (tenureSlider != null)
        {
            UpdateTenureLabel(tenureSlider.value);
            tenureSlider.onValueChanged.AddListener(UpdateTenureLabel);
        }

        if (timelineSlider != null)
        {
            timelineSlider.onValueChanged.AddListener(OnTimelineSliderChanged);
        }
    }

    private void OnDestroy()
    {
        if (tenureSlider != null)
            tenureSlider.onValueChanged.RemoveListener(UpdateTenureLabel);

        if (timelineSlider != null)
            timelineSlider.onValueChanged.RemoveListener(OnTimelineSliderChanged);
    }

    // --------------------------------------------------
    // TENURE SLIDER
    // --------------------------------------------------

    public void UpdateTenureLabel(float value)
    {
        if (tenureValueText == null)
            return;

        int months = Mathf.RoundToInt(value);
        tenureValueText.text = months + " Months";
    }

    // --------------------------------------------------
    // CALCULATE LOAN
    // --------------------------------------------------

    public void OnCalculateClicked()
    {
        if (bridge == null)
        {
            Debug.LogError("[DebtSight] DebtSightBridge is not assigned!");
            return;
        }

        if (amountInput == null || rateInput == null ||
            periodDropdown == null || tenureSlider == null)
        {
            Debug.LogError("[DebtSight] One or more loan input references are missing in Inspector!");
            return;
        }

        // 1. Read amount and interest rate safely
        float principal;
        float rate;

        if (!float.TryParse(amountInput.text, NumberStyles.Float, CultureInfo.CurrentCulture, out principal) &&
            !float.TryParse(amountInput.text, NumberStyles.Float, CultureInfo.InvariantCulture, out principal))
        {
            Debug.LogError("[DebtSight] Please enter a valid loan amount.");
            return;
        }

        if (!float.TryParse(rateInput.text, NumberStyles.Float, CultureInfo.CurrentCulture, out rate) &&
            !float.TryParse(rateInput.text, NumberStyles.Float, CultureInfo.InvariantCulture, out rate))
        {
            Debug.LogError("[DebtSight] Please enter a valid interest rate.");
            return;
        }

        if (principal <= 0f || rate < 0f)
        {
            Debug.LogError("[DebtSight] Loan amount must be positive and interest rate cannot be negative.");
            return;
        }

        int tenureMonths = Mathf.RoundToInt(tenureSlider.value);
        if (tenureMonths < 1)
        {
            Debug.LogError("[DebtSight] Loan tenure must be at least one month.");
            return;
        }

        // ----------------------------------------------
        // 2. PASS INPUTS TO DEBTSIGHT BRIDGE
        // ----------------------------------------------

        bridge.currentInput.principal = principal;
        bridge.currentInput.interestRate = rate;
        bridge.currentInput.tenureMonths = tenureMonths;

        // Period Dropdown: 0 = Monthly, 1 = Annual
        if (periodDropdown.value == 0)
        {
            bridge.currentInput.ratePeriod = RatePeriod.Monthly;
        }
        else
        {
            bridge.currentInput.ratePeriod = RatePeriod.Annual;
        }

        // ----------------------------------------------
        // 3. READ LENDER SELECTION & SET FORMULA
        // ----------------------------------------------

        if (bankMUDRAToggle != null && bankMUDRAToggle.isOn)
        {
            bridge.lenderType = 0;
            bridge.currentInput.interestMethod = InterestMethod.ReducingBalance;
        }
        else if (shgToggle != null && shgToggle.isOn)
        {
            bridge.lenderType = 1;
            bridge.currentInput.interestMethod = InterestMethod.ReducingBalance;
        }
        else if (informalToggle != null && informalToggle.isOn)
        {
            bridge.lenderType = 2;
            bridge.currentInput.interestMethod = InterestMethod.FlatRate; // Moneylender Flat Rate Trap
        }
        else
        {
            // Default to Informal Moneylender if toggles are unassigned
            bridge.lenderType = 2;
            bridge.currentInput.interestMethod = InterestMethod.FlatRate;
        }

        // ----------------------------------------------
        // 4. READ INCOME SELECTION
        // ----------------------------------------------

        if (incomeBelow10k != null && incomeBelow10k.isOn)
        {
            bridge.incomeBracket = 0;
        }
        else if (income10kTo25k != null && income10kTo25k.isOn)
        {
            bridge.incomeBracket = 1;
        }
        else if (income25kTo50k != null && income25kTo50k.isOn)
        {
            bridge.incomeBracket = 2;
        }
        else if (incomeAbove50k != null && incomeAbove50k.isOn)
        {
            bridge.incomeBracket = 3;
        }
        else
        {
            bridge.incomeBracket = 1; // Default middle bracket
        }

        // ----------------------------------------------
        // 5. RUN LOAN & RISK CALCULATION
        // ----------------------------------------------

        try
        {
            bridge.Recalculate();
        }
        catch (System.Exception ex)
        {
            Debug.LogError("[DebtSight] Loan calculation failed: " + ex.Message);
            return;
        }

        if (bridge.currentSchedule == null ||
            bridge.currentSchedule.monthlyBalance == null ||
            bridge.currentSchedule.monthlyBalance.Count == 0)
        {
            Debug.LogError("[DebtSight] Loan schedule could not be generated.");
            return;
        }

        // ----------------------------------------------
        // 6. DISPLAY RESULTS ON SCREEN
        // ----------------------------------------------

        if (emiText != null)
        {
            emiText.text = "Monthly EMI: INR " + bridge.currentSchedule.monthlyPayment.ToString("N2");
        }

        if (interestText != null)
        {
            interestText.text = "Total Interest: INR " + bridge.currentSchedule.totalInterest.ToString("N2");
        }

        float savings = bridge.GetComparisonInterestSavings();
        if (savingsText != null)
        {
            savingsText.text = savings > 0f
                ? "Switching to a Bank / SHG loan saves INR " + savings.ToString("N0") + "!"
                : "Great rate! Your current loan is competitive.";
        }

        // ----------------------------------------------
        // 7. CONFIGURE REPAYMENT TIMELINE SLIDER
        // ----------------------------------------------

        int totalMonths = bridge.currentSchedule.monthlyBalance.Count;

        if (timelineSlider != null)
        {
            timelineSlider.minValue = 1;
            timelineSlider.maxValue = totalMonths;
            timelineSlider.wholeNumbers = true;
            timelineSlider.SetValueWithoutNotify(1);
        }

        // Force initial update to month 1
        OnTimelineSliderChanged(1f);

        // ----------------------------------------------
        // 8. SWITCH TO RESULTS OVERLAY PANEL
        // ----------------------------------------------

        ShowResultsScreen();

        Debug.Log("[DebtSight] Loan calculation and ML risk assessment completed successfully!");
    }

    // --------------------------------------------------
    // TIMELINE SLIDER (UPDATES 3D COIN BURDEN & RISK)
    // --------------------------------------------------

    public void OnTimelineSliderChanged(float monthValue)
    {
        if (bridge == null ||
            bridge.currentSchedule == null ||
            bridge.currentSchedule.monthlyBalance == null ||
            bridge.currentSchedule.monthlyBalance.Count == 0)
        {
            return;
        }

        int monthIndex = Mathf.Clamp(
            Mathf.RoundToInt(monthValue) - 1,
            0,
            bridge.currentSchedule.monthlyBalance.Count - 1
        );

        // Update 3D burden scale and color through the bridge
        bridge.ScrubTimeline(monthIndex);

        float remainingBalance = bridge.currentSchedule.monthlyBalance[monthIndex];

        if (timelineMonthText != null)
        {
            timelineMonthText.text = "Month " + (monthIndex + 1) + ": Remaining INR " + remainingBalance.ToString("N0");
        }
    }

    // --------------------------------------------------
    // SCREEN NAVIGATION METHODS
    // --------------------------------------------------

    public void ShowLoanInputScreen()
    {
        if (loanInputPanel != null) loanInputPanel.SetActive(true);
        if (resultsOverlayPanel != null) resultsOverlayPanel.SetActive(false);
        if (arViewPanel != null) arViewPanel.SetActive(false);
    }

    public void ShowResultsScreen()
    {
        if (loanInputPanel != null) loanInputPanel.SetActive(false);
        if (resultsOverlayPanel != null) resultsOverlayPanel.SetActive(true);
        if (arViewPanel != null) arViewPanel.SetActive(false);
    }

    /// <summary>
    /// Connect this method to the OpenARButton / ViewInARButton OnClick event!
    /// </summary>
    public void OpenARView()
    {
        if (loanInputPanel != null) loanInputPanel.SetActive(false);
        if (resultsOverlayPanel != null) resultsOverlayPanel.SetActive(false);
        if (arViewPanel != null) arViewPanel.SetActive(true);

        Debug.Log("[DebtSight] AR View Panel opened successfully.");
    }

    public void BackToResults()
    {
        ShowResultsScreen();
    }

    public void BackToLoanInput()
    {
        ShowLoanInputScreen();
    }
}
