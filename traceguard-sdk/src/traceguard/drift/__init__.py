"""
traceguard.drift
----------------
Statistical Drift Monitoring Suite:
- PSI (Population Stability Index) with quantile binning
- KS (Two-Sample Kolmogorov-Smirnov) test for continuous signals
- Chi-Square (Homogeneity) test for categorical signals
- Kernel MMD (Maximum Mean Discrepancy) with permutation testing
- Benjamini-Hochberg (BH) False Discovery Rate control
- DriftMonitor orchestrator
"""

from .psi import PSIResult, calculate_psi
from .ks import KSResult, ks_two_sample_test
from .chi2 import ChiSquareResult, chi2_homogeneity_test
from .mmd import MMDResult, mmd_permutation_test
from .fdr import FDRResult, benjamini_hochberg
from .monitor import DriftMonitor, DriftReport

__all__ = [
    "PSIResult",
    "calculate_psi",
    "KSResult",
    "ks_two_sample_test",
    "ChiSquareResult",
    "chi2_homogeneity_test",
    "MMDResult",
    "mmd_permutation_test",
    "FDRResult",
    "benjamini_hochberg",
    "DriftMonitor",
    "DriftReport",
]
