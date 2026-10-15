"""
traceguard/evals/drift.py
-------------------------
Production Statistical Drift Engine for PR gating and continuous evaluation.
Integrates Population Stability Index (PSI) with bootstrap confidence intervals,
and two-sample Kolmogorov-Smirnov (KS) tests to detect silent distribution degradation.
"""

from typing import List
import numpy as np

from traceguard.evals.ks_test import KSTwoSampleTester
from traceguard.evals.psi_calculator import PSICalculator


class StatisticalDriftEngine:
    """
    Integrates Bootstrap Confidence Intervals (CI), Population Stability Index (PSI), 
    and Kolmogorov-Smirnov (KS) tests directly to mathematically gate PRs on eval degradation.
    """

    def __init__(
        self,
        historical_baseline: List[float],
        psi_threshold: float = 0.10,
        ks_alpha: float = 0.05,
    ):
        self.baseline = historical_baseline
        self.psi_threshold = psi_threshold
        self.ks_alpha = ks_alpha
        self.psi_calc = PSICalculator(num_bins=10, num_bootstrap=100)
        self.ks_tester = KSTwoSampleTester(alpha=ks_alpha)

    def validate_pr_candidate(
        self,
        candidate_scores: List[float],
        strict_bootstrap_mean: bool = True,
    ) -> bool:
        """
        Runs rigorous statistical tests to ensure the candidate PR does not degrade performance.
        Returns True if safe to merge, False if distribution drift is detected.
        """
        if not self.baseline or not candidate_scores:
            return False

        # 1. KS Test for continuous distribution divergence
        ks_result = self.ks_tester.test(self.baseline, candidate_scores)
        if ks_result.is_drift_detected:
            return False  # Statistically significant drift detected

        # 2. Population Stability Index (PSI) test
        psi_summary = self.psi_calc.calculate_psi(self.baseline, candidate_scores)
        if psi_summary.psi >= self.psi_threshold:
            return False  # Population instability

        # 3. Bootstrap CI check on candidate distribution mean
        if strict_bootstrap_mean:
            rng = np.random.default_rng(42)
            c_arr = np.asarray(candidate_scores, dtype=np.float64)
            boot_means = [float(np.mean(rng.choice(c_arr, size=len(c_arr), replace=True))) for _ in range(100)]
            lower_ci = float(np.percentile(boot_means, 2.5))

            baseline_mean = float(np.mean(self.baseline))
            # If the lower bound of candidate is substantially below baseline mean, gate PR
            if lower_ci < (baseline_mean - 0.05):
                return False

        return True
