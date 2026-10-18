"""
tests/test_drift_monitor.py
---------------------------
Unit tests for traceguard.drift:
- PSI on continuous scalars with 0.10 / 0.25 thresholds
- Two-sample Kolmogorov-Smirnov (KS) test via scipy.stats
- Chi-Square homogeneity test on categorical signals
- Kernel MMD with median heuristic bandwidth and permutation testing (B=200)
- Benjamini-Hochberg FDR step-up control across multi-signal windows
- End-to-end DriftMonitor window evaluation
"""

import numpy as np

from traceguard.drift import (
    DriftMonitor,
    calculate_psi,
    ks_two_sample_test,
    chi2_homogeneity_test,
    mmd_permutation_test,
    benjamini_hochberg,
)


class TestPSICalculation:
    def test_identical_distributions_yields_stable_status(self):
        rng = np.random.default_rng(42)
        baseline = rng.normal(100.0, 15.0, 1000).tolist()
        current = rng.normal(100.0, 15.0, 1000).tolist()

        res = calculate_psi(baseline, current, num_bins=10)
        assert res.psi < 0.10
        assert res.status == "STABLE"
        assert res.is_drift_detected is False

    def test_moderate_and_significant_drift_thresholds(self):
        rng = np.random.default_rng(42)
        baseline = rng.normal(100.0, 15.0, 1000).tolist()
        # Shift mean by 1 standard deviation
        current_moderate = rng.normal(115.0, 15.0, 1000).tolist()
        # Shift mean by 3 standard deviations
        current_significant = rng.normal(145.0, 15.0, 1000).tolist()

        res_mod = calculate_psi(baseline, current_moderate, num_bins=10)
        assert res_mod.psi >= 0.10
        assert res_mod.status in ("MODERATE_DRIFT", "SIGNIFICANT_DRIFT")

        res_sig = calculate_psi(baseline, current_significant, num_bins=10)
        assert res_sig.psi >= 0.25
        assert res_sig.status == "SIGNIFICANT_DRIFT"
        assert res_sig.is_drift_detected is True


class TestKSTest:
    def test_ks_null_distribution_no_drift(self):
        rng = np.random.default_rng(42)
        base = rng.normal(50.0, 10.0, 500).tolist()
        curr = rng.normal(50.0, 10.0, 500).tolist()

        res = ks_two_sample_test(base, curr, alpha=0.05)
        assert res.p_value > 0.05
        assert res.is_drift_detected is False

    def test_ks_shifted_distribution_detects_drift(self):
        rng = np.random.default_rng(42)
        base = rng.normal(50.0, 10.0, 500).tolist()
        curr = rng.normal(65.0, 10.0, 500).tolist()

        res = ks_two_sample_test(base, curr, alpha=0.05)
        assert res.p_value < 0.001
        assert res.is_drift_detected is True


class TestChiSquareTest:
    def test_categorical_homogeneity_stable(self):
        rng = np.random.default_rng(42)
        categories = ["route_a", "route_b", "route_c", "route_d"]
        probs = [0.4, 0.3, 0.2, 0.1]
        base = rng.choice(categories, size=1000, p=probs).tolist()
        curr = rng.choice(categories, size=500, p=probs).tolist()

        res = chi2_homogeneity_test(base, curr, alpha=0.05)
        assert res.p_value > 0.05
        assert res.is_drift_detected is False
        assert res.degrees_of_freedom == 3

    def test_categorical_homogeneity_drift(self):
        rng = np.random.default_rng(42)
        categories = ["route_a", "route_b", "route_c", "route_d"]
        base_probs = [0.4, 0.3, 0.2, 0.1]
        curr_probs = [0.1, 0.1, 0.5, 0.3]
        base = rng.choice(categories, size=1000, p=base_probs).tolist()
        curr = rng.choice(categories, size=500, p=curr_probs).tolist()

        res = chi2_homogeneity_test(base, curr, alpha=0.05)
        assert res.p_value < 0.001
        assert res.is_drift_detected is True


class TestKernelMMD:
    def test_mmd_identical_distributions(self):
        rng = np.random.default_rng(42)
        base = rng.normal(0.0, 1.0, (100, 16))
        curr = rng.normal(0.0, 1.0, (100, 16))

        res = mmd_permutation_test(base, curr, num_permutations=100, alpha=0.05, random_state=42)
        assert res.p_value > 0.05
        assert res.is_drift_detected is False
        assert res.bandwidth_sigma > 0

    def test_mmd_shifted_embeddings_detects_drift(self):
        rng = np.random.default_rng(42)
        base = rng.normal(0.0, 1.0, (100, 16))
        curr = rng.normal(0.8, 1.0, (100, 16))

        res = mmd_permutation_test(base, curr, num_permutations=100, alpha=0.05, random_state=42)
        assert res.p_value <= 0.05
        assert res.is_drift_detected is True
        assert res.statistic > 0


class TestBenjaminiHochbergFDR:
    def test_bh_controls_false_discovery(self):
        p_vals = {
            "sig_strong": 0.0005,
            "sig_borderline": 0.045,
            "sig_null1": 0.55,
            "sig_null2": 0.88,
        }
        res = benjamini_hochberg(p_vals, alpha=0.05)
        assert res.rejections["sig_strong"] is True
        # Under BH with m=4, rank 2 requires p <= 2/4 * 0.05 = 0.025, so 0.045 is controlled and rejected from false alarms
        assert res.rejections["sig_borderline"] is False
        assert res.rejections["sig_null1"] is False
        assert res.rejections["sig_null2"] is False
        assert res.any_rejected is True

    def test_bh_all_nulls_no_rejections(self):
        p_vals = {f"sig_{i}": 0.15 + i * 0.1 for i in range(5)}
        res = benjamini_hochberg(p_vals, alpha=0.05)
        assert res.any_rejected is False
        assert all(rej is False for rej in res.rejections.values())


class TestUnifiedDriftMonitor:
    def test_multi_signal_evaluation_stable(self):
        rng = np.random.default_rng(42)
        monitor = DriftMonitor(alpha=0.05)

        # Register baselines
        monitor.register_scalar_baseline("latency_ms", rng.normal(50.0, 10.0, 500).tolist())
        monitor.register_scalar_baseline("prompt_len", rng.normal(120.0, 20.0, 500).tolist())
        monitor.register_categorical_baseline("tool_name", rng.choice(["search", "calc", "sql"], size=500).tolist())
        monitor.register_embedding_baseline("prompt_emb", rng.normal(0.0, 1.0, (80, 16)))

        # Evaluate identical window
        cand_data = {
            "latency_ms": rng.normal(50.0, 10.0, 200).tolist(),
            "prompt_len": rng.normal(120.0, 20.0, 200).tolist(),
            "tool_name": rng.choice(["search", "calc", "sql"], size=200).tolist(),
            "prompt_emb": rng.normal(0.0, 1.0, (80, 16)),
        }

        report = monitor.evaluate_window(cand_data, num_mmd_permutations=50)
        assert report.is_drift_detected is False
        assert "STABLE" in report.summary_message

    def test_multi_signal_evaluation_detects_drift(self):
        rng = np.random.default_rng(42)
        monitor = DriftMonitor(alpha=0.05)

        monitor.register_scalar_baseline("latency_ms", rng.normal(50.0, 10.0, 500).tolist())
        monitor.register_embedding_baseline("prompt_emb", rng.normal(0.0, 1.0, (80, 16)))

        # Candidate window with shifted latency and shifted embeddings
        cand_data = {
            "latency_ms": rng.normal(120.0, 25.0, 200).tolist(),
            "prompt_emb": rng.normal(1.2, 1.0, (80, 16)),
        }

        report = monitor.evaluate_window(cand_data, num_mmd_permutations=50)
        assert report.is_drift_detected is True
        assert "DRIFT DETECTED" in report.summary_message
