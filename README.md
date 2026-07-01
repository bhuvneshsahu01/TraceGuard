<div align="center">
  <h1>🛡️ TraceGuard V2</h1>
  <p><strong>Next-Gen Autonomous Observability & Security Platform for AI Agents</strong></p>
</div>

---

> 85%+ of AI agent projects fail in production because developers test probabilistic systems with deterministic tools. TraceGuard fixes this by bringing rigorous mathematical evaluation, reinforcement learning, and autonomous security to the AI agent lifecycle.

TraceGuard unifies the entire AI evaluation flywheel:
**Trace → Autonomous Security → Statistical Eval → RL Swarm Training → FinOps Routing.**

## 🧠 The Moat: TraceGuard V2 Features

### 1. Autonomous Multimodal Security
- **OCR & CLIP Stego Firewalls:** Blocks advanced Cross-Modal Prompt Injections (CrossMPI) and text-in-image steganography before they hit your agent.
- **Privilege Sandboxing & Zero Trust:** Blocks data exfiltration at the API layer by enforcing strict URL allowlists during agent tool execution.
- **RL-Driven Red Teaming:** An autonomous CLI agent that attacks your system nightly, utilizing a persistent, lifelong "Attack Library" to continually mutate and learn new exploitation vectors.

### 2. Statistical Evals & Calibration
- **Logprob Thresholding:** If the LLM judge isn't confident in its internal log probabilities, TraceGuard drops the sample.
- **Kolmogorov-Smirnov (KS) Tests:** Guarantees judgment distribution stability during multi-agent consensus debates.
- **Statistical Drift Engine:** Uses Bootstrap Confidence Intervals (CI) and Population Stability Index (PSI) to mathematically gate PRs that degrade performance.

### 3. Swarm Observability & RL Credit
- **Graph Aggregation Engine:** TraceGuard leverages OpenTelemetry (`gen_ai.agent.swarm.id`) to dynamically reconstruct highly complex, non-linear DAGs across distributed environments.
- **Psychological Swarm Monitors:** Explicit heuristic detection for Sycophancy ("agreement without verification") and Context Contamination (semantic drift across shared memory).
- **RL Credit Assignment:** Backpropagates temporal "rewards" through a Swarm DAG, laying the absolute foundation for training Multi-Agent systems via Reinforcement Learning.

### 4. Machine-Learning FinOps
- **Semantic Prototype Routing:** Dynamically computes cosine similarity against known query prototypes to instantly route tasks to the optimal LLM (e.g., `gpt-4o` vs `llama-3.1-8b`), explicitly falling back to latency predictors when ambiguous.
- **Live A/B Tool Testing & EMA Tracking:** Dynamically splits traffic between tool variants, measures the Exponential Moving Average (EMA) of their ROI, and autonomously allocates traffic to the most profitable tools.

---

## 🏗️ Architecture

TraceGuard is a monorepo consisting of 5 seamlessly integrated modules:

1. **`traceguard-sdk`:** A lightweight OpenTelemetry-compliant Python SDK containing all Firewall, FinOps, and Telemetry Hooks.
2. **`traceguard-curate`:** Dataset Curation pipeline that extracts failed states into version-controlled golden datasets.
3. **`traceguard-run`:** The core evaluation and Red Teaming engine (CLI).
4. **`traceguard-fuzz`:** Adversarial robustness testing layer.
5. **`traceguard-dashboard`:** An Enterprise Next.js 15+ App Router web application directly connected to the local OTel SQLite DB. Visualizes parallel execution waves, memory locks, and hallucination score badges instantly on the trace graph.

---

## 🚀 Getting Started

### Generate Traces
Run the End-to-End V2 Showcase script to generate mock swarm traces with parallel waves, sycophancy loops, and Vector DB retrieval spans:
```bash
python test_traceguard/e2e_v2_showcase.py
```

### Local Dashboard
To view your agent's telemetry locally:
```bash
cd traceguard-dashboard
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

---

## 📄 License
MIT License.
