from typing import List, Optional
from pydantic import BaseModel
from .extractor import TraceData

class AnomalyResult(BaseModel):
    is_anomalous: bool
    reason: Optional[str] = None

class BaseRule:
    def evaluate(self, trace: TraceData) -> AnomalyResult:
        raise NotImplementedError()

class ErrorRule(BaseRule):
    """Flags traces that contain any span with an ERROR status code."""
    def evaluate(self, trace: TraceData) -> AnomalyResult:
        for span in trace.spans:
            if span.status_code == 'ERROR':
                # Attempt to extract Limit Cycle or other specific errors if they were logged as attributes
                return AnomalyResult(is_anomalous=True, reason=f"Span '{span.name}' threw an error: Limit Cycle detected." if "Limit Cycle" in str(span.attributes.get("output.result", "")) or "Limit Cycle" in str(span.attributes.get("exception.message", "")) else f"Span '{span.name}' threw an error.")
        return AnomalyResult(is_anomalous=False)

class LatencyRule(BaseRule):
    """Flags traces where total execution time exceeds a threshold."""
    def __init__(self, max_latency_ns: int):
        self.max_latency_ns = max_latency_ns
        
    def evaluate(self, trace: TraceData) -> AnomalyResult:
        if not trace.spans:
            return AnomalyResult(is_anomalous=False)
            
        start_time = min(s.start_time for s in trace.spans)
        end_time = max(s.end_time for s in trace.spans)
        latency = end_time - start_time
        
        if latency > self.max_latency_ns:
            return AnomalyResult(is_anomalous=True, reason=f"Latency {latency}ns exceeded threshold {self.max_latency_ns}ns.")
            
        return AnomalyResult(is_anomalous=False)

class AnomalyEngine:
    def __init__(self, rules: List[BaseRule]):
        self.rules = rules
        
    def check_trace(self, trace: TraceData) -> AnomalyResult:
        """Returns the first anomaly found, or False if none."""
        for rule in self.rules:
            result = rule.evaluate(trace)
            if result.is_anomalous:
                return result
        return AnomalyResult(is_anomalous=False)
