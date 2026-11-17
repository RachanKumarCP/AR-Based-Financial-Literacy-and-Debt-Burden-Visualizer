using System;
using UnityEngine;
#if SENTIS_INSTALLED
using Unity.Sentis;
#endif

namespace DebtSight
{
    /// <summary>
    /// Handles machine learning default risk prediction using Unity Sentis ONNX runtime.
    /// Includes a zero-dependency fallback heuristic if Sentis is not yet installed or the model asset is unassigned.
    /// </summary>
    public class DebtSightRiskPredictor : IDisposable
    {
#if SENTIS_INSTALLED
        private Model _runtimeModel;
        private IWorker _worker;
#endif
        private readonly bool _hasModel;

        public bool IsLoaded => _hasModel;

#if SENTIS_INSTALLED
        public DebtSightRiskPredictor(ModelAsset modelAsset, BackendType backend = BackendType.GPUCompute)
        {
            if (modelAsset == null)
            {
                Debug.LogWarning("[DebtSight ML] ModelAsset is null. Running with baseline heuristic fallback.");
                _hasModel = false;
                return;
            }

            try
            {
                _runtimeModel = ModelLoader.Load(modelAsset);
                _worker = WorkerFactory.CreateWorker(backend, _runtimeModel);
                _hasModel = true;
                Debug.Log($"[DebtSight ML] Sentis model loaded successfully on {backend}.");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[DebtSight ML] Failed to load Sentis model: {ex.Message}. Falling back to heuristic.");
                _hasModel = false;
            }
        }
#else
        public DebtSightRiskPredictor(object modelAsset = null)
        {
            _hasModel = false;
        }
#endif

        /// <summary>
        /// Predicts default risk probability [0.0 - 1.0].
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
            // 1. Calculate Debt-to-Income (DTI) ratio
            float estimatedAnnualIncome = incomeTier switch
            {
                0 => 96000f,    // < 10k/month (~8k proxy)
                1 => 216000f,   // 10k - 25k/month (~18k proxy)
                2 => 420000f,   // 25k - 50k/month (~35k proxy)
                _ => 780000f    // > 50k/month (~65k proxy)
            };

            float annualDebtPayment = monthlyPayment * 12f;
            float pctIncome = Mathf.Clamp01(annualDebtPayment / estimatedAnnualIncome);

#if SENTIS_INSTALLED
            if (_hasModel && _worker != null)
            {
                // Tensor input shape: [1, 10]
                float[] featureArray = new float[10]
                {
                    principal,
                    apr,
                    pctIncome,
                    3.0f,               // emp_length (default 3 years)
                    tenureMonths,
                    (float)incomeTier,
                    (float)lenderType,
                    (float)loanIntent,
                    (float)homeOwnership,
                    (float)defaultOnFile
                };

                using Tensor<float> inputTensor = new Tensor<float>(new TensorShape(1, 10), featureArray);
                _worker.Schedule(inputTensor);

                // Output probabilities shape: [1, 2] -> index 1 is default probability
                using Tensor<float> outputTensor = _worker.PeekOutput("probabilities") as Tensor<float>;
                if (outputTensor != null)
                {
                    return Mathf.Clamp01(outputTensor[0, 1]);
                }
            }
#endif

            // Fallback heuristic if Sentis is not active
            return FallbackHeuristicRisk(apr, lenderType, incomeTier, pctIncome);
        }

        private float FallbackHeuristicRisk(float apr, int lender, int incomeTier, float pctIncome)
        {
            float score = 0.20f;
            if (apr > 36f) score += 0.35f;
            else if (apr > 24f) score += 0.20f;
            else if (apr > 14f) score += 0.08f;

            if (lender == 2) score += 0.25f;      // Moneylender
            else if (lender == 1) score += 0.10f; // SHG

            if (incomeTier == 0) score += 0.15f;
            else if (incomeTier == 1) score += 0.08f;

            if (pctIncome > 0.40f) score += 0.20f;

            return Mathf.Clamp01(score);
        }

        public void Dispose()
        {
#if SENTIS_INSTALLED
            _worker?.Dispose();
            _worker = null;
#endif
        }
    }
}
