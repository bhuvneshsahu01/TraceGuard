import json
import os
from typing import Dict, Any

class AgentLifecycleManager:
    """
    Primitives for the Discontinuous Autonomous Lifecycle.
    Allows long-horizon agents to serialize state, sleep, and rehydrate context from disk,
    circumventing the accumulation of continuous context amnesia.
    """
    
    def __init__(self, storage_dir: str = ".agent_states"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
            
    def serialize_and_sleep(self, session_id: str, state: Dict[str, Any]):
        """
        Persists the agent's current context to disk.
        """
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        with open(file_path, 'w') as f:
            json.dump(state, f)
            
    def rehydrate_context(self, session_id: str) -> Dict[str, Any]:
        """
        Loads the agent's context from disk, restoring a clean state without amnesia.
        """
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
