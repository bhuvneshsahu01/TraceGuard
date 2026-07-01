# Production-Grade TraceGuard Evaluation

We successfully completed a true, production-grade test of the TraceGuard framework utilizing the **Groq API** and a custom **LLM ReAct Agent**. This demonstrates that TraceGuard is fully prepared to defend an enterprise application from LLM degradation.

## The ReAct Agent (`real_agent.py`)
We built an LLM agent that resolves customer billing issues. It was given two external tools:
1. `get_customer_billing_history(customer_id)`
2. `issue_refund(customer_id, amount)`

## Phase A: The Golden Baseline (0% Fuzz)
We ran the agent 15 times with a 0% injection rate. 
The LLM successfully retrieved the billing history, calculated the refund, and issued it perfectly. The `traceguard-sdk` silently recorded this clean behavior to `.traceguard.db`. We then extracted this as `golden_baseline.jsonl` to serve as our mathematical anchor.

## Phase B: The Adversarial Pull Request (20% Fuzz)
We simulated a developer deploying a buggy PR. We increased the fuzz injection rate to 20%. 
The tools began throwing Type Errors and returning random strings.
- **The Result:** The Groq LLM became confused. In several traces, it attempted to call hallucinated tools or provided incorrect arguments (e.g. `issue_refund(amount=-50)`). 
- We extracted these chaotic traces into `pr_run.jsonl`.

## Phase C: The CI/CD Gate (`traceguard-run`)
We executed the Math Engine to compare the PR against the Baseline.

```bash
python -m traceguard_run.cli --dataset test_traceguard/pr_run.jsonl --baseline test_traceguard/golden_baseline.jsonl
```

### The Verdict: [FAIL] Do not merge.
1. **Population Stability Index (PSI):** The system recorded a **massive PSI drift of 1.927**. (Anything > 0.1 indicates significant distribution shift). The LLM's erratic tool retries and hallucinations fundamentally altered the token burn distribution compared to the stable baseline.
2. **Result:** TraceGuard instantly caught the degradation and blocked the Pull Request.

> [!SUCCESS]
> **Reputation Secured.** 
> TraceGuard successfully identified that the LLM was behaving erratically due to the fuzzed tools and blocked the bad deployment from reaching production!
