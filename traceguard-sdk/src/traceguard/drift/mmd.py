"""
traceguard/drift/mmd.py
-----------------------
Permutation-Tested Kernel Maximum Mean Discrepancy (MMD) for embedding distributions.
Uses an RBF kernel with the median heuristic for bandwidth sigma and an exact
permutation test (default B=200 permutations) to compute a non-parametric p-value.
Optimized via quadratic-form algebra and Gram-matrix decomposition.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np


@dataclass
class MMDResult:
    """Results from a Kernel MMD permutation test."""
    signal_name: str
    statistic: float
    p_value: float
    bandwidth_sigma: float
    num_permutations: int = 200
    alpha: float = 0.05
    is_drift_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "metric": "Kernel_MMD_Permutation",
            "statistic": round(self.statistic, 6),
            "p_value": float(self.p_value),
            "bandwidth_sigma": round(self.bandwidth_sigma, 4),
            "num_permutations": self.num_permutations,
            "alpha": self.alpha,
            "is_drift_detected": self.is_drift_detected,
        }


def mmd_permutation_test(
    baseline_embeddings: np.ndarray,
    current_embeddings: np.ndarray,
    signal_name: str = "embeddings",
    num_permutations: int = 200,
    alpha: float = 0.05,
    random_state: Optional[int] = 42,
) -> MMDResult:
    """
    Computes unbiased MMD^2 with an RBF kernel and a permutation test for embedding drift.

    Parameters:
    -----------
    baseline_embeddings: np.ndarray (M x D)
        Reference prompt/response embeddings.
    current_embeddings: np.ndarray (N x D)
        Evaluation window embeddings.
    signal_name: str
        Signal identifier.
    num_permutations: int
        Number of random permutations B (default: 200).
    alpha: float
        Significance level.
    random_state: Optional[int]
        Random seed for reproducibility.

    Returns:
    --------
    MMDResult with MMD^2 statistic, exact permutation p-value, and drift verdict.
    """
    X = np.asarray(baseline_embeddings, dtype=np.float64)
    Y = np.asarray(current_embeddings, dtype=np.float64)

    if X.ndim == 1:
        X = X[:, None]
    if Y.ndim == 1:
        Y = Y[:, None]

    m, n = len(X), len(Y)
    if m < 2 or n < 2:
        return MMDResult(
            signal_name=signal_name,
            statistic=0.0,
            p_value=1.0,
            bandwidth_sigma=1.0,
            num_permutations=num_permutations,
            alpha=alpha,
            is_drift_detected=False,
        )

    # 1. Pool embeddings and compute pairwise squared distance matrix via Gram matrix
    Z = np.vstack([X, Y])
    total_len = m + n

    sq_norms = np.sum(Z ** 2, axis=1, keepdims=True)
    dists_sq = np.maximum(0.0, sq_norms + sq_norms.T - 2.0 * (Z @ Z.T))

    # 2. Median heuristic for bandwidth sigma
    triu_idx = np.triu_indices(total_len, k=1)
    if len(triu_idx[0]) > 0:
        med_sq = float(np.median(dists_sq[triu_idx]))
        med = float(np.sqrt(med_sq)) if med_sq > 0 else 1.0
        sigma = med if med > 1e-6 else 1.0
    else:
        sigma = 1.0

    gamma = 1.0 / (2.0 * sigma * sigma)
    # Precomputed full kernel matrix K
    K = np.exp(-gamma * dists_sq)
    np.fill_diagonal(K, 1.0)

    # Precomputed constants for algebraic permutation evaluations
    S_total = float(np.sum(K))
    r = np.sum(K, axis=1)  # row sums vector of length total_len

    # Helper function to compute unbiased MMD^2 from partition indices
    def _compute_mmd2_from_indices(idx_x: np.ndarray, idx_y: np.ndarray) -> float:
        # Evaluate using the smaller partition for speed
        if len(idx_y) <= len(idx_x):
            S_y = float(np.sum(K[np.ix_(idx_y, idx_y)]))
            R_y = float(np.sum(r[idx_y]))
            S_x = S_total - 2.0 * R_y + S_y
            S_xy = R_y - S_y
        else:
            S_x = float(np.sum(K[np.ix_(idx_x, idx_x)]))
            R_x = float(np.sum(r[idx_x]))
            S_y = S_total - 2.0 * R_x + S_x
            S_xy = R_x - S_x

        term_xx = (S_x - m) / (m * (m - 1))
        term_yy = (S_y - n) / (n * (n - 1))
        term_xy = 2.0 * S_xy / (m * n)
        return float(term_xx + term_yy - term_xy)

    # 3. Observed statistic
    idx_x_orig = np.arange(m)
    idx_y_orig = np.arange(m, total_len)
    obs_mmd = _compute_mmd2_from_indices(idx_x_orig, idx_y_orig)

    # 4. Permutation test
    rng = np.random.default_rng(random_state)
    all_indices = np.arange(total_len)
    extreme_count = 0

    for _ in range(num_permutations):
        perm = rng.permutation(all_indices)
        perm_x, perm_y = perm[:m], perm[m:]
        val = _compute_mmd2_from_indices(perm_x, perm_y)
        if val >= obs_mmd:
            extreme_count += 1

    p_value = float((1 + extreme_count) / (num_permutations + 1))
    is_drift = (p_value < alpha) and (obs_mmd > 0)

    return MMDResult(
        signal_name=signal_name,
        statistic=obs_mmd,
        p_value=p_value,
        bandwidth_sigma=sigma,
        num_permutations=num_permutations,
        alpha=alpha,
        is_drift_detected=is_drift,
    )
