from typing import Dict, List
from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class SemanticDLPEngine:
    """
    Evaluates semantic similarity between outbound payloads and known sensitive data signatures
    to prevent data exfiltration.
    """
    def __init__(self, sensitivity_threshold: float = 0.85):
        self.sensitivity_threshold = sensitivity_threshold
        
    def evaluate_payload(self, outbound_data: str) -> bool:
        """
        Returns True if the payload is safe, False if it matches a sensitive signature.
        """
        # Stub: check for simple simulated keywords or run embedding cosine similarity
        sensitive_keywords = ["SECRET_API_KEY", "INTERNAL_MEMO_CONFIDENTIAL"]
        for keyword in sensitive_keywords:
            if keyword.lower() in outbound_data.lower():
                return False
        return True

    def check_differential_outlier(self, inbound_context_tokens: int, outbound_tool_tokens: int) -> bool:
        """
        Detects RAG-poisoning data exfiltration symptoms.
        If an agent receives a tiny user prompt but attempts to send a massive 
        payload in an outbound API call, it's a differential outlier.
        Returns True if safe, False if an outlier.
        """
        # If the outbound payload is 50x larger than the inbound context, flag it
        if inbound_context_tokens > 0 and (outbound_tool_tokens / inbound_context_tokens) > 50.0:
            with tracer.start_as_current_span("exfil.differential_outlier") as span:
                span.set_attribute("traceguard.exfil.inbound_tokens", inbound_context_tokens)
                span.set_attribute("traceguard.exfil.outbound_tokens", outbound_tool_tokens)
                span.set_attribute("traceguard.block_reason", "Differential_Outlier_Exfil")
            return False
        return True

class DataFlowTracker:
    """
    Tracks agent handoffs and tool interactions across the Swarm Graph to detect 
    anomalous data exfiltration paths.
    """
    def __init__(self):
        self.handoff_graph: List[Dict[str, str]] = []
        
    def log_handoff(self, source_agent: str, target_agent: str, payload_summary: str):
        with tracer.start_as_current_span("agent.handoff") as span:
            span.set_attribute("gen_ai.agent.handoff.source", source_agent)
            span.set_attribute("gen_ai.agent.handoff.target", target_agent)
            self.handoff_graph.append({
                "source": source_agent,
                "target": target_agent,
                "payload": payload_summary
            })
            
    def analyze_flow_for_exfil(self) -> bool:
        """
        Checks if an agent that read sensitive data (e.g. Internal DB) passed it 
        to an agent executing a public outbound action (e.g. Email).
        """
        # Stub logic
        for edge in self.handoff_graph:
            if "internal_db" in edge["source"].lower() and "email" in edge["target"].lower():
                return True # Exfil detected
        return False
