from typing import List, Any, Dict
import json

def _hash_state(state: Any) -> str:
    """Helper to convert a state dict/list into a deterministic string hash."""
    try:
        return json.dumps(state, sort_keys=True)
    except Exception:
        return str(state)

def detect_limit_cycle(states: List[Any], min_cycle_length: int = 2) -> Dict[str, Any]:
    """
    Detects if the agent state has fallen into an infinite limit cycle (loop).
    Uses sequence exact matching for categorical/structural states.
    
    Returns:
        dict containing 'has_cycle' (bool) and 'cycle_length' (int)
    """
    if len(states) < min_cycle_length * 2:
        return {"has_cycle": False, "cycle_length": 0}
        
    # Convert states to a list of strings for easier comparison
    string_states = [_hash_state(s) for s in states]
    n = len(string_states)
    
    # Look for repeating sequences at the end of the state list
    for length in range(min_cycle_length, n // 2 + 1):
        # Compare the last 'length' elements with the 'length' elements before them
        seq1 = string_states[n - length:n]
        seq2 = string_states[n - 2*length:n - length]
        
        if seq1 == seq2:
            return {
                "has_cycle": True,
                "cycle_length": length
            }
            
    return {"has_cycle": False, "cycle_length": 0}
