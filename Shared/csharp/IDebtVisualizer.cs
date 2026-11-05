namespace DebtSight
{
    /// <summary>
    /// Shared interface for Unity AR 3D visualization objects.
    /// Implemented by Rakesh on the rice sack / coin stack AR GameObject.
    /// </summary>
    public interface IDebtVisualizer
    {
        /// <summary>
        /// Updates the 3D visual burden level (typically controls 3D model scale and height).
        /// </summary>
        /// <param name="burden">Normalized burden between 0.0f (lowest debt) and 1.0f (peak debt).</param>
        void SetBurden(float burden);

        /// <summary>
        /// Updates the estimated default risk (controls material darkness/color tint and vibration shaking).
        /// </summary>
        /// <param name="risk">Estimated risk probability between 0.0f (safe) and 1.0f (high risk).</param>
        void SetRisk(float risk);
    }
}
