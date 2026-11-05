using System;
using System.Collections.Generic;

namespace DebtSight
{
    /// <summary>
    /// Supported interest calculation methods in DebtSight.
    /// </summary>
    public enum InterestMethod
    {
        ReducingBalance,       // Bank / NBFC / SHG standard EMI
        FlatRate,              // Informal moneylender flat rate
        SimpleInterestBullet   // Crop / harvest loan (interest monthly, principal at end)
    }

    /// <summary>
    /// Periodicity of the entered interest rate.
    /// </summary>
    public enum RatePeriod
    {
        Annual,   // e.g. 24.0% per annum
        Monthly   // e.g. 2.0% or 3.0% per month ("vaddi")
    }

    /// <summary>
    /// Input parameters for a loan calculation.
    /// </summary>
    [Serializable]
    public class LoanInput
    {
        public float principal = 50000f;
        public float interestRate = 24f;
        public RatePeriod ratePeriod = RatePeriod.Annual;
        public int tenureMonths = 12;
        public InterestMethod interestMethod = InterestMethod.ReducingBalance;
        public float monthlyPrepayment = 0f;

        public void Validate()
        {
            if (principal <= 0f)
                throw new ArgumentException($"Principal must be strictly positive (> 0), got ₹{principal:F2}");
            if (interestRate < 0f)
                throw new ArgumentException($"Interest rate cannot be negative, got {interestRate}%");
            if (tenureMonths < 1)
                throw new ArgumentException($"Tenure must be at least 1 month, got {tenureMonths}");
            if (monthlyPrepayment < 0f)
                throw new ArgumentException($"Monthly prepayment cannot be negative, got ₹{monthlyPrepayment:F2}");
        }
    }

    /// <summary>
    /// Record of payments and balance for a single month.
    /// </summary>
    [Serializable]
    public class MonthlyRecord
    {
        public int month;
        public float openingBalance;
        public float payment;
        public float principalPaid;
        public float interestPaid;
        public float closingBalance;
    }

    /// <summary>
    /// Output result of a loan calculation containing the full amortization schedule.
    /// </summary>
    [Serializable]
    public class LoanScheduleResult
    {
        public List<float> monthlyBalance = new List<float>();
        public float monthlyPayment;
        public float totalInterest;
        public float totalRepayment;
        public int debtFreeMonth;
        public float effectiveAnnualRate;
        public List<MonthlyRecord> amortizationTable = new List<MonthlyRecord>();
    }

    /// <summary>
    /// Standalone, pure C# financial calculation engine for DebtSight.
    /// Zero external dependencies, fully compatible with Unity 2021+ and .NET Standard.
    /// </summary>
    public static class DebtSightMathEngine
    {
        /// <summary>
        /// Calculates the full loan amortization schedule.
        /// </summary>
        public static LoanScheduleResult Calculate(LoanInput input)
        {
            if (input == null)
                throw new ArgumentNullException(nameof(input));

            input.Validate();

            switch (input.interestMethod)
            {
                case InterestMethod.ReducingBalance:
                    return CalculateReducingBalance(input);
                case InterestMethod.FlatRate:
                    return CalculateFlatRate(input);
                case InterestMethod.SimpleInterestBullet:
                    return CalculateBulletRepayment(input);
                default:
                    throw new NotSupportedException($"Unsupported interest method: {input.interestMethod}");
            }
        }

        private static LoanScheduleResult CalculateReducingBalance(LoanInput input)
        {
            float p = input.principal;
            float r = ToMonthlyFractionalRate(input.interestRate, input.ratePeriod);
            float apr = ToAnnualPercentageRate(input.interestRate, input.ratePeriod);
            int n = input.tenureMonths;
            float prepayment = input.monthlyPrepayment;

            float baseEmi = CalculateReducingEmi(p, r, n);

            float currentBalance = p;
            var amortization = new List<MonthlyRecord>();
            var monthlyBalances = new List<float>();
            float totalInterest = 0f;
            float totalRepayment = 0f;
            int debtFreeMonth = n;

            for (int m = 1; m <= n; m++)
            {
                if (currentBalance <= 0.0001f)
                {
                    amortization.Add(new MonthlyRecord
                    {
                        month = m,
                        openingBalance = 0f,
                        payment = 0f,
                        principalPaid = 0f,
                        interestPaid = 0f,
                        closingBalance = 0f
                    });
                    monthlyBalances.Add(0f);
                    continue;
                }

                float opening = currentBalance;
                float monthInterest = opening * r;
                float plannedPayment = baseEmi + prepayment;
                float maxNeeded = opening + monthInterest;
                float actualPayment = Math.Min(plannedPayment, maxNeeded);

                float principalPortion = Math.Max(0f, actualPayment - monthInterest);
                float closing = Math.Max(0f, opening - principalPortion);

                if (closing < 0.01f)
                    closing = 0f;

                totalInterest += monthInterest;
                totalRepayment += actualPayment;

                amortization.Add(new MonthlyRecord
                {
                    month = m,
                    openingBalance = (float)Math.Round(opening, 2),
                    payment = (float)Math.Round(actualPayment, 2),
                    principalPaid = (float)Math.Round(principalPortion, 2),
                    interestPaid = (float)Math.Round(monthInterest, 2),
                    closingBalance = (float)Math.Round(closing, 2)
                });
                monthlyBalances.Add((float)Math.Round(closing, 2));
                currentBalance = closing;

                if (closing == 0f && debtFreeMonth == n)
                {
                    debtFreeMonth = m;
                }
            }

            return new LoanScheduleResult
            {
                monthlyBalance = monthlyBalances,
                monthlyPayment = (float)Math.Round(baseEmi, 2),
                totalInterest = (float)Math.Round(totalInterest, 2),
                totalRepayment = (float)Math.Round(totalRepayment, 2),
                debtFreeMonth = debtFreeMonth,
                effectiveAnnualRate = (float)Math.Round(apr, 2),
                amortizationTable = amortization
            };
        }

        private static LoanScheduleResult CalculateFlatRate(LoanInput input)
        {
            float p = input.principal;
            float apr = ToAnnualPercentageRate(input.interestRate, input.ratePeriod);
            int n = input.tenureMonths;
            float prepayment = input.monthlyPrepayment;

            float totalInterestContracted = p * (apr / 100f) * (n / 12f);
            float baseMonthlyPayment = (p + totalInterestContracted) / n;
            float baseMonthlyInterest = totalInterestContracted / n;
            float baseMonthlyPrincipal = p / n;

            float currentBalance = p;
            var amortization = new List<MonthlyRecord>();
            var monthlyBalances = new List<float>();
            float accumulatedInterest = 0f;
            float accumulatedRepayment = 0f;
            int debtFreeMonth = n;

            for (int m = 1; m <= n; m++)
            {
                if (currentBalance <= 0.0001f)
                {
                    amortization.Add(new MonthlyRecord
                    {
                        month = m,
                        openingBalance = 0f,
                        payment = 0f,
                        principalPaid = 0f,
                        interestPaid = 0f,
                        closingBalance = 0f
                    });
                    monthlyBalances.Add(0f);
                    continue;
                }

                float opening = currentBalance;
                float monthInterest = baseMonthlyInterest;
                float principalPaid = Math.Min(opening, baseMonthlyPrincipal + prepayment);
                float actualPayment = principalPaid + monthInterest;
                float closing = Math.Max(0f, opening - principalPaid);

                if (closing < 0.01f)
                    closing = 0f;

                accumulatedInterest += monthInterest;
                accumulatedRepayment += actualPayment;

                amortization.Add(new MonthlyRecord
                {
                    month = m,
                    openingBalance = (float)Math.Round(opening, 2),
                    payment = (float)Math.Round(actualPayment, 2),
                    principalPaid = (float)Math.Round(principalPaid, 2),
                    interestPaid = (float)Math.Round(monthInterest, 2),
                    closingBalance = (float)Math.Round(closing, 2)
                });
                monthlyBalances.Add((float)Math.Round(closing, 2));
                currentBalance = closing;

                if (closing == 0f && debtFreeMonth == n)
                {
                    debtFreeMonth = m;
                }
            }

            float effectiveApr = n > 1 ? apr * (2f * n / (n + 1f)) : apr;

            return new LoanScheduleResult
            {
                monthlyBalance = monthlyBalances,
                monthlyPayment = (float)Math.Round(baseMonthlyPayment, 2),
                totalInterest = (float)Math.Round(accumulatedInterest, 2),
                totalRepayment = (float)Math.Round(accumulatedRepayment, 2),
                debtFreeMonth = debtFreeMonth,
                effectiveAnnualRate = (float)Math.Round(effectiveApr, 2),
                amortizationTable = amortization
            };
        }

        private static LoanScheduleResult CalculateBulletRepayment(LoanInput input)
        {
            float p = input.principal;
            float r = ToMonthlyFractionalRate(input.interestRate, input.ratePeriod);
            float apr = ToAnnualPercentageRate(input.interestRate, input.ratePeriod);
            int n = input.tenureMonths;
            float prepayment = input.monthlyPrepayment;

            float currentBalance = p;
            var amortization = new List<MonthlyRecord>();
            var monthlyBalances = new List<float>();
            float totalInterest = 0f;
            float totalRepayment = 0f;
            int debtFreeMonth = n;

            float regularMonthlyInterest = p * r;

            for (int m = 1; m <= n; m++)
            {
                if (currentBalance <= 0.0001f)
                {
                    amortization.Add(new MonthlyRecord
                    {
                        month = m,
                        openingBalance = 0f,
                        payment = 0f,
                        principalPaid = 0f,
                        interestPaid = 0f,
                        closingBalance = 0f
                    });
                    monthlyBalances.Add(0f);
                    continue;
                }

                float opening = currentBalance;
                float monthInterest = opening * r;
                totalInterest += monthInterest;

                float principalPortion;
                float actualPayment;
                float closing;

                if (m < n)
                {
                    principalPortion = Math.Min(opening, prepayment);
                    actualPayment = monthInterest + principalPortion;
                    closing = Math.Max(0f, opening - principalPortion);
                }
                else
                {
                    principalPortion = opening;
                    actualPayment = monthInterest + principalPortion;
                    closing = 0f;
                }

                if (closing < 0.01f)
                    closing = 0f;

                totalRepayment += actualPayment;

                amortization.Add(new MonthlyRecord
                {
                    month = m,
                    openingBalance = (float)Math.Round(opening, 2),
                    payment = (float)Math.Round(actualPayment, 2),
                    principalPaid = (float)Math.Round(principalPortion, 2),
                    interestPaid = (float)Math.Round(monthInterest, 2),
                    closingBalance = (float)Math.Round(closing, 2)
                });
                monthlyBalances.Add((float)Math.Round(closing, 2));
                currentBalance = closing;

                if (closing == 0f && debtFreeMonth == n)
                {
                    debtFreeMonth = m;
                }
            }

            return new LoanScheduleResult
            {
                monthlyBalance = monthlyBalances,
                monthlyPayment = (float)Math.Round(regularMonthlyInterest, 2),
                totalInterest = (float)Math.Round(totalInterest, 2),
                totalRepayment = (float)Math.Round(totalRepayment, 2),
                debtFreeMonth = debtFreeMonth,
                effectiveAnnualRate = (float)Math.Round(apr, 2),
                amortizationTable = amortization
            };
        }

        public static float CalculateReducingEmi(float principal, float monthlyRate, int tenureMonths)
        {
            if (monthlyRate <= 0f)
                return principal / tenureMonths;

            double factor = Math.Pow(1.0 + monthlyRate, tenureMonths);
            double emi = principal * (monthlyRate * factor) / (factor - 1.0);
            return (float)emi;
        }

        public static float ToAnnualPercentageRate(float rate, RatePeriod period)
        {
            return period == RatePeriod.Monthly ? rate * 12f : rate;
        }

        public static float ToMonthlyFractionalRate(float rate, RatePeriod period)
        {
            if (period == RatePeriod.Monthly)
                return rate / 100f;
            return (rate / 12f) / 100f;
        }
    }
}
