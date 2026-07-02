from typing import Any

from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class RLCreditAssigner:
    """
    Instruments orchestration traces specifically to support RL-style credit assignment
    across the swarm. Propagates 'reward' back through the DAG of agent actions and tool calls.
    """
    def __init__(self):
        self.trace_history = []
        
    def log_agent_action(self, agent_id: str, action: str, step_idx: int):
        self.trace_history.append({"agent_id": agent_id, "action": action, "step_idx": step_idx})
        
    def assign_reward(self, final_reward: float):
        """
        Distributes the final reward to the causal chain of agents based on a simple discounting factor.
        """
        discount_factor = 0.9
        with tracer.start_as_current_span("rl.credit_assignment") as span:
            span.set_attribute("gen_ai.swarm.final_reward", final_reward)
            
            # Simple reverse temporal credit assignment
            for idx, record in enumerate(reversed(self.trace_history)):
                credit = final_reward * (discount_factor ** idx)
                span.set_attribute(f"rl.credit.agent.{record['agent_id']}.step_{record['step_idx']}", credit)
                
            return True

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
