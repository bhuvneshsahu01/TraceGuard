<div align="center">
  <h1>🛡️ TraceGuard V3</h1>
  <p><strong>Next-Gen Autonomous Observability & Security Platform for AI Agents</strong></p>
</div>

# 🛡️ TraceGuard V3: Advanced Generative AI Security & Observability

TraceGuard V3 is the ultimate enterprise-grade infrastructure for orchestrating, securing, and evaluating Large Language Models (LLMs) and Autonomous Agent Swarms. Built on OpenTelemetry (OTel), it enforces robust multimodal firewalls, semantic data-loss prevention, dynamic finops, and state-of-the-art multi-agent evaluators.

**Trace → Autonomous Security → Statistical Eval → Multi-Agent Swarms → FinOps Routing.**

## 🧠 The Moat: TraceGuard V3 Features

### 🛡️ 1. Sovereign Security & Automated Red Teaming
- **Multimodal Firewalls:** Detects text-embedded prompt injections (CrossMPI) hidden in images and ultrasonic audio frequencies (e.g., DolphinAttack) via FFT/OCR sanitizers.
- **Differential Exfiltration Monitoring:** Actively analyzes the token ratio of inbound prompts vs. outbound API calls. If an agent tries to dump massive data payloads based on a tiny input (RAG poisoning), it instantly terminates the process.
- **CI/CD Fuzzing Hooks:** Reinforcement Learning Red Team agents that automatically attack new prompt PRs to proactively find vulnerabilities.

### 📊 2. LLM-as-a-Judge & Empirical Calibration
- **Constructor/Auditor/Judge Debate Triad:** Defeats verbosity and position bias by spawning two agents to argue opposing sides of an evaluation, scored by a third Judge.
- **Logistic / Isotonic Calibrators:** Maps an LLM's inherently flawed raw log-probabilities to a mathematically sound, empirical percentage of true correctness based on historical human labels.

### 🐝 3. Autonomous Swarm Observability
- **Deadlock Cycle Detection:** Analyzes real-time delegation graphs to detect circular wait states (Agent A -> B -> C -> A), preventing infinite loops from burning cloud budgets.
- **Swimlane UIs:** Visually untangles parallel asynchronous Swarm waves by plotting dedicated horizontal lanes per agent, complete with state contamination overlays.

### 💸 4. Dynamic FinOps & Cascading Routers
- **Dynamic Model Cascading:** Automatically attempts to resolve prompts with cheap models (e.g., Llama-3). If the model's self-reported confidence is low, it seamlessly suppresses the weak response and re-runs the prompt on GPT-4o.
- **Adaptive Early Termination:** Calculates the 95% Confidence Interval for historical run costs and aggressively terminates active Swarms that breach the upper limit.

### 📡 5. Deep RAG Sub-span Schemas (OTel)
- **Granular RAG Breakdown:** Splits monolithic RAG spans into surgical `rag.embedding`, `rag.retrieval`, `rag.reranking`, and `rag.context` sub-spans, making it trivial to isolate the exact origin of a hallucination.

## 🚀 Quick Start

1. Set up your OpenTelemetry Collector locally.
2. Initialize TraceGuard with your target budget and logging level.

```python
from traceguard import TraceGuard
from traceguard.finops.router import SemanticRouter

# 1. Initialize TraceGuard Platform
tg = TraceGuard(budget_usd=1000.0)

# 2. Let the Semantic Router pick the cheapest model that meets your confidence threshold
router = SemanticRouter()
response, confidence = router.cascade_route("Solve P=NP", evaluator_func)
```

## 🏗️ Architecture

TraceGuard is built as a highly-modular monorepo containing 5 distinct domains:

- `traceguard-sdk/`: The core OpenTelemetry instrumentation, Dynamic FinOps routers, Swarm Cycle Detectors, and Evaluators.
- `traceguard-run/`: The CLI for kicking off Agent Swarm jobs and configuring model fallbacks.
- `traceguard-curate/`: A specialized Golden Dataset pipeline for aligning future models.
- `traceguard-fuzz/`: The RL-driven Autonomous Red Team for CI/CD fuzzing hooks.
- `traceguard-dashboard/`: The powerful Next.js Swimlane web application for human-in-the-loop review.
