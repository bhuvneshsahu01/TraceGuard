from typing import Optional, Dict, Any
from opentelemetry import trace
from .privacy import RealTimeRedactionEngine, ExternalStorageReference

class DualLayerTelemetry:
    """
    Harmonizes OpenInference's agentic granularity with OTel GenAI SIG standards.
    """
    def __init__(self):
        self.tracer = trace.get_tracer("traceguard.gen_ai")
        self.redaction_engine = RealTimeRedactionEngine()
        self.secure_storage = ExternalStorageReference()
        
    def start_root_span(self, task_name: str, attributes: Dict[str, Any] = None):
        """Starts the overall user task span."""
        return self.tracer.start_as_current_span(
            task_name, 
            attributes={"openinference.span.kind": "CHAIN", **(attributes or {})}
        )
        
    def start_internal_span(self, agent_name: str, span_kind: str = "AGENT", attributes: Dict[str, Any] = None):
        """Starts an internal reasoning/routing span."""
        return self.tracer.start_as_current_span(
            agent_name, 
            attributes={"openinference.span.kind": span_kind, **(attributes or {})}
        )
        
    def start_client_span(self, model_name: str, system_prompt: str, is_compliant_env: bool = False):
        """
        Starts an outbound LLM call span, mapped to `gen_ai.*` namespace.
        Applies redaction automatically.
        """
        span = self.tracer.start_as_current_span(
            f"LLM Call: {model_name}",
            attributes={"openinference.span.kind": "LLM", "gen_ai.system": model_name}
        )
        
        if is_compliant_env:
            # High compliance: store unredacted externally, log reference
            ref_url = self.secure_storage.store_and_reference(system_prompt, str(span.get_span_context().span_id))
            span.set_attribute("gen_ai.prompt.reference", ref_url)
        else:
            # Standard compliance: inline redaction
            safe_prompt = self.redaction_engine.redact(system_prompt)
            span.set_attribute("gen_ai.prompt", safe_prompt)
            
        return span

    def track_fallback(self, original_span_name: str, fallback_span_name: str, error: Exception):
        """Explicitly tracks complex routing fallbacks."""
        span = self.tracer.start_as_current_span(f"Fallback: {fallback_span_name}")
        span.set_attribute("traceguard.fallback.from", original_span_name)
        span.set_attribute("traceguard.fallback.reason", str(error))
        return span
