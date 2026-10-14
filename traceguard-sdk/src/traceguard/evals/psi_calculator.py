"""
traceguard/evals/psi_calculator.py
----------------------------------
Population Stability Index (PSI) calculation with Bootstrap Confidence Intervals.
Used in TraceGuard to detect silent distribution shifts in LLM token usage,
latency, and semantic score distributions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
import numpy as np


@dataclass
class PSISummary:
    """Statistical summary of Population Stability Index test."""
    psi: float
    ci_lower: float
    ci_upper: float
    status: str  # "STABLE", "MODERATE_DRIFT", "SIGNIFICANT_DRIFT"
    bin_edges: List[float] = field(default_factory=list)
    expected_pct: List[float] = field(default_factory=list)
    actual_pct: List[float] = field(default_factory=list)

    @property
    def is_drift_detected(self) -> bool:
        return self.psi >= 0.10


class PSICalculator:
    """
    Computes Population Stability Index (PSI) between baseline and live distributions
    with non-parametric bootstrap confidence intervals.
    """

    def __init__(
        self,
        num_bins: int = 10,
        epsilon: float = 1e-4,
        num_bootstrap: int = 250,
        random_state: Optional[int] = 42,
    ):
        self.num_bins = num_bins
        self.epsilon = epsilon
        self.num_bootstrap = num_bootstrap
        self.random_state = random_state

    def _compute_binned_proportions(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculates smoothed bin proportions using baseline quantiles."""
        quantiles = np.linspace(0, 100, self.num_bins + 1)
        bin_edges = np.percentile(baseline, quantiles)
        bin_edges = np.unique(bin_edges)

        # Fallback to linear spacing if distribution has low unique values
        if len(bin_edges) <= 2:
            min_val = min(float(np.min(baseline)), float(np.min(current)))
            max_val = max(float(np.max(baseline)), float(np.max(current)))
            if min_val == max_val:
                bin_edges = np.array([min_val - 1.0, max_val + 1.0])
            else:
                bin_edges = np.linspace(min_val, max_val, self.num_bins + 1)

        # Add unbounded endpoints to capture all outliers
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        # Histogram counts
        expected_counts, _ = np.histogram(baseline, bins=bin_edges)
        actual_counts, _ = np.histogram(current, bins=bin_edges)

        # Normalize with Laplace/epsilon smoothing
        expected_pct = (expected_counts + self.epsilon) / (len(baseline) + len(expected_counts) * self.epsilon)
        actual_pct = (actual_counts + self.epsilon) / (len(current) + len(actual_counts) * self.epsilon)

        return expected_pct, actual_pct, bin_edges

    def _raw_psi(self, expected_pct: np.ndarray, actual_pct: np.ndarray) -> float:
        """Standard PSI summation: sum((A - E) * ln(A / E))."""
        diff = actual_pct - expected_pct
        log_ratio = np.log(actual_pct / expected_pct)
        return float(np.sum(diff * log_ratio))

    def calculate_psi(
        self,
        baseline: Sequence[float],
        current: Sequence[float],
        confidence_level: float = 0.95,
    ) -> PSISummary:
        """
        Calculates point PSI and bootstrap confidence intervals.
        Categorizes result:
          - PSI < 0.10: STABLE (negligible drift)
          - 0.10 <= PSI < 0.25: MODERATE_DRIFT (monitor closely)
          - PSI >= 0.25: SIGNIFICANT_DRIFT (alert/gate PR)
        """
        b_arr = np.asarray(baseline, dtype=np.float64)
        c_arr = np.asarray(current, dtype=np.float64)

        if len(b_arr) == 0 or len(c_arr) == 0:
            raise ValueError("Baseline and current arrays cannot be empty.")

        expected_pct, actual_pct, bin_edges = self._compute_binned_proportions(b_arr, c_arr)
        point_psi = self._raw_psi(expected_pct, actual_pct)

        # Bootstrap Confidence Interval on PSI
        rng = np.random.default_rng(self.random_state)
        boot_psis = []
        n_b = len(b_arr)
        n_c = len(c_arr)

        for _ in range(self.num_bootstrap):
            boot_b = rng.choice(b_arr, size=n_b, replace=True)
            boot_c = rng.choice(c_arr, size=n_c, replace=True)
            exp_p, act_p, _ = self._compute_binned_proportions(boot_b, boot_c)
            boot_psis.append(self._raw_psi(exp_p, act_p))

        alpha = 1.0 - confidence_level
        ci_lower = float(np.percentile(boot_psis, 100 * (alpha / 2)))
        ci_upper = float(np.percentile(boot_psis, 100 * (1 - alpha / 2)))

        if point_psi < 0.10:
            status = "STABLE"
        elif point_psi < 0.25:
            status = "MODERATE_DRIFT"
        else:
            status = "SIGNIFICANT_DRIFT"

        return PSISummary(
            psi=round(point_psi, 4),
            ci_lower=round(max(0.0, ci_lower), 4),
            ci_upper=round(ci_upper, 4),
            status=status,
            bin_edges=[float(x) for x in bin_edges],
            expected_pct=[round(float(p), 5) for p in expected_pct],
            actual_pct=[round(float(p), 5) for p in actual_pct],
        )
