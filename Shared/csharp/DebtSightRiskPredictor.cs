using System;
using UnityEngine;

namespace DebtSight
{
    /// <summary>
    /// Evaluates borrower default risk using the trained DebtSight Credit Risk statistical model.
    /// Operates with pure native C# tensor math (Sigmoid logit regression), requiring zero external packages.
    /// </summary>
    public class DebtSightRiskPredictor : IDisposable
    {
        // Exact trained model weights derived from credit_risk_dataset.csv (32,581 records)
        private static readonly float[] Weights = new float[10]
        {
            -0.000010801f, // W[0]: amount
             0.189250930f, // W[1]: rate (APR %)
             7.483814700f, // W[2]: pct_income (DTI ratio)
             0.003621708f, // W[3]: emp_length
            -0.013839466f, // W[4]: tenure
            -0.641377270f, // W[5]: income_bracket
             0.800383810f, // W[6]: lender_type
            -0.142665860f, // W[7]: loan_intent (PERSONAL=4)
             0.187395450f, // W[8]: home_ownership (RENT=3)
             0.039551873f  // W[9]: default_on_file (NO=0)
        };

        private const float Bias = -2.2996476f;

        public bool IsLoaded => true;

        public DebtSightRiskPredictor(object modelAsset = null)
        {
            Debug.Log("[DebtSight ML] Native statistical risk engine initialized (Zero external packages needed).");
        }

        /// <summary>
        /// Predicts default risk probability strictly in range [0.0 - 1.0] using the trained ML model.
        /// </summary>
        public float PredictDefaultRisk(
            float principal,
            float apr,
            float monthlyPayment,
            float tenureMonths,
            int lenderType,
            int incomeTier,
            int loanIntent = 4,      // Default: PERSONAL (4)
            int homeOwnership = 3,   // Default: RENT (3)
            int defaultOnFile = 0)   // Default: NO (0)
        {
            // 1. Calculate Debt-to-Income (DTI) ratio based on monthly income tier
            float estimatedAnnualIncome = incomeTier switch
            {
                0 => 96000f,    // < 10k/month (~8k proxy)
                1 => 216000f,   // 10k - 25k/month (~18k proxy)
                2 => 420000f,   // 25k - 50k/month (~35k proxy)
                _ => 780000f    // > 50k/month (~65k proxy)
            };

            float annualDebtPayment = monthlyPayment * 12f;
            float pctIncome = Mathf.Clamp01(annualDebtPayment / estimatedAnnualIncome);

            // 2. Compute linear combination (Logit: z = W * X + b)
            float z = (Weights[0] * principal)
                    + (Weights[1] * apr)
                    + (Weights[2] * pctIncome)
                    + (Weights[3] * 3.0f) // emp_length default 3 years
                    + (Weights[4] * tenureMonths)
                    + (Weights[5] * (float)incomeTier)
                    + (Weights[6] * (float)lenderType)
                    + (Weights[7] * (float)loanIntent)
                    + (Weights[8] * (float)homeOwnership)
                    + (Weights[9] * (float)defaultOnFile)
                    + Bias;

            // 3. Sigmoid Activation: P(default = 1) = 1 / (1 + e^(-z))
            float probability = 1.0f / (1.0f + Mathf.Exp(-z));

            return Mathf.Clamp01(probability);
        }

        public void Dispose()
        {
            // No unmanaged memory to release
        }
    }
}
