"""
traceguard/drift/psi.py
-----------------------
Population Stability Index (PSI) calculation for continuous scalar distributions.
Computes quantile-binned population stability statistics and standard 0.10 / 0.25 thresholds.
Note: PSI does not output a p-value; it is an informational divergence metric.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class PSIResult:
    """Results from a Population Stability Index (PSI) calculation."""
    signal_name: str
    psi: float
    threshold_stable: float = 0.10
    threshold_significant: float = 0.25
    status: str = "STABLE"  # STABLE, MODERATE_DRIFT, SIGNIFICANT_DRIFT
    is_drift_detected: bool = False
    num_bins: int = 10
    bin_proportions: Optional[Tuple[List[float], List[float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "metric": "PSI",
            "psi": round(self.psi, 5),
            "status": self.status,
            "is_drift_detected": self.is_drift_detected,
            "threshold_stable": self.threshold_stable,
            "threshold_significant": self.threshold_significant,
            "num_bins": self.num_bins,
        }


def calculate_psi(
    baseline: List[float],
    current: List[float],
    signal_name: str = "scalar_signal",
    num_bins: int = 10,
    epsilon: float = 1e-6,
    drift_threshold: float = 0.25,
) -> PSIResult:
    """
    Computes Population Stability Index (PSI) over quantile-binned scalar distributions.
    """
    base_arr = np.asarray(baseline, dtype=np.float64)
    curr_arr = np.asarray(current, dtype=np.float64)

    if len(base_arr) == 0 or len(curr_arr) == 0:
        return PSIResult(
            signal_name=signal_name,
            psi=0.0,
            status="INSUFFICIENT_DATA",
            is_drift_detected=False,
            num_bins=num_bins,
        )

    # 1. Quantile-based bin edges from baseline
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(base_arr, quantiles)
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return PSIResult(
            signal_name=signal_name,
            psi=0.0,
            status="STABLE",
            is_drift_detected=False,
            num_bins=num_bins,
        )

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    # 2. Histogram counts
    base_counts, _ = np.histogram(base_arr, bins=bin_edges)
    curr_counts, _ = np.histogram(curr_arr, bins=bin_edges)

    # 3. Proportions with epsilon smoothing
    base_prop = (base_counts + epsilon) / (np.sum(base_counts) + epsilon * len(base_counts))
    curr_prop = (curr_counts + epsilon) / (np.sum(curr_counts) + epsilon * len(curr_counts))

    # 4. PSI computation: sum (curr - base) * ln(curr / base)
    psi_terms = (curr_prop - base_prop) * np.log(curr_prop / base_prop)
    total_psi = float(np.sum(psi_terms))

    # 5. Status determination
    if total_psi < 0.10:
        status = "STABLE"
    elif total_psi < 0.25:
        status = "MODERATE_DRIFT"
    else:
        status = "SIGNIFICANT_DRIFT"

    is_drift = total_psi >= drift_threshold

    return PSIResult(
        signal_name=signal_name,
        psi=total_psi,
        threshold_stable=0.10,
        threshold_significant=0.25,
        status=status,
        is_drift_detected=is_drift,
        num_bins=len(bin_edges) - 1,
        bin_proportions=(base_prop.tolist(), curr_prop.tolist()),
    )
