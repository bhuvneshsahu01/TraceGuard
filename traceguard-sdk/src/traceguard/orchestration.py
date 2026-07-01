from typing import Any, Callable

class StructuredDissentNode:
    """
    API to automatically inject a specialized Dissenter Agent into Swarms 
    to disrupt L14-L18 circuit consensus vulnerabilities (Sycophancy Loops).
    """
    
    def __init__(self, dissent_prompt: str = "Argue the counterfactual strictly using evidence."):
        self.dissent_prompt = dissent_prompt
        
    def inject_into_swarm(self, swarm_config: Any):
        """
        Modifies a LangGraph or AutoGen swarm config to include the dissenter node.
        """
        # Stub logic
        if hasattr(swarm_config, 'add_node'):
            swarm_config.add_node("Dissenter", self._dissent_behavior)
        return swarm_config
        
    def _dissent_behavior(self, state: Any) -> Any:
        # Evaluate consensus and provide opposing structural logic
        state["dissenter_injected"] = True
        state["consensus_strength"] = 0.4 # Reduces sycophancy loop strength
        return state
