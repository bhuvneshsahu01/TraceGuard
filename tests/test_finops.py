import pytest
from traceguard.finops.budget import AdaptiveBudgetMonitor, BudgetExceededError

def test_adaptive_budget():
    monitor = AdaptiveBudgetMonitor()
    monitor.log_historical_cost("test", 1.0)
    monitor.log_historical_cost("test", 1.1)
    monitor.log_historical_cost("test", 0.9)
    monitor.log_historical_cost("test", 1.0)
    monitor.log_historical_cost("test", 1.05)
    
    # Should not raise
    monitor.check_runtime_cost("test", 1.15)
    
    # Should raise (way out of 95% CI)
    with pytest.raises(BudgetExceededError):
        monitor.check_runtime_cost("test", 5.0)


