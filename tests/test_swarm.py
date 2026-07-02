import pytest
from traceguard.monitors.deadlock import SwarmCycleDetector, SwarmDeadlockError

def test_swarm_cycle_detection():
    detector = SwarmCycleDetector()
    
    detector.log_delegation("AgentA", "AgentB")
    detector.log_delegation("AgentB", "AgentC")
    
    # Resolving works fine
    detector.resolve_delegation("AgentB", "AgentC")
    
    # Adding new edges
    detector.log_delegation("AgentB", "AgentD")
    
    # Introduce cycle A -> B -> D -> A
    with pytest.raises(SwarmDeadlockError):
        detector.log_delegation("AgentD", "AgentA")
