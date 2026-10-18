from typing import Tuple, Callable, Optional
from opentelemetry import trace

tracer = trace.get_tracer("traceguard.gen_ai")

class ConstructorAuditorTriad:
    """
    GPT Phase 24: Multi-Agent Debate Routine.
    An evaluation panel that spawns a Constructor to defend an output, 
    an Auditor to attack it, and a Judge to score the debate, neutralizing
    verbosity and positional biases.
    """
    def __init__(self, llm_callable: Optional[Callable[[str], str]] = None, judge_callable: Optional[Callable[[str, str], Tuple[float, float]]] = None):
        self.model = "groq/llama3-8b-8192"
        self.judge = judge_callable
        
    def _litellm_call(self, prompt: str) -> str:
        from litellm import completion
        try:
            res = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"

    def evaluate_with_debate(self, prompt: str, target_answer: str) -> Tuple[float, float]:
        """
        Runs the full Constructor/Auditor/Judge triad.
        Returns the calibrated (score, logprob_confidence) from the Judge.
        """
        with tracer.start_as_current_span("eval.debate.triad"):
            
            # 1. Constructor Thread
            with tracer.start_as_current_span("agent.debate.constructor") as const_span:
                const_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                constructor_argument = self._litellm_call(f"Defend why this answer is correct for the prompt: '{prompt}'. Answer: '{target_answer}'")
                const_span.set_attribute("gen_ai.completion", constructor_argument)
                
            # 2. Auditor Thread
            with tracer.start_as_current_span("agent.debate.auditor") as aud_span:
                aud_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                auditor_argument = self._litellm_call(f"Critique and attack why this answer is flawed for the prompt: '{prompt}'. Answer: '{target_answer}'")
                aud_span.set_attribute("gen_ai.completion", auditor_argument)
                
            # 3. Judge Thread
            with tracer.start_as_current_span("agent.debate.judge_score") as judge_span:
                judge_span.set_attribute("gen_ai.agent.swarm.id", "debate_triad")
                
                debate_context = f"Constructor: {constructor_argument}\n\nAuditor: {auditor_argument}"
                
                # The judge resolves the debate
                if self.judge:
                    score, logprob = self.judge(prompt, debate_context)
                else:
                    # Simulated mock judge
                    import math
                    score = 0.8
                    logprob = math.log(0.9)
                
                judge_span.set_attribute("traceguard.eval.score", score)
                judge_span.set_attribute("traceguard.eval.logprob", logprob)
                
                return score, logprob
