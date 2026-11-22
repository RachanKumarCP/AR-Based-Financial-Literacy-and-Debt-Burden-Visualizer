using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace DebtSight
{
    /// <summary>
    /// Master UI Controller for DebtSight.
    /// Manages panel transitions, reading user loan parameters, triggering math recalculations,
    /// and routing the timeline slider to DebtSightBridge.
    /// </summary>
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

        [Header("Buttons")]
        [SerializeField] private Button calculateButton;
        [SerializeField] private Button viewInARButton;
        [SerializeField] private Button backToInputButton;
        [SerializeField] private Button closeARButton;

        [Header("Results Display")]
        [SerializeField] private TextMeshProUGUI monthlyEMIText;
        [SerializeField] private TextMeshProUGUI totalInterestText;
        [SerializeField] private TextMeshProUGUI formalSavingsText;
        [SerializeField] private TextMeshProUGUI riskScoreText;

        [Header("Timeline Controls")]
        [SerializeField] private Slider timelineSlider;
        [SerializeField] private TextMeshProUGUI monthLabelText;
        [SerializeField] private TextMeshProUGUI remainingBalanceText;

        private void Awake()
        {
            // Auto-detect bridge if unassigned
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

            // Set friendly defaults if fields are present
            if (amountInput != null && string.IsNullOrEmpty(amountInput.text)) amountInput.text = "50000";
            if (interestRateInput != null && string.IsNullOrEmpty(interestRateInput.text)) interestRateInput.text = "3";
            if (ratePeriodDropdown != null) ratePeriodDropdown.value = 0; // Monthly
            if (tenureSlider != null) tenureSlider.value = 12;

            UpdateTenureLabel(tenureSlider != null ? tenureSlider.value : 12);

            // Hook Button Listeners
            if (calculateButton != null) calculateButton.onClick.AddListener(OnCalculateClicked);
            if (viewInARButton != null) viewInARButton.onClick.AddListener(OnViewInARClicked);
            if (backToInputButton != null) backToInputButton.onClick.AddListener(ShowInputPanel);
            if (closeARButton != null) closeARButton.onClick.AddListener(ShowResultsPanel);

            if (tenureSlider != null) tenureSlider.onValueChanged.AddListener(UpdateTenureLabel);
            if (timelineSlider != null) timelineSlider.onValueChanged.AddListener(OnTimelineSliderChanged);

            // Hook Bridge Events
            if (bridge != null)
            {
                bridge.OnCalculationCompleted += DisplayResults;
                bridge.OnTimelineMonthChanged += UpdateTimelineDisplay;
            }

            // Start on input panel if configured
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

            float principal = (amountInput != null && float.TryParse(amountInput.text, out float p)) ? p : 50000f;
            float rate = (interestRateInput != null && float.TryParse(interestRateInput.text, out float r)) ? r : 3f;
            RatePeriod period = (ratePeriodDropdown != null && ratePeriodDropdown.value == 1) ? RatePeriod.Annual : RatePeriod.Monthly;
            int tenure = tenureSlider != null ? Mathf.RoundToInt(tenureSlider.value) : 12;
            int lender = lenderDropdown != null ? lenderDropdown.value : 2; // Default Informal Moneylender
            int income = incomeDropdown != null ? incomeDropdown.value : 0; // Default <10k

            bridge.currentInput.principal = principal;
            bridge.currentInput.interestRate = rate;
            bridge.currentInput.ratePeriod = period;
            bridge.currentInput.tenureMonths = tenure;
            bridge.currentInput.interestMethod = (lender == 2) 
                ? InterestMethod.FlatRate 
                : InterestMethod.ReducingBalance;

            bridge.lenderType = lender;
            bridge.incomeBracket = income;

            bridge.Recalculate();

            ShowResultsPanel();
        }

        public void DisplayResults(LoanScheduleResult schedule, float risk)
        {
            if (monthlyEMIText != null)
                monthlyEMIText.text = $"Monthly EMI : ₹{schedule.monthlyPayment:N0}";

            if (totalInterestText != null)
                totalInterestText.text = $"Total Interest : ₹{schedule.totalInterest:N0}";

            if (formalSavingsText != null)
            {
                float savings = bridge != null ? bridge.GetComparisonInterestSavings() : 0f;
                formalSavingsText.text = savings > 0 
                    ? $"You save ₹{savings:N0} with a Bank / SHG loan!"
                    : "Your rate is competitive with formal loans.";
            }

            if (riskScoreText != null)
            {
                string riskTier = risk >= 0.50f ? "<color=#E74C3C>High Risk</color>" : 
                                 (risk >= 0.25f ? "<color=#F39C12>Moderate Risk</color>" : "<color=#2ECC71>Low Risk</color>");
                riskScoreText.text = $"Default Risk : {risk * 100f:F1}% ({riskTier})";
            }

            // Configure Timeline Slider range
            if (timelineSlider != null && schedule.monthlyBalance != null)
            {
                timelineSlider.minValue = 0;
                timelineSlider.maxValue = schedule.monthlyBalance.Count - 1;
                timelineSlider.value = 0;
            }
        }

        public void OnTimelineSliderChanged(float val)
        {
            int monthIndex = Mathf.RoundToInt(val);
            if (bridge != null)
            {
                bridge.ScrubTimeline(monthIndex);
            }
        }

        public void UpdateTimelineDisplay(int month, float balance, float burden)
        {
            if (monthLabelText != null)
                monthLabelText.text = $"Month {month}";

            if (remainingBalanceText != null)
                remainingBalanceText.text = $"Remaining INR {balance:N0}";
        }

        public void ShowInputPanel()
        {
            if (loanInputPanel) loanInputPanel.SetActive(true);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(false);
            if (arViewPanel) arViewPanel.SetActive(false);
        }

        public void ShowResultsPanel()
        {
            if (loanInputPanel) loanInputPanel.SetActive(false);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(true);
            if (arViewPanel) arViewPanel.SetActive(false);
        }

        public void OnViewInARClicked()
        {
            // Transition directly into AR View Panel!
            if (loanInputPanel) loanInputPanel.SetActive(false);
            if (resultsOverlayPanel) resultsOverlayPanel.SetActive(false);
            if (arViewPanel) arViewPanel.SetActive(true);
        }
    }
}
