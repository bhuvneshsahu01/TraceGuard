"""
traceguard/drift/ks.py
----------------------
Two-Sample Kolmogorov-Smirnov (KS) Test for continuous scalar signals.
Returns exact or asymptotic p-value via scipy.stats.ks_2samp.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np
from scipy import stats


@dataclass
class KSResult:
    """Results from a Two-Sample Kolmogorov-Smirnov (KS) test."""
    signal_name: str
    statistic: float
    p_value: float
    alpha: float = 0.05
    is_drift_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "metric": "KS_2sample",
            "statistic": round(self.statistic, 5),
            "p_value": float(self.p_value),
            "alpha": self.alpha,
            "is_drift_detected": self.is_drift_detected,
        }


def ks_two_sample_test(
    baseline: List[float],
    current: List[float],
    signal_name: str = "scalar_signal",
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> KSResult:
    """
    Computes two-sample Kolmogorov-Smirnov test to detect shift between baseline and current distributions.
    """
    base_arr = np.asarray(baseline, dtype=np.float64)
    curr_arr = np.asarray(current, dtype=np.float64)

    if len(base_arr) == 0 or len(curr_arr) == 0:
        return KSResult(
            signal_name=signal_name,
            statistic=0.0,
            p_value=1.0,
            alpha=alpha,
            is_drift_detected=False,
        )

    res = stats.ks_2samp(base_arr, curr_arr, alternative=alternative)
    stat = float(res.statistic)
    p_val = float(res.pvalue)
    is_drift = p_val < alpha

    return KSResult(
        signal_name=signal_name,
        statistic=stat,
        p_value=p_val,
        alpha=alpha,
        is_drift_detected=is_drift,
    )
