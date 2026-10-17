"""
traceguard/drift/monitor.py
---------------------------
Unified DriftMonitor coordinating PSI, KS, Chi-Square, and Kernel MMD tests
with Benjamini-Hochberg False Discovery Rate (FDR) control across multi-signal windows.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from .psi import PSIResult, calculate_psi
from .ks import KSResult, ks_two_sample_test
from .chi2 import ChiSquareResult, chi2_homogeneity_test
from .mmd import MMDResult, mmd_permutation_test
from .fdr import FDRResult, benjamini_hochberg


@dataclass
class DriftReport:
    """Comprehensive evaluation report for a monitoring window."""
    is_drift_detected: bool
    psi_results: Dict[str, PSIResult] = field(default_factory=dict)
    ks_results: Dict[str, KSResult] = field(default_factory=dict)
    chi2_results: Dict[str, ChiSquareResult] = field(default_factory=dict)
    mmd_results: Dict[str, MMDResult] = field(default_factory=dict)
    fdr_result: Optional[FDRResult] = None
    alpha: float = 0.05
    summary_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "is_drift_detected": self.is_drift_detected,
            "alpha": self.alpha,
            "summary_message": self.summary_message,
            "psi": {k: v.to_dict() for k, v in self.psi_results.items()},
            "ks": {k: v.to_dict() for k, v in self.ks_results.items()},
            "chi2": {k: v.to_dict() for k, v in self.chi2_results.items()},
            "mmd": {k: v.to_dict() for k, v in self.mmd_results.items()},
        }
        if self.fdr_result:
            res["fdr_control"] = self.fdr_result.to_dict()
        return res


class DriftMonitor:
    """
    Production Statistical Drift Monitor for LLM and Agentic AI systems.
    Coordinates continuous scalar tests (KS, PSI), categorical tests (Chi^2),
    and embedding tests (Kernel MMD) behind Benjamini-Hochberg FDR control.
    """

    def __init__(self, alpha: float = 0.05, psi_threshold: float = 0.25):
        self.alpha = alpha
        self.psi_threshold = psi_threshold
        self.scalar_baselines: Dict[str, List[float]] = {}
        self.categorical_baselines: Dict[str, List[Any]] = {}
        self.embedding_baselines: Dict[str, np.ndarray] = {}

    def register_scalar_baseline(self, name: str, values: List[float]) -> "DriftMonitor":
        """Registers a baseline continuous distribution for a scalar signal."""
        self.scalar_baselines[name] = list(values)
        return self

    def register_categorical_baseline(self, name: str, categories: List[Any]) -> "DriftMonitor":
        """Registers a baseline categorical distribution (e.g., tool routes, status codes)."""
        self.categorical_baselines[name] = list(categories)
        return self

    def register_embedding_baseline(self, name: str, embeddings: np.ndarray) -> "DriftMonitor":
        """Registers a baseline embedding matrix (N x D)."""
        self.embedding_baselines[name] = np.asarray(embeddings, dtype=np.float64)
        return self

    def evaluate_window(
        self,
        candidate_data: Dict[str, Any],
        alpha: Optional[float] = None,
        apply_fdr: bool = True,
        num_mmd_permutations: int = 200,
        random_state: int = 42,
    ) -> DriftReport:
        """
        Evaluates a candidate monitoring window against all registered baselines.
        """
        target_alpha = alpha if alpha is not None else self.alpha

        psi_results: Dict[str, PSIResult] = {}
        ks_results: Dict[str, KSResult] = {}
        chi2_results: Dict[str, ChiSquareResult] = {}
        mmd_results: Dict[str, MMDResult] = {}

        p_values_to_test: Dict[str, float] = {}

        # 1. Continuous Scalar Signals
        for name, base_vals in self.scalar_baselines.items():
            if name in candidate_data:
                curr_vals = candidate_data[name]

                # (a) PSI computation (does not yield p-value)
                psi_res = calculate_psi(
                    base_vals,
                    curr_vals,
                    signal_name=name,
                    drift_threshold=self.psi_threshold,
                )
                psi_results[name] = psi_res

                # (b) KS test (yields p-value)
                ks_res = ks_two_sample_test(
                    base_vals,
                    curr_vals,
                    signal_name=name,
                    alpha=target_alpha,
                )
                ks_results[name] = ks_res
                p_values_to_test[f"ks_{name}"] = ks_res.p_value

        # 2. Categorical Signals
        for name, base_cats in self.categorical_baselines.items():
            if name in candidate_data:
                curr_cats = candidate_data[name]
                chi_res = chi2_homogeneity_test(
                    base_cats,
                    curr_cats,
                    signal_name=name,
                    alpha=target_alpha,
                )
                chi2_results[name] = chi_res
                p_values_to_test[f"chi2_{name}"] = chi_res.p_value

        # 3. Embedding Distributions (MMD)
        for name, base_emb in self.embedding_baselines.items():
            if name in candidate_data:
                curr_emb = candidate_data[name]
                mmd_res = mmd_permutation_test(
                    base_emb,
                    curr_emb,
                    signal_name=name,
                    num_permutations=num_mmd_permutations,
                    alpha=target_alpha,
                    random_state=random_state,
                )
                mmd_results[name] = mmd_res
                p_values_to_test[f"mmd_{name}"] = mmd_res.p_value

        # 4. Multi-Signal False Discovery Rate (FDR) Control
        fdr_res: Optional[FDRResult] = None
        drift_detected = False

        if p_values_to_test and apply_fdr:
            fdr_res = benjamini_hochberg(p_values_to_test, alpha=target_alpha)
            drift_detected = fdr_res.any_rejected
            # Sync individual test drift flags to reflect FDR rejections
            for signal_key, rejected in fdr_res.rejections.items():
                if signal_key.startswith("ks_"):
                    orig_name = signal_key[3:]
                    if orig_name in ks_results:
                        ks_results[orig_name].is_drift_detected = rejected
                elif signal_key.startswith("chi2_"):
                    orig_name = signal_key[5:]
                    if orig_name in chi2_results:
                        chi2_results[orig_name].is_drift_detected = rejected
                elif signal_key.startswith("mmd_"):
                    orig_name = signal_key[4:]
                    if orig_name in mmd_results:
                        mmd_results[orig_name].is_drift_detected = rejected
        elif p_values_to_test and not apply_fdr:
            # Uncorrected individual p-value significance
            drift_detected = any(
                res.is_drift_detected for res in list(ks_results.values()) + list(chi2_results.values()) + list(mmd_results.values())
            )

        # 5. Check PSI divergence (severe population instability)
        for psi_res in psi_results.values():
            if psi_res.is_drift_detected:
                drift_detected = True

        # Generate summary message
        flagged_signals = []
        if fdr_res:
            for k, rej in fdr_res.rejections.items():
                if rej:
                    flagged_signals.append(f"{k} (q={fdr_res.q_values[k]:.4f})")
        for k, p_res in psi_results.items():
            if p_res.is_drift_detected:
                flagged_signals.append(f"psi_{k} ({p_res.psi:.3f})")

        if drift_detected:
            msg = f"DRIFT DETECTED across {len(flagged_signals)} signals: {', '.join(flagged_signals)}"
        else:
            msg = f"STABLE: All {len(p_values_to_test)} tested hypothesis signals within target alpha={target_alpha}."

        return DriftReport(
            is_drift_detected=drift_detected,
            psi_results=psi_results,
            ks_results=ks_results,
            chi2_results=chi2_results,
            mmd_results=mmd_results,
            fdr_result=fdr_res,
            alpha=target_alpha,
            summary_message=msg,
        )
