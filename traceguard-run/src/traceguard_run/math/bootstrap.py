import numpy as np
from typing import List, Dict

def calculate_bootstrap_ci(scores: List[float], baseline_scores: List[float], iterations: int = 10000, alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculates the Bootstrap Confidence Interval for the difference between two sets of scores.
    Returns a dictionary containing the lower bound, upper bound, and mean difference.
    
    Args:
        scores: The evaluation scores of the current run.
        baseline_scores: The evaluation scores of the baseline run.
        iterations: Number of bootstrap iterations.
        alpha: Significance level (default 0.05 for 95% CI).
    """
    scores_np = np.array(scores)
    baseline_np = np.array(baseline_scores)
    
    if len(scores_np) == 0 or len(baseline_np) == 0:
        raise ValueError("Score arrays cannot be empty.")

    # Generate bootstrap samples
    # We resample with replacement from both distributions
    rng = np.random.default_rng(seed=42) # Fixed seed for reproducibility in CI
    
    bootstrap_diffs = np.zeros(iterations)
    for i in range(iterations):
        sample_scores = rng.choice(scores_np, size=len(scores_np), replace=True)
        sample_baseline = rng.choice(baseline_np, size=len(baseline_np), replace=True)
        
        diff = np.mean(sample_scores) - np.mean(sample_baseline)
        bootstrap_diffs[i] = diff
        
    lower_bound = np.percentile(bootstrap_diffs, (alpha / 2) * 100)
    upper_bound = np.percentile(bootstrap_diffs, (1 - alpha / 2) * 100)
    mean_diff = np.mean(bootstrap_diffs)
    
    # Calculate p-value (probability that the difference is <= 0 if mean_diff > 0, etc.)
    # Two-sided p-value
    if mean_diff > 0:
        p_value = np.mean(bootstrap_diffs <= 0) * 2
    else:
        p_value = np.mean(bootstrap_diffs >= 0) * 2

    return {
        "mean_diff": float(mean_diff),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "p_value": float(min(p_value, 1.0)),
        "is_significant": p_value < alpha
    }
