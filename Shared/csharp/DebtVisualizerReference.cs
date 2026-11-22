using UnityEngine;

namespace DebtSight
{
    /// <summary>
    /// Reference implementation of IDebtVisualizer for Unity AR.
    /// Controls 3D object size (burden) and dynamic danger color tinting (risk).
    /// </summary>
    public class DebtVisualizerReference : MonoBehaviour, IDebtVisualizer
    {
        [Header("Burden Scaling (Size)")]
        [Tooltip("Scale of 3D object when remaining debt is 0.0")]
        public Vector3 minScale = new Vector3(0.2f, 0.2f, 0.2f);

        [Tooltip("Scale of 3D object when debt is at full 1.0")]
        public Vector3 maxScale = new Vector3(1.5f, 1.5f, 1.5f);

        [Tooltip("Smoothing speed for size transitions")]
        public float scaleLerpSpeed = 8f;

        [Header("Risk Tinting (Color)")]
        [Tooltip("Object color tint under safe / low risk (0.0)")]
        public Color safeColor = new Color(0.95f, 0.85f, 0.40f); // Bright Gold

        [Tooltip("Object color tint under severe informal moneylender risk (1.0)")]
        public Color dangerColor = new Color(0.95f, 0.15f, 0.10f); // Bright Crimson Red

        public Renderer targetRenderer;

        [Header("Risk Shaking (Instability)")]
        public float maxShakeOffset = 0.04f;
        public float shakeFrequency = 25f;

        private float _targetBurden = 0.8f;
        private float _targetRisk = 0.8f;
        private Vector3 _basePosition;
        private Vector3 _initialScale;

        private void Awake()
        {
            _basePosition = transform.localPosition;
            _initialScale = transform.localScale;

            if (targetRenderer == null)
            {
                targetRenderer = GetComponentInChildren<Renderer>();
            }

            // If user didn't customize min/max scale, calibrate proportionally to the model's imported size
            if (minScale == Vector3.zero || minScale == new Vector3(0.3f, 0.3f, 0.3f))
            {
                minScale = _initialScale * 0.25f;
                maxScale = _initialScale * 1.30f;
            }
        }

        private void Update()
        {
            UpdateScale();
            UpdateTint();
            UpdateShake();
        }

        public void SetBurden(float burden)
        {
            _targetBurden = Mathf.Clamp01(burden);
        }

        public void SetRisk(float risk)
        {
            _targetRisk = Mathf.Clamp01(risk);
        }

        private void UpdateScale()
        {
            Vector3 desiredScale = Vector3.Lerp(minScale, maxScale, _targetBurden);
            transform.localScale = Vector3.Lerp(transform.localScale, desiredScale, Time.deltaTime * scaleLerpSpeed);
        }

        private void UpdateTint()
        {
            if (targetRenderer == null) return;

            Color currentColor = Color.Lerp(safeColor, dangerColor, _targetRisk);

            // Directly update materials to guarantee support for glTF, URP, and standard shaders
            foreach (Material mat in targetRenderer.materials)
            {
                if (mat == null) continue;

                if (mat.HasProperty("_BaseColor"))
                    mat.SetColor("_BaseColor", currentColor);

                if (mat.HasProperty("_Color"))
                    mat.SetColor("_Color", currentColor);

                if (mat.HasProperty("_BaseColorFactor"))
                    mat.SetColor("_BaseColorFactor", currentColor);

                mat.color = currentColor;
            }
        }

        private void UpdateShake()
        {
            if (_targetRisk < 0.25f)
            {
                transform.localPosition = _basePosition;
                return;
            }

            float intensity = Mathf.InverseLerp(0.25f, 1.0f, _targetRisk) * maxShakeOffset;
            float offsetX = (Mathf.PerlinNoise(Time.time * shakeFrequency, 0.0f) - 0.5f) * 2.0f * intensity;
            float offsetZ = (Mathf.PerlinNoise(0.0f, Time.time * shakeFrequency) - 0.5f) * 2.0f * intensity;

            transform.localPosition = _basePosition + new Vector3(offsetX, 0, offsetZ);
        }
    }
}
