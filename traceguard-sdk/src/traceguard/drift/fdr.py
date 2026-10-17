"""
traceguard/drift/fdr.py
-----------------------
Benjamini-Hochberg (BH) Step-Up Procedure for False Discovery Rate (FDR) control.
Guarantees multiple hypothesis testing over all p-value signals (KS, Chi2, MMD)
strictly controls FDR <= target alpha.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class FDRResult:
    """Results from Benjamini-Hochberg FDR control."""
    alpha: float
    rejections: Dict[str, bool]
    q_values: Dict[str, float]
    raw_p_values: Dict[str, float]
    any_rejected: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "any_rejected": self.any_rejected,
            "rejections": self.rejections,
            "q_values": {k: round(v, 6) for k, v in self.q_values.items()},
            "raw_p_values": {k: round(v, 6) for k, v in self.raw_p_values.items()},
        }


def benjamini_hochberg(
    p_values: Dict[str, float],
    alpha: float = 0.05,
) -> FDRResult:
    """
    Applies Benjamini-Hochberg step-up procedure across p-value signals.

    Parameters:
    -----------
    p_values: Dict[str, float]
        Mapping from signal name to its raw p-value.
    alpha: float
        Target False Discovery Rate threshold (default: 0.05).

    Returns:
    --------
    FDRResult with individual rejections, adjusted q-values, and global drift boolean.
    """
    items = list(p_values.items())
    m = len(items)
    if m == 0:
        return FDRResult(
            alpha=alpha,
            rejections={},
            q_values={},
            raw_p_values={},
            any_rejected=False,
        )

    # 1. Sort by ascending p-value
    sorted_items = sorted(items, key=lambda x: x[1])
    p_sorted = [x[1] for x in sorted_items]

    # 2. BH critical thresholds: (k / m) * alpha for k = 1..m
    crit = [(k / m) * alpha for k in range(1, m + 1)]

    # 3. Find largest index k where p_(k) <= (k/m)*alpha
    k_max = -1
    for k in range(m - 1, -1, -1):
        if p_sorted[k] <= crit[k]:
            k_max = k
            break

    # 4. Rejections: all signals with rank <= k_max
    rejections = {}
    for i in range(m):
        name = sorted_items[i][0]
        rejections[name] = (i <= k_max) if k_max != -1 else False

    # 5. Adjusted p-values (q-values): q_(i) = min_{j >= i} (m / j) * p_(j)
    q_vals = [0.0] * m
    running_min = 1.0
    for i in range(m - 1, -1, -1):
        rank = i + 1
        q_raw = (m / rank) * p_sorted[i]
        running_min = min(running_min, q_raw)
        q_vals[i] = min(1.0, running_min)

    q_values = {sorted_items[i][0]: q_vals[i] for i in range(m)}
    any_rejected = any(rejections.values())

    return FDRResult(
        alpha=alpha,
        rejections=rejections,
        q_values=q_values,
        raw_p_values=p_values,
        any_rejected=any_rejected,
    )
