"""
tests/test_statistical_drift.py
-------------------------------
Unit and property tests for TraceGuard statistical drift detection suite:
- Population Stability Index (PSI) with bootstrap confidence intervals
- Two-sample Kolmogorov-Smirnov (KS) test for continuous score distributions
- StatisticalDriftEngine PR regression gating
- AgentCycleException for infinite tool and delegation loops
Addresses Batch 2, Task 2.1 requirements.
"""

import numpy as np
import pytest

from traceguard.evals.drift import StatisticalDriftEngine
from traceguard.evals.ks_test import KSTwoSampleTester
from traceguard.evals.psi_calculator import PSICalculator
from traceguard.monitors.deadlock import AgentCycleException, SwarmCycleDetector, SwarmDeadlockError


# =====================================================================
# 1. Population Stability Index (PSI) Tests
# =====================================================================

class TestPSICalculator:
    """Tests for PSICalculator and non-parametric bootstrap confidence intervals."""

    def test_identical_distributions_yields_stable_psi(self):
        rng = np.random.default_rng(42)
        baseline = rng.normal(loc=100.0, scale=15.0, size=500).tolist()
        current = rng.normal(loc=100.0, scale=15.0, size=500).tolist()

        calc = PSICalculator(num_bins=10, num_bootstrap=100, random_state=42)
        summary = calc.calculate_psi(baseline, current)

        assert summary.psi < 0.10
        assert summary.status == "STABLE"
        assert summary.is_drift_detected is False
        assert summary.ci_lower <= summary.ci_upper

    def test_severe_distribution_shift_flags_significant_drift(self):
        rng = np.random.default_rng(42)
        # Shift mean from 100 to 140 (severe token inflation drift)
        baseline = rng.normal(loc=100.0, scale=15.0, size=500).tolist()
        current = rng.normal(loc=140.0, scale=15.0, size=500).tolist()

        calc = PSICalculator(num_bins=10, num_bootstrap=100, random_state=42)
        summary = calc.calculate_psi(baseline, current)

        assert summary.psi >= 0.25
        assert summary.status == "SIGNIFICANT_DRIFT"
        assert summary.is_drift_detected is True

    def test_bootstrap_confidence_interval_bounds(self):
        rng = np.random.default_rng(99)
        baseline = rng.uniform(0.0, 1.0, size=300).tolist()
        current = rng.uniform(0.1, 1.1, size=300).tolist()

        calc = PSICalculator(num_bins=8, num_bootstrap=150, random_state=99)
        summary = calc.calculate_psi(baseline, current, confidence_level=0.95)

        assert summary.ci_lower >= 0.0
        assert summary.ci_upper >= summary.ci_lower

    def test_empty_payload_raises_value_error(self):
        calc = PSICalculator()
        with pytest.raises(ValueError, match="cannot be empty"):
            calc.calculate_psi([], [1.0, 2.0])


# =====================================================================
# 2. Two-Sample Kolmogorov-Smirnov (KS) Tests
# =====================================================================

class TestKolmogorovSmirnovTester:
    """Tests for KSTwoSampleTester on 1D continuous cosine distance distributions."""

    def test_continuous_null_distribution_retained(self):
        rng = np.random.default_rng(123)
        # Baseline cosine similarity scores drawn from Beta(8, 2)
        baseline = rng.beta(a=8, b=2, size=400).tolist()
        current = rng.beta(a=8, b=2, size=400).tolist()

        tester = KSTwoSampleTester(alpha=0.05)
        result = tester.test(baseline, current)

        assert result.p_value >= 0.05
        assert result.is_drift_detected is False
        assert "Retain H0" in result.description

    def test_continuous_distribution_shift_rejected(self):
        rng = np.random.default_rng(123)
        # Shifted cosine similarity: degraded model Beta(5, 5) vs baseline Beta(8, 2)
        baseline = rng.beta(a=8, b=2, size=400).tolist()
        degraded = rng.beta(a=5, b=5, size=400).tolist()

        tester = KSTwoSampleTester(alpha=0.05)
        result = tester.test(baseline, degraded)

        assert result.p_value < 0.001
        assert result.statistic > 0.20
        assert result.is_drift_detected is True
        assert "Reject H0" in result.description


# =====================================================================
# 3. Statistical Drift Engine PR Validation Tests
# =====================================================================

class TestStatisticalDriftEngine:
    """Tests for PR gating engine combining KS, PSI, and Bootstrap Mean tests."""

    def test_safe_pr_candidate_passes_validation(self):
        rng = np.random.default_rng(42)
        baseline = rng.normal(0.85, 0.05, size=200).tolist()
        candidate = rng.normal(0.85, 0.05, size=200).tolist()

        engine = StatisticalDriftEngine(historical_baseline=baseline)
        assert engine.validate_pr_candidate(candidate) is True

    def test_degraded_pr_candidate_fails_validation(self):
        rng = np.random.default_rng(42)
        baseline = rng.normal(0.85, 0.05, size=200).tolist()
        degraded_candidate = rng.normal(0.60, 0.12, size=200).tolist()

        engine = StatisticalDriftEngine(historical_baseline=baseline)
        assert engine.validate_pr_candidate(degraded_candidate) is False


# =====================================================================
# 4. Agent Cycle Detection & AgentCycleException Tests
# =====================================================================

class TestAgentCycleException:
    """Tests for infinite agent tool and delegation loop detection."""

    def test_agent_cycle_exception_inheritance(self):
        """Verifies AgentCycleException is a subclass of SwarmDeadlockError for backward compatibility."""
        assert issubclass(AgentCycleException, SwarmDeadlockError)

    def test_recursive_tool_loop_raises_agent_cycle_exception(self):
        detector = SwarmCycleDetector()
        # Agent orchestrator delegates to SearchAgent -> CalculatorAgent -> CodeAgent -> SearchAgent
        detector.log_delegation("Orchestrator", "SearchAgent")
        detector.log_delegation("SearchAgent", "CalculatorAgent")
        detector.log_delegation("CalculatorAgent", "CodeAgent")

        # Closing cycle raises AgentCycleException
        with pytest.raises(AgentCycleException, match="Circular delegation loop detected"):
            detector.log_delegation("CodeAgent", "SearchAgent")

    def test_self_recursive_tool_call_raises_immediately(self):
        detector = SwarmCycleDetector()
        with pytest.raises(AgentCycleException):
            detector.log_delegation("SelfLoopAgent", "SelfLoopAgent")
