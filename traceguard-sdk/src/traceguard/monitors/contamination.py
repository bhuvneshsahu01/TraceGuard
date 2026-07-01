from typing import List, Dict, Any

def string_similarity_stub(str1: str, str2: str) -> float:
    """Stub for cosine similarity between two string embeddings."""
    return 0.9 if str1 == str2 else 0.5

class ContaminationMonitor:
    """
    Heuristic monitor for 'semantic drift across spans'.
    Detects if the semantic intent of the memory state wildly diverges
    as it is passed across multiple parallel agents.
    """
    def __init__(self, drift_threshold: float = 0.4):
        self.drift_threshold = drift_threshold
        self.state_history: List[Dict[str, Any]] = []
        
    def log_state_update(self, agent_id: str, new_memory_state: str):
        self.state_history.append({
            "agent_id": agent_id,
            "state": new_memory_state
        })
        
    def detect_contamination(self) -> bool:
        """
        Returns True if semantic drift exceeds the threshold, implying 
        context contamination or hallucination propagation.
        """
        if len(self.state_history) < 2:
            return False
            
        original_state = self.state_history[0]["state"]
        current_state = self.state_history[-1]["state"]
        
        similarity = string_similarity_stub(original_state, current_state)
        
        # If similarity drops too low, the core intent has been lost/contaminated
        return similarity < self.drift_threshold
