from typing import Tuple, Dict, Any, Callable
from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class ConstructorAuditorTriad:
    """
    GPT Phase 24: Multi-Agent Debate Routine.
    An evaluation panel that spawns a Constructor to defend an output, 
    an Auditor to attack it, and a Judge to score the debate, neutralizing
    verbosity and positional biases.
    """
    def __init__(self, llm_callable: Callable[[str], str], judge_callable: Callable[[str, str], Tuple[float, float]]):
        self.llm = llm_callable
        self.judge = judge_callable
        
    def evaluate_with_debate(self, prompt: str, target_answer: str) -> Tuple[float, float]:
        """
        Runs the full Constructor/Auditor/Judge triad.
        Returns the calibrated (score, logprob_confidence) from the Judge.
        """
        with tracer.start_as_current_span("eval.debate.triad") as root_span:
            
            # 1. Constructor Thread
            with tracer.start_as_current_span("agent.debate.constructor") as const_span:
                const_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                constructor_argument = self.llm(f"Defend why this answer is correct for the prompt: '{prompt}'. Answer: '{target_answer}'")
                const_span.set_attribute("gen_ai.completion", constructor_argument)
                
            # 2. Auditor Thread
            with tracer.start_as_current_span("agent.debate.auditor") as aud_span:
                aud_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                auditor_argument = self.llm(f"Critique and attack why this answer is flawed for the prompt: '{prompt}'. Answer: '{target_answer}'")
                aud_span.set_attribute("gen_ai.completion", auditor_argument)
                
            # 3. Judge Thread
            with tracer.start_as_current_span("agent.debate.judge_score") as judge_span:
                judge_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                
                debate_context = f"Constructor: {constructor_argument}\n\nAuditor: {auditor_argument}"
                
                # The judge resolves the debate
                score, logprob = self.judge(prompt, debate_context)
                
                judge_span.set_attribute("traceguard.eval.score", score)
                judge_span.set_attribute("traceguard.eval.logprob", logprob)
                
                return score, logprob
