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

class RepairRetryTracker:
    """Measures re-prompting frequency due to schema validation failures."""
    def __init__(self):
        self.retry_counts = {}
        
    def log_retry(self, tool_name: str):
        self.retry_counts[tool_name] = self.retry_counts.get(tool_name, 0) + 1
        
    def get_retry_frequency(self, tool_name: str) -> int:
        return self.retry_counts.get(tool_name, 0)
