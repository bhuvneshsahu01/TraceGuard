from typing import Dict, Any

class FinOpsMetrics:
    """Tracks SLIs for Next-Gen FinOps."""
    
    @staticmethod
    def calculate_tool_roi(net_business_benefit: float, total_token_cost: float, infrastructure_overhead: float) -> float:
        """Calculates Return on Investment per tool."""
        total_investment = total_token_cost + infrastructure_overhead
        if total_investment == 0:
            return 0.0
        return net_business_benefit / total_investment
        
    @staticmethod
    def calculate_cost_per_resolution(spans: list) -> float:
        """Amortize the full price of a completed task across the entire multi-step agent path."""
        total_cost = 0.0
        for span in spans:
            cost = span.get("attributes", {}).get("financial.cost_usd", 0.0)
            if cost:
                total_cost += cost
        return total_cost

class ToolROIOptimizer:
    """Tracks and dynamically tests tool ROI using EMA and A/B Testing."""
    def __init__(self, ema_alpha: float = 0.1):
        self.tool_roi_ema: Dict[str, float] = {}
        self.ema_alpha = ema_alpha
        
    def update_roi(self, tool_name: str, new_roi: float):
        """Exponential Moving Average (EMA) for tool ROI drift detection."""
        if tool_name not in self.tool_roi_ema:
            self.tool_roi_ema[tool_name] = new_roi
        else:
            old_ema = self.tool_roi_ema[tool_name]
            self.tool_roi_ema[tool_name] = (self.ema_alpha * new_roi) + ((1 - self.ema_alpha) * old_ema)
            
    def ab_test_route(self, tool_variant_a: str, tool_variant_b: str) -> str:
        """
        Live A/B Testing: Dynamically allocates traffic to the tool with the 
        highest real-time EMA ROI score. If missing, randomly splits traffic for exploration.
        """
        import random
        roi_a = self.tool_roi_ema.get(tool_variant_a)
        roi_b = self.tool_roi_ema.get(tool_variant_b)
        
        if roi_a is None or roi_b is None:
            return tool_variant_a if random.random() > 0.5 else tool_variant_b
            
        return tool_variant_a if roi_a >= roi_b else tool_variant_b

class RepairRetryTracker:
    """Measures re-prompting frequency due to schema validation failures."""
    def __init__(self):
        self.retry_counts = {}
        
    def log_retry(self, tool_name: str):
        self.retry_counts[tool_name] = self.retry_counts.get(tool_name, 0) + 1
        
    def get_retry_frequency(self, tool_name: str) -> int:
        return self.retry_counts.get(tool_name, 0)
