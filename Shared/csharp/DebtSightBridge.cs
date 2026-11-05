using System;
using System.Collections.Generic;
using UnityEngine;

namespace DebtSight
{
    /// <summary>
    /// Central Bridge connecting UI inputs, Loan Mathematics, Risk Assessment, and 3D AR Visuals.
    /// Can be attached to a GameManager or AR Session GameObject in Unity.
    /// </summary>
    public class DebtSightBridge : MonoBehaviour
    {
        [Header("Target Visualizer")]
        [Tooltip("Reference to the 3D visualizer object (Rice sack / coin stack)")]
        public GameObject visualizerObject;

        private IDebtVisualizer _visualizer;

        [Header("Current Simulation State")]
        public LoanInput currentInput = new LoanInput();
        public int lenderType = 2; // 0=Bank, 1=SHG, 2=Informal Moneylender
        public int incomeBracket = 1; // 0=<10k, 1=10k-25k, 2=25k-50k, 3=>50k

        [Header("Calculated Outputs")]
        public LoanScheduleResult currentSchedule;
        public float currentRisk = 0.4f;
        public List<float> monthlyBurdenIndices = new List<float>();

        // Events for Rachan's UI to listen to
        public event Action<LoanScheduleResult, float> OnCalculationCompleted;
        public event Action<int, float, float> OnTimelineMonthChanged; // (month, balance, burden)

        private void Awake()
        {
            ResolveVisualizer();
        }

        private void Start()
        {
            // Initial default calculation
            Recalculate();
        }

        public void ResolveVisualizer()
        {
            if (visualizerObject != null)
            {
                _visualizer = visualizerObject.GetComponent<IDebtVisualizer>();
            }
        }

        /// <summary>
        /// Recalculates loan schedule, risk probability, and monthly burden indices.
        /// Call this whenever the user edits an input field or clicks 'Calculate'.
        /// </summary>
        public void Recalculate()
        {
            if (_visualizer == null && visualizerObject != null)
            {
                ResolveVisualizer();
            }

            // 1. Calculate financial amortization schedule using pure C# engine
            currentSchedule = DebtSightMathEngine.Calculate(currentInput);

            // 2. Compute risk probability (calibrated baseline until ONNX ML model is linked)
            currentRisk = EstimateDefaultRisk(currentInput, lenderType, incomeBracket);

            // 3. Compute monthly burden indices: burden(t) = 0.6 * normalized_debt(t) + 0.4 * risk
            monthlyBurdenIndices.Clear();
            float p = currentInput.principal;

            for (int i = 0; i < currentSchedule.monthlyBalance.Count; i++)
            {
                float balance = currentSchedule.monthlyBalance[i];
                float normalizedDebt = Mathf.Clamp01(balance / p);
                float burden = Mathf.Clamp01((0.6f * normalizedDebt) + (0.4f * currentRisk));
                monthlyBurdenIndices.Add((float)Math.Round(burden, 3));
            }

            // 4. Update visualizer with initial month 1 burden and risk
            if (_visualizer != null && monthlyBurdenIndices.Count > 0)
            {
                _visualizer.SetBurden(monthlyBurdenIndices[0]);
                _visualizer.SetRisk(currentRisk);
            }

            OnCalculationCompleted?.Invoke(currentSchedule, currentRisk);
        }

        /// <summary>
        /// Call this when the user drags the timeline slider to monthIndex (0 to N-1).
        /// </summary>
        public void ScrubTimeline(int monthIndex)
        {
            if (monthlyBurdenIndices == null || monthlyBurdenIndices.Count == 0)
                return;

            int clampedMonth = Mathf.Clamp(monthIndex, 0, monthlyBurdenIndices.Count - 1);
            float burden = monthlyBurdenIndices[clampedMonth];
            float balance = currentSchedule.monthlyBalance[clampedMonth];

            if (_visualizer != null)
            {
                _visualizer.SetBurden(burden);
                _visualizer.SetRisk(currentRisk);
            }

            OnTimelineMonthChanged?.Invoke(clampedMonth + 1, balance, burden);
        }

        /// <summary>
        /// Computes savings compared to a formal SHG/Bank loan (typically 12% APR).
        /// </summary>
        public float GetComparisonInterestSavings()
        {
            var formalInput = new LoanInput
            {
                principal = currentInput.principal,
                interestRate = 12f,
                ratePeriod = RatePeriod.Annual,
                tenureMonths = currentInput.tenureMonths,
                interestMethod = InterestMethod.ReducingBalance
            };

            var formalResult = DebtSightMathEngine.Calculate(formalInput);
            float savings = currentSchedule.totalInterest - formalResult.totalInterest;
            return Mathf.Max(0f, savings);
        }

        /// <summary>
        /// Baseline risk estimation reflecting financial strain.
        /// Will be replaced seamlessly by the trained ONNX model in Phase 4.
        /// </summary>
        private float EstimateDefaultRisk(LoanInput input, int lender, int incomeTier)
        {
            float apr = DebtSightMathEngine.ToAnnualPercentageRate(input.interestRate, input.ratePeriod);
            float monthlyPayment = currentSchedule != null ? currentSchedule.monthlyPayment : (input.principal / input.tenureMonths);

            // Estimated monthly income proxy based on bracket
            float estimatedMonthlyIncome;
            switch (incomeTier)
            {
                case 0: estimatedMonthlyIncome = 8000f; break;   // < 10k
                case 1: estimatedMonthlyIncome = 18000f; break;  // 10k - 25k
                case 2: estimatedMonthlyIncome = 35000f; break;  // 25k - 50k
                default: estimatedMonthlyIncome = 65000f; break; // > 50k
            }

            // Debt-to-Income burden ratio
            float dti = monthlyPayment / estimatedMonthlyIncome;

            float score = 0.2f; // Base risk

            // APR impact
            if (apr > 36f) score += 0.35f;
            else if (apr > 24f) score += 0.20f;
            else if (apr > 14f) score += 0.08f;

            // Lender type impact (Informal moneylenders have severe collection stress)
            if (lender == 2) score += 0.25f; // Moneylender
            else if (lender == 1) score -= 0.05f; // SHG

            // Income / DTI strain
            if (dti > 0.5f) score += 0.30f;
            else if (dti > 0.3f) score += 0.15f;

            return Mathf.Clamp(score, 0.05f, 0.98f);
        }
    }
}
