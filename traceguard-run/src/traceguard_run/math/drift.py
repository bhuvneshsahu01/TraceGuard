import numpy as np
from scipy.stats import ks_2samp
from typing import Dict, Union

def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """
    Calculates the Population Stability Index (PSI) to detect drift in distributions.
    Higher PSI means more drift. Rule of thumb:
    PSI < 0.1: No significant change
    0.1 <= PSI < 0.2: Moderate change
    PSI >= 0.2: Significant change
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine bins based on expected distribution
    breakpoints = np.arange(0, buckets + 1) / buckets * 100
    bins = np.percentile(expected, breakpoints)
    # Ensure bins are unique (e.g., if many zeros)
    bins = np.unique(bins)
    if len(bins) < 2:
        # Fallback if expected has zero variance
        if np.array_equal(expected, actual):
            return 0.0
        return float('inf') # Maximum drift
        
    # Add small epsilon to bins for numerical stability at edges
    bins[0] = -np.inf
    bins[-1] = np.inf
    
    expected_percents = np.histogram(expected, bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins)[0] / len(actual)
    
    # Avoid division by zero and log(0)
    def substitute_zeroes(x: np.ndarray) -> np.ndarray:
        return np.where(x == 0, 0.0001, x)
        
    expected_percents = substitute_zeroes(expected_percents)
    actual_percents = substitute_zeroes(actual_percents)
    
    psi_values = (expected_percents - actual_percents) * np.log(expected_percents / actual_percents)
    return float(np.sum(psi_values))

def calculate_ks_test(expected: np.ndarray, actual: np.ndarray) -> Dict[str, Union[float, bool]]:
    """
    Calculates the Kolmogorov-Smirnov test for two continuous distributions.
    Checks if they are drawn from the same underlying distribution.
    """
    if len(expected) == 0 or len(actual) == 0:
        return {"statistic": 0.0, "p_value": 1.0, "is_drifted": False}
        
    statistic, p_value = ks_2samp(expected, actual)
    
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "is_drifted": p_value < 0.05 # Reject null hypothesis if p_value < 0.05
    }
