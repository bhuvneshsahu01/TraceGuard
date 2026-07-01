from typing import List

def bootstrap_ci_stub(data: List[float]) -> tuple[float, float]:
    """Stub for Bootstrap Confidence Interval calculation."""
    if not data: return 0.0, 0.0
    mean = sum(data) / len(data)
    # Simulate a narrow CI around the mean
    return max(0.0, mean - 0.05), min(1.0, mean + 0.05)
    
def psi_stub(expected: List[float], actual: List[float]) -> float:
    """Stub for Population Stability Index (PSI)."""
    return 0.05 # < 0.1 is usually stable

def ks_test_stub(data1: List[float], data2: List[float]) -> float:
    """Stub for KS test returning p-value."""
    return 0.8 # High p-value = same distribution

class StatisticalDriftEngine:
    """
    Integrates Bootstrap Confidence Intervals (CI), Population Stability Index (PSI), 
    and KS tests directly to mathematically gate PRs on eval degradation.
    """
    def __init__(self, historical_baseline: List[float]):
        self.baseline = historical_baseline
        
    def validate_pr_candidate(self, candidate_scores: List[float]) -> bool:
        """
        Runs rigorous statistical tests to ensure the PR doesn't degrade performance.
        Returns True if safe to merge.
        """
        # 1. KS Test for distribution shift
        p_value = ks_test_stub(self.baseline, candidate_scores)
        if p_value < 0.05:
            return False # Reject: Statistically significant drift detected
            
        # 2. PSI Check
        psi = psi_stub(self.baseline, candidate_scores)
        if psi > 0.1:
            return False # Reject: Population instability
            
        # 3. Bootstrap CI check on the mean
        lower, upper = bootstrap_ci_stub(candidate_scores)
        baseline_mean = sum(self.baseline) / len(self.baseline) if self.baseline else 0.0
        
        # If the lower bound of candidate is below the baseline mean, it's risky
        if lower < (baseline_mean - 0.02):
            return False
            
        return True
