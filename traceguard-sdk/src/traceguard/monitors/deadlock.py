from typing import List, Set

class DeadlockDetector:
    """
    Detects circular logic loops and flat topologies lacking hierarchical arbitration.
    """
    def __init__(self):
        self.dependency_graph = {}
        
    def add_edge(self, agent_from: str, agent_to: str):
        if agent_from not in self.dependency_graph:
            self.dependency_graph[agent_from] = []
        self.dependency_graph[agent_from].append(agent_to)
        
    def _has_cycle(self, node: str, visited: Set[str], stack: Set[str]) -> bool:
        visited.add(node)
        stack.add(node)
        
        for neighbor in self.dependency_graph.get(node, []):
            if neighbor not in visited:
                if self._has_cycle(neighbor, visited, stack):
                    return True
            elif neighbor in stack:
                return True
                
        stack.remove(node)
        return False

    def check_for_deadlock(self) -> bool:
        """
        Returns True if a circular dependency (Hallucination Deadlock) is found.
        """
        visited = set()
        stack = set()
        for node in self.dependency_graph:
            if node not in visited:
                if self._has_cycle(node, visited, stack):
                    return True
        return False
