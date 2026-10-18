import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class SwarmAnalyzer:
    """
    Analyzes the structure of multi-agent interactions to detect
    swarm-specific failure modes like Circular Delegation and Echo Chambers.
    """
    
    def __init__(self, spans_data: List[dict]):
        self.spans = spans_data
        # spans_data should be a list of dictionaries with keys:
        # span_id, trace_id, parent_span_id, name, agent_id, parent_agent_id
        
    def _build_agent_graph(self) -> Dict[str, Set[str]]:
        """Build a directed graph of agent delegations."""
        graph: Dict[str, Set[str]] = {}
        for span in self.spans:
            agent = span.get("agent_id")
            parent_agent = span.get("parent_agent_id")
            if agent and parent_agent and agent != parent_agent:
                if parent_agent not in graph:
                    graph[parent_agent] = set()
                graph[parent_agent].add(agent)
                if agent not in graph:
                    graph[agent] = set()
        return graph

    def detect_circular_delegation(self) -> List[List[str]]:
        """
        Find cycles in the agent delegation graph using DFS.
        Returns a list of cycles (lists of agent IDs).
        """
        graph = self._build_agent_graph()
        visited: Set[str] = set()
        path: List[str] = []
        cycles: List[List[str]] = []
        
        def dfs(node):
            if node in path:
                # Cycle detected
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            path.pop()

        for agent in graph:
            if agent not in visited:
                dfs(agent)
                
        return cycles

    def detect_echo_chamber(self) -> bool:
        """
        Detects if multiple agents are recursively validating identical responses.
        (Heuristic placeholder: checking if same exact agent loop occurs frequently).
        """
        cycles = self.detect_circular_delegation()
        # If there's a tight cycle of 2 agents, it could be an echo chamber.
        # A more advanced version would diff the LLM text outputs.
        for cycle in cycles:
            if len(cycle) == 3: # A -> B -> A
                logger.warning(f"Potential Echo Chamber detected between {cycle[0]} and {cycle[1]}")
                return True
        return False
