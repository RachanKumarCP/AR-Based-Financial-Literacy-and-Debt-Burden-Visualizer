using UnityEngine;

namespace DebtSight
{
    /// <summary>
    /// Reference implementation of IDebtVisualizer for Unity AR.
    /// Attach this script to the 3D visual object (Rice Sack or Coin Stack).
    /// Owned and customizable by Rakesh.
    /// </summary>
    public class DebtVisualizerReference : MonoBehaviour, IDebtVisualizer
    {
        [Header("Burden Scaling (Size)")]
        [Tooltip("Scale of 3D object when burden is 0.0")]
        public Vector3 minScale = new Vector3(0.3f, 0.3f, 0.3f);

        [Tooltip("Scale of 3D object when burden is 1.0")]
        public Vector3 maxScale = new Vector3(1.5f, 1.5f, 1.5f);

        [Tooltip("Smoothing speed for size transitions")]
        public float scaleLerpSpeed = 5f;

        [Header("Risk Tinting (Darkness)")]
        [Tooltip("Object color tint under low risk (0.0)")]
        public Color safeColor = new Color(0.9f, 0.85f, 0.7f); // Natural burlap / golden

        [Tooltip("Object color tint under severe default risk (1.0)")]
        public Color dangerColor = new Color(0.2f, 0.05f, 0.05f); // Dark / charred / warning

        public Renderer targetRenderer;

        [Header("Risk Shaking (Instability)")]
        [Tooltip("Maximum shake offset distance in meters at risk = 1.0")]
        public float maxShakeOffset = 0.03f;

        [Tooltip("Shake frequency (vibrations per second)")]
        public float shakeFrequency = 25f;

        // Current internal targets
        private float _targetBurden = 0.5f;
        private float _targetRisk = 0.2f;
        private Vector3 _basePosition;
        private MaterialPropertyBlock _propBlock;

        private void Awake()
        {
            _basePosition = transform.localPosition;
            _propBlock = new MaterialPropertyBlock();

            if (targetRenderer == null)
            {
                targetRenderer = GetComponentInChildren<Renderer>();
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

            targetRenderer.GetPropertyBlock(_propBlock);
            _propBlock.SetColor("_Color", currentColor);
            _propBlock.SetColor("_BaseColor", currentColor); // Supports URP Lit shader
            targetRenderer.SetPropertyBlock(_propBlock);
        }

        private void UpdateShake()
        {
            if (_targetRisk < 0.2f)
            {
                // Stable, negligible vibration
                transform.localPosition = _basePosition;
                return;
            }

            // High risk causes rapid shaking vibration
            float intensity = Mathf.InverseLerp(0.2f, 1.0f, _targetRisk) * maxShakeOffset;
            float offsetX = (Mathf.PerlinNoise(Time.time * shakeFrequency, 0.0f) - 0.5f) * 2f * intensity;
            float offsetZ = (Mathf.PerlinNoise(0.0f, Time.time * shakeFrequency) - 0.5f) * 2f * intensity;

            transform.localPosition = _basePosition + new Vector3(offsetX, 0f, offsetZ);
        }
    }
}
