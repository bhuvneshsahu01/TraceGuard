import uuid

class IdentityVerifier:
    """
    Enforces ephemeral, context-bound workload identities at the routing layer 
    to prevent Inter-Agent Trust Escalation.
    """
    def __init__(self):
        self.active_identities = {}
        
    def issue_identity(self, agent_role: str, context_scope: str) -> str:
        """Issues an ephemeral token bound to a specific context."""
        token = f"eph_{uuid.uuid4().hex}"
        self.active_identities[token] = {
            "role": agent_role,
            "scope": context_scope
        }
        return token
        
    def verify_action(self, token: str, requested_action: str, requested_scope: str) -> bool:
        """Verifies if the agent is authorized for the action within its ephemeral scope."""
        if token not in self.active_identities:
            return False
            
        identity = self.active_identities[token]
        if identity["scope"] != requested_scope:
            return False
            
        return True
