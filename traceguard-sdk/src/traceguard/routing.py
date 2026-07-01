from typing import Dict, Any
from .provenance import MultimodalProvenanceTracker

class IntentAwareRouter:
    """
    Combines the MultimodalProvenanceTracker ledger with content-sensitive routing algorithms.
    If a document's provenance trust level is low, it dynamically routes the request 
    through a more rigid parsing layer to neutralize Indirect Document Injections.
    """
    def __init__(self, provenance_tracker: MultimodalProvenanceTracker):
        self.provenance = provenance_tracker
        
    def route_request(self, request_payload: Dict[str, Any], origin_source: str) -> str:
        """
        Determines the routing path based on content intent and provenance trust score.
        """
        trust_level = self.provenance.get_trust_level(origin_source)
        
        # If trust is low (e.g., raw web scrape), route to a rigid, highly constrained parsing model
        if trust_level < 0.5:
            return "ROUTE_RIGID_PARSER"
            
        # If highly trusted (e.g., internal verified DB), route to standard execution path
        return "ROUTE_STANDARD_EXECUTION"
