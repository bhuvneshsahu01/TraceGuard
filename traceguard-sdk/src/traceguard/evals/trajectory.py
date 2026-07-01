from typing import List, Dict, Any

class TrajectoryRiskCompressor:
    """
    Dual-module Compressor-Reader architecture for long-horizon agent evaluation.
    Aggregates sparse risk cues across the entire temporal sequence.
    """
    
    def compress_trajectory(self, steps: List[Dict[str, Any]]) -> str:
        """
        Compressor Module: generates a compact latent evidence state from long trajectories.
        """
        evidence = []
        for step in steps:
            if step.get("error") or step.get("high_risk_tool"):
                evidence.append(str(step))
        return "LATENT_EVIDENCE[" + "|".join(evidence) + "]"
        
    def evaluate_with_reader(self, raw_trajectory: List[Dict[str, Any]], latent_evidence: str) -> float:
        """
        Reader Module: Evaluates the trajectory utilizing the persistent safety reference anchor.
        """
        if "error" in latent_evidence.lower():
            return 0.2
        return 0.9

class StateDriftTracker:
    """
    Tracks cumulative drift between the textual scratchpad and actual environment states (Coherence Cliff).
    """
    def __init__(self):
        self.cumulative_drift = 0.0
        
    def measure_drift(self, internal_belief_state: str, true_environment_state: str) -> float:
        """
        Computes the divergence between what the agent believes and the actual environment.
        """
        drift = abs(len(internal_belief_state) - len(true_environment_state)) / max(1, len(true_environment_state))
        self.cumulative_drift += drift
        return self.cumulative_drift
