from typing import List
import statistics
from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class BudgetExceededError(Exception):
    """Raised when a run breaches the historical 95% Confidence Interval for token costs."""
    pass

class AdaptiveBudgetMonitor:
    """
    GPT Phase 26: Adaptive Budget Alarms.
    Automatically terminates expensive runaway processes (infinite loops) 
    by calculating the 95% Confidence Interval of historical costs.
    """
    def __init__(self):
        # Maps task_name -> List of historical cost values (USD)
        self.historical_costs: dict[str, List[float]] = {}
        
    def log_historical_cost(self, task_name: str, cost: float):
        if task_name not in self.historical_costs:
            self.historical_costs[task_name] = []
        self.historical_costs[task_name].append(cost)
        
    def _calculate_upper_bound(self, task_name: str) -> float:
        """Calculates the 95% CI upper bound for cost."""
        costs = self.historical_costs.get(task_name, [])
        if len(costs) < 5:
            return float('inf') # Not enough data to confidently terminate
            
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs) if len(costs) > 1 else 0.0
        # 95% CI upper bound approximation (mean + 1.96 * stdev)
        return mean + (1.96 * stdev)
        
    def check_runtime_cost(self, task_name: str, current_spend_usd: float):
        """
        Evaluates ongoing cost against historical bounds.
        Raises BudgetExceededError if breached.
        """
        upper_bound = self._calculate_upper_bound(task_name)
        
        if current_spend_usd > upper_bound:
            with tracer.start_as_current_span("finops.early_termination") as span:
                span.set_attribute("financial.cost_usd", current_spend_usd)
                span.set_attribute("financial.budget_limit_usd", upper_bound)
                span.set_attribute("traceguard.block_reason", "Adaptive_Budget_Exceeded")
                
            raise BudgetExceededError(
                f"Adaptive Early Termination: Current spend (${current_spend_usd:.4f}) "
                f"exceeds 95% CI historical upper bound (${upper_bound:.4f}) for task '{task_name}'."
            )
