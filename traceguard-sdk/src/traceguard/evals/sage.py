from typing import List, Dict, Any, Callable

class SageEvaluator:
    """
    Self-Assessing Gauge for Evaluators (Sage) Framework.
    Implements rational choice theory calibration for LLM-as-a-Judge.
    """
    
    def __init__(self, judge_model_callable: Callable[[str, str], float]):
        self.judge = judge_model_callable
        
    def intra_pair_instability(self, prompt: str, ans_A: str, ans_B: str) -> bool:
        """
        Measures local self-consistency and positional bias.
        Swaps presentation order to check for preference reversals.
        Returns True if the judge is unstable (reverses preference).
        """
        # Score A vs B
        score_AB = self.judge(prompt, f"Answer A: {ans_A}\\nAnswer B: {ans_B}")
        
        # Score B vs A
        score_BA = self.judge(prompt, f"Answer A: {ans_B}\\nAnswer B: {ans_A}")
        
        prefers_A_initially = score_AB > 0.5
        prefers_B_when_swapped = score_BA < 0.5
        
        return prefers_A_initially == (not prefers_B_when_swapped)

    def weak_total_order_violation(self, prompt: str, ans_A: str, ans_B: str, ans_C: str) -> bool:
        """
        Assesses global logical coherence (transitivity).
        If A > B and B > C, then A > C must hold.
        """
        A_gt_B = self.judge(prompt, f"A: {ans_A}\\nB: {ans_B}") > 0.5
        B_gt_C = self.judge(prompt, f"A: {ans_B}\\nB: {ans_C}") > 0.5
        A_gt_C = self.judge(prompt, f"A: {ans_A}\\nB: {ans_C}") > 0.5
        
        if A_gt_B and B_gt_C:
            return not A_gt_C
        return False

class MultiAgentConsensusPanel:
    """
    Structured debate panel invoked when a single judge exhibits Situational Preference (TOV failure).
    """
    def __init__(self, panel_members: List[Callable]):
        self.members = panel_members
        
    def evaluate(self, payload: Any) -> float:
        scores = [member(payload) for member in self.members]
        return sum(scores) / len(scores) if scores else 0.0
