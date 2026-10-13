"""
tests/test_property_based.py
----------------------------
Property-based testing suite using Hypothesis for TraceGuard.
Verifies invariants for schema validation, payload serialization,
path traversal sanitization, credential redaction, and swarm cycle detection.
Addresses Batch 1, Task 1.3 requirements.
"""

import json
from hypothesis import given, settings, strategies as st
import pytest

from traceguard.firewall import (
    FirewallMutationContext,
    _serialize_to_json,
    check_indirect_prompt_injection,
    TraceGuardFirewallBlock,
)
from traceguard.decorators import _serialize_to_json as dec_serialize_to_json
from traceguard.monitors.deadlock import SwarmCycleDetector, SwarmDeadlockError
from traceguard.finops.budget import AdaptiveBudgetMonitor


# =====================================================================
# Hypothesis Strategies
# =====================================================================

json_primitives = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-1_000_000, max_value=1_000_000)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100)
)

json_values = st.recursive(
    json_primitives,
    lambda children: st.lists(children, max_size=10)
    | st.dictionaries(
        st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=20),
        children,
        max_size=10,
    ),
    max_leaves=25,
)


# =====================================================================
# 1. Serialization Invariant Properties
# =====================================================================

class TestSerializationProperties:
    """Property-based verification of JSON serialization invariants."""

    @given(val=json_values)
    @settings(max_examples=50)
    def test_json_serialization_roundtrip_invariant(self, val):
        """Any valid JSON structure serializes and parses back to the original value."""
        serialized = _serialize_to_json(val)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed == val

    @given(val=json_values)
    @settings(max_examples=50)
    def test_decorator_serializer_parity(self, val):
        """Decorator serializer produces identical output to firewall serializer."""
        s1 = _serialize_to_json(val)
        s2 = dec_serialize_to_json(val)
        assert s1 == s2

    @given(f=st.floats(allow_nan=True, allow_infinity=True))
    @settings(max_examples=30)
    def test_serializer_never_crashes_on_extreme_floats(self, f):
        """Serialization never raises an unhandled exception on NaN or Infinity."""
        res = _serialize_to_json(f)
        assert isinstance(res, str)


# =====================================================================
# 2. Firewall Path & Credential Mutation Properties
# =====================================================================

class TestFirewallMutationProperties:
    """Property-based tests for Firewall parameter mutation and sanitization."""

    @given(
        prefix=st.text(max_size=20),
        suffix=st.text(max_size=20),
        dot_count=st.integers(min_value=1, max_value=8),
    )
    @settings(max_examples=50)
    def test_path_sanitization_removes_all_traversals(self, prefix, suffix, dot_count):
        """Sanitized path must never contain '../' or '..\\\\' regardless of insertion patterns."""
        traversal = "../" * dot_count
        raw_path = f"{prefix}{traversal}{suffix}"
        ctx = FirewallMutationContext({"path": raw_path})
        ctx.sanitize_path("path")

        sanitized = ctx.kwargs["path"]
        assert "../" not in sanitized
        assert "..\\" not in sanitized

    @given(raw_path=st.text(max_size=100))
    @settings(max_examples=40)
    def test_path_sanitization_idempotence(self, raw_path):
        """Calling sanitize_path multiple times produces identical results."""
        ctx1 = FirewallMutationContext({"path": raw_path})
        ctx1.sanitize_path("path")
        first_pass = ctx1.kwargs["path"]

        ctx2 = FirewallMutationContext({"path": first_pass})
        ctx2.sanitize_path("path")
        second_pass = ctx2.kwargs["path"]

        assert first_pass == second_pass

    @given(
        key_name=st.sampled_from(["password", "secret", "key", "token", "PASSWORD", "Token"]),
        delimiter=st.sampled_from([":", "=", " : ", " = "]),
        quote=st.sampled_from(['"', "'"]),
        secret_val=st.text(min_size=4, max_size=30).filter(lambda s: '"' not in s and "'" not in s and ":" not in s),
    )
    @settings(max_examples=40)
    def test_credential_redaction_never_leaks_secret(self, key_name, delimiter, quote, secret_val):
        """Secret values matching sensitive key regex patterns must never appear in cleartext."""
        raw_str = f"config_{key_name}{delimiter}{quote}{secret_val}{quote}"
        ctx = FirewallMutationContext({"payload": raw_str})
        ctx.redact_credentials("payload")

        redacted = ctx.kwargs["payload"]
        assert secret_val not in redacted
        assert "***REDACTED***" in redacted


# =====================================================================
# 3. Prompt Injection Defense Properties
# =====================================================================

class TestPromptInjectionProperties:
    """Property-based verification of indirect prompt injection detection."""

    @given(
        prefix=st.text(max_size=30),
        suffix=st.text(max_size=30),
        trigger=st.sampled_from([
            "ignore previous instructions",
            "IGNORE PREVIOUS INSTRUCTIONS",
            "Ignore Previous Instructions",
            "system override",
            "SYSTEM OVERRIDE",
        ]),
    )
    @settings(max_examples=30)
    def test_indirect_prompt_injection_always_intercepted(self, prefix, suffix, trigger):
        """Any payload containing injection triggers raises TraceGuardFirewallBlock."""
        payload = f"{prefix} {trigger} {suffix}"
        with pytest.raises(TraceGuardFirewallBlock):
            check_indirect_prompt_injection(payload)


# =====================================================================
# 4. Swarm Cycle Detection Properties
# =====================================================================

class TestSwarmCycleDetectorProperties:
    """Property-based tests for swarm delegation graph cycle detection."""

    @given(num_agents=st.integers(min_value=2, max_value=12))
    @settings(max_examples=25)
    def test_acyclic_linear_chains_never_raise_deadlock(self, num_agents):
        """A linear delegation chain A1 -> A2 -> ... -> An has no cycles and never deadlocks."""
        detector = SwarmCycleDetector()
        agents = [f"agent_{i}" for i in range(num_agents)]

        for i in range(len(agents) - 1):
            detector.log_delegation(agents[i], agents[i + 1])

        # None of the resolutions should encounter a cycle
        for i in range(len(agents) - 1):
            detector.resolve_delegation(agents[i], agents[i + 1])

    @given(chain_len=st.integers(min_value=2, max_value=8))
    @settings(max_examples=25)
    def test_closed_loops_always_raise_deadlock(self, chain_len):
        """Closing a cycle An -> A0 must deterministically raise SwarmDeadlockError."""
        detector = SwarmCycleDetector()
        agents = [f"node_{i}" for i in range(chain_len)]

        # Form chain: 0 -> 1 -> ... -> chain_len - 1
        for i in range(chain_len - 1):
            detector.log_delegation(agents[i], agents[i + 1])

        # Closing back to node 0 triggers deadlock
        with pytest.raises(SwarmDeadlockError):
            detector.log_delegation(agents[-1], agents[0])


# =====================================================================
# 5. Adaptive Budget Anomaly Properties
# =====================================================================

class TestAdaptiveBudgetProperties:
    """Property-based tests for adaptive budget statistical thresholding."""

    @given(
        costs=st.lists(
            st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=4,
        ),
        candidate_cost=st.floats(min_value=1000.0, max_value=100_000.0),
    )
    @settings(max_examples=25)
    def test_fewer_than_five_samples_never_flags_anomaly(self, costs, candidate_cost):
        """Statistical baseline requirement of >= 5 samples is strictly preserved."""
        monitor = AdaptiveBudgetMonitor()
        task = "test_prop_task"
        for c in costs:
            monitor.log_historical_cost(task, c)

        # Even a cost 1000x higher never raises BudgetExceededError when samples < 5
        monitor.check_runtime_cost(task, candidate_cost)
