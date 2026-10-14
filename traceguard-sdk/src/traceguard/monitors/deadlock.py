from typing import Dict, Set

class SwarmDeadlockError(Exception):
    pass


class AgentCycleException(SwarmDeadlockError):
    """Raised when an agent enters a circular delegation or recursive tool execution loop."""
    pass

class SwarmCycleDetector:
    """
    GPT Phase 25: Real-time Swarm Deadlock Monitor.
    Detects Circular Delegation (e.g., Agent A -> B -> C -> A) using 
    cycle-detection on the live delegation graph, terminating the swarm 
    before it burns through tokens in an infinite loop.
    """
    def __init__(self):
        # Maps an agent to the set of agents it is currently waiting on
        self.delegation_graph: Dict[str, Set[str]] = {}
        
    def log_delegation(self, source_agent: str, target_agent: str):
        """Records that source_agent delegated a task to target_agent."""
        if source_agent not in self.delegation_graph:
            self.delegation_graph[source_agent] = set()
        self.delegation_graph[source_agent].add(target_agent)
        
        self.check_for_cycles()
        
    def resolve_delegation(self, source_agent: str, target_agent: str):
        """Records that target_agent returned control to source_agent."""
        if source_agent in self.delegation_graph and target_agent in self.delegation_graph[source_agent]:
            self.delegation_graph[source_agent].remove(target_agent)
            
    def check_for_cycles(self):
        """Runs Depth-First Search to detect circular waits."""
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in self.delegation_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    # Found a cycle
                    return True
                    
            recursion_stack.remove(node)
            return False
            
        for agent in list(self.delegation_graph.keys()):
            if agent not in visited:
                if dfs(agent):
                    raise AgentCycleException(
                        f"Circular delegation loop detected! The swarm has deadlocked. "
                        f"Current Wait Graph: {self.delegation_graph}"
                    )
