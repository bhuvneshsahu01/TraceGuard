"""
TraceGuard SDK - The Unified Agent CI & Eval Platform
"""

__version__ = "0.2.0"

from .decorators import observe, log_rag_context, guardrail, TraceGuardFirewallBlock
from .config import configure_traceguard
from . import drift
from . import guardrails
from .drift import (
    DriftMonitor,
    calculate_psi,
    ks_two_sample_test,
    chi2_homogeneity_test,
    mmd_permutation_test,
    benjamini_hochberg,
)
from .guardrails import (
    TraceGuardMiddleware,
    GuardrailConfig,
    PIIRedactor,
    PromptInjectionScanner,
    StreamingBuffer,
)

__all__ = [
    "observe",
    "configure_traceguard",
    "log_rag_context",
    "guardrail",
    "TraceGuardFirewallBlock",
    "drift",
    "guardrails",
    "DriftMonitor",
    "calculate_psi",
    "ks_two_sample_test",
    "chi2_homogeneity_test",
    "mmd_permutation_test",
    "benjamini_hochberg",
    "TraceGuardMiddleware",
    "GuardrailConfig",
    "PIIRedactor",
    "PromptInjectionScanner",
    "StreamingBuffer",
]
