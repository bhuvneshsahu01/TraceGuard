"""
traceguard/drift/chi2.py
------------------------
Chi-Square (chi^2) Homogeneity Test for categorical signals.
Evaluates category distribution shifts (e.g., topic route, status code, tool name)
via scipy.stats.contingency.chi2_contingency.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np
from scipy import stats


@dataclass
class ChiSquareResult:
    """Results from a Chi-Square homogeneity test."""
    signal_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: int
    alpha: float = 0.05
    is_drift_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "metric": "ChiSquare_Homogeneity",
            "statistic": round(self.statistic, 5),
            "p_value": float(self.p_value),
            "degrees_of_freedom": self.degrees_of_freedom,
            "alpha": self.alpha,
            "is_drift_detected": self.is_drift_detected,
        }


def chi2_homogeneity_test(
    baseline: List[Any],
    current: List[Any],
    signal_name: str = "categorical_signal",
    alpha: float = 0.05,
) -> ChiSquareResult:
    """
    Computes chi-square test of homogeneity across two categorical distributions.
    """
    if len(baseline) == 0 or len(current) == 0:
        return ChiSquareResult(
            signal_name=signal_name,
            statistic=0.0,
            p_value=1.0,
            degrees_of_freedom=0,
            alpha=alpha,
            is_drift_detected=False,
        )

    # Union of all distinct categories
    all_categories = sorted(list(set(baseline) | set(current)))
    if len(all_categories) <= 1:
        return ChiSquareResult(
            signal_name=signal_name,
            statistic=0.0,
            p_value=1.0,
            degrees_of_freedom=0,
            alpha=alpha,
            is_drift_detected=False,
        )

    base_map = {c: 0 for c in all_categories}
    curr_map = {c: 0 for c in all_categories}

    for item in baseline:
        base_map[item] += 1
    for item in current:
        curr_map[item] += 1

    base_counts = [base_map[c] for c in all_categories]
    curr_counts = [curr_map[c] for c in all_categories]

    # 2 x C contingency table
    contingency_table = np.array([base_counts, curr_counts], dtype=np.int64)

    # Guard: if any column is all 0, remove it
    valid_cols = (contingency_table.sum(axis=0) > 0)
    contingency_table = contingency_table[:, valid_cols]

    if contingency_table.shape[1] <= 1:
        return ChiSquareResult(
            signal_name=signal_name,
            statistic=0.0,
            p_value=1.0,
            degrees_of_freedom=0,
            alpha=alpha,
            is_drift_detected=False,
        )

    res = stats.contingency.chi2_contingency(contingency_table)
    stat = float(res.statistic)
    p_val = float(res.pvalue)
    dof = int(res.dof)
    is_drift = p_val < alpha

    return ChiSquareResult(
        signal_name=signal_name,
        statistic=stat,
        p_value=p_val,
        degrees_of_freedom=dof,
        alpha=alpha,
        is_drift_detected=is_drift,
    )
