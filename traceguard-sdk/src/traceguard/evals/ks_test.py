"""
traceguard/evals/ks_test.py
---------------------------
Two-sample Kolmogorov-Smirnov (KS) test for continuous distribution drift detection.
Used in TraceGuard to compare continuous cosine similarity distributions, latency,
and semantic confidence scores between baseline and deployment candidates.
"""

from dataclasses import dataclass
from typing import Sequence
import numpy as np
from scipy import stats


@dataclass
class KSResult:
    """Result of two-sample Kolmogorov-Smirnov drift test."""
    statistic: float
    p_value: float
    is_drift_detected: bool
    significance_alpha: float
    description: str


class KSTwoSampleTester:
    """
    Two-sample Kolmogorov-Smirnov goodness-of-fit validator.
    Tests null hypothesis H0: both samples are drawn from the same continuous distribution.
    """

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def test(
        self,
        baseline: Sequence[float],
        current: Sequence[float],
        alternative: str = "two-sided",
    ) -> KSResult:
        """
        Executes two-sample KS test.
        Flags drift if p-value < alpha (rejects null hypothesis of identical distributions).
        """
        b_arr = np.asarray(baseline, dtype=np.float64)
        c_arr = np.asarray(current, dtype=np.float64)

        if len(b_arr) == 0 or len(c_arr) == 0:
            raise ValueError("Baseline and current samples cannot be empty.")

        res = stats.ks_2samp(b_arr, c_arr, alternative=alternative)
        statistic = float(res.statistic)
        p_val = float(res.pvalue)

        drift_detected = p_val < self.alpha

        if drift_detected:
            desc = (
                f"Statistically significant distribution drift detected (KS stat={statistic:.4f}, "
                f"p-value={p_val:.5f} < {self.alpha}). Reject H0."
            )
        else:
            desc = (
                f"No significant distribution shift detected (KS stat={statistic:.4f}, "
                f"p-value={p_val:.5f} >= {self.alpha}). Retain H0."
            )

        return KSResult(
            statistic=round(statistic, 4),
            p_value=round(p_val, 5),
            is_drift_detected=drift_detected,
            significance_alpha=self.alpha,
            description=desc,
        )
