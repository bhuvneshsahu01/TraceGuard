from typing import Dict, Any, List
from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class TrajectoryEvaluator:
    """
    Evaluates long-horizon, multi-step agent trajectories. 
    Moves beyond surface-level answer grading to step-wise, white-box verification.
    """
    def __init__(self):
        self.metrics = {
            "plan_quality": 0.0,
            "adherence": 0.0,
            "tool_accuracy": 0.0,
            "deterministic_outcome": 0.0
        }
        
    def evaluate_nested_span(self, span_data: Dict[str, Any]) -> float:
        """
        White-Box Verification: Asserts against the specific contents of a nested span 
        (e.g., verifying if the correct DB rows were retrieved, regardless of the final answer).
        """
        span_kind = span_data.get("kind", "")
        if span_kind == "AGENT":
            # Stub: Grade reasoning
            return 0.9
        elif span_kind == "TOOL":
            # Stub: Grade tool usage accuracy
            return 1.0
        return 0.5
        
    def score_trajectory(self, trace_tree: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analyzes the full execution history (trace_tree) and assigns granular scores.
        """
        with tracer.start_as_current_span("eval.trajectory") as span:
            # 1. Plan Quality
            plan_span = next((s for s in trace_tree if s.get("name") == "PlanGeneration"), None)
            if plan_span:
                self.metrics["plan_quality"] = self.evaluate_nested_span(plan_span)
                
            # 2. Tool Accuracy
            tool_spans = [s for s in trace_tree if s.get("kind") == "TOOL"]
            if tool_spans:
                scores = [self.evaluate_nested_span(s) for s in tool_spans]
                self.metrics["tool_accuracy"] = sum(scores) / len(scores)
                
            # 3. Adherence (Did it follow the plan?)
            self.metrics["adherence"] = 0.85 # Stub
            
            # 4. Final Deterministic Outcome
            self.metrics["deterministic_outcome"] = 1.0 # Stub
            
            span.set_attribute("eval.trajectory.plan_quality", self.metrics["plan_quality"])
            span.set_attribute("eval.trajectory.adherence", self.metrics["adherence"])
            span.set_attribute("eval.trajectory.tool_accuracy", self.metrics["tool_accuracy"])
            
            return self.metrics
