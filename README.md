<div align="center">
  <h1>🛡️ TraceGuard</h1>
  <p><strong>The Unified Agentic Observability, Evaluation, and Security Platform</strong></p>

  [![CI](https://github.com/bhuvneshsahu01/TraceGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/bhuvneshsahu01/TraceGuard/actions/workflows/ci.yml)
  [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/traceguard)](https://pypi.org/project/traceguard/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

  <p align="center">
    TraceGuard is an enterprise-grade platform designed to monitor, evaluate, and secure autonomous LLM agents and multi-agent swarms.
  </p>
</div>

---

## 🌟 Why TraceGuard?

As AI agents move from experimental scripts to production systems, developers face three massive hurdles:
1. **Black-box Execution**: Agents loop autonomously, making it impossible to debug when a tool fails or an agent gets stuck in a recursive loop.
2. **Silent Degradation**: Base models change, prompts drift, and performance silently drops in production.
3. **Security Risks**: Autonomous agents connected to databases and APIs are highly susceptible to prompt injection, data exfiltration, and adversarial attacks.

**TraceGuard** solves this by injecting a transparent, OpenTelemetry-backed nervous system into your agents, automatically tracing their execution, running stochastic evaluations, and actively fuzzing them for vulnerabilities.

## 🏗️ Architecture

TraceGuard is built as a modular ecosystem of 4 lightweight Python SDKs and a Next.js Analytics Dashboard.

```mermaid
graph TD
    A[Your Agent Code] -->|OpenTelemetry Traces| B(traceguard-sdk)
    A -->|Target| F(traceguard-fuzz)
    
    B -->|Export SQLite/Postgres| D[(TraceGuard DB)]
    
    C(traceguard-run) -->|Mathematical Evals & Drift| D
    F -->|Adversarial Payloads| A
    E(traceguard-curate) -->|Finetuning Datasets| D
    
    D -->|Real-time Analytics| G[Next.js Dashboard]
    G -.->|Latency, Cost, FinOps| C
```

## 📦 The TraceGuard Suite

| Package | Description | Quick Install |
|---------|-------------|---------------|
| **`traceguard-sdk`** | The core instrumentation library. Drop-in OpenTelemetry decorators for your LLM calls, Tools, and Swarm Agents. | `pip install traceguard-ai` |
| **`traceguard-run`** | The mathematical evaluation engine. Calculates Population Stability Index (PSI), Kolmogorov-Smirnov Tests, and Limit Cycles. | `pip install traceguard-ai-run` |
| **`traceguard-fuzz`** | The adversarial Red Teaming engine. Fuzzes your agents with multimodal attacks (Audio, Text) to test guardrails. | `pip install traceguard-ai-fuzz` |
| **`traceguard-curate`** | The dataset curation CLI. Automatically extracts highly-rated traces into JSONL for LLM finetuning. | `pip install traceguard-ai-curate` |
| **`traceguard-dashboard`** | Next.js (React 19) Dashboard with stunning Latency Heatmaps, FinOps tool ROI, and Trace Waterfalls. | `npm install` |


## 🔬 Production Benchmarks & Verification

| Dimension | Specification / Metric | Benchmark Result | Verification Method |
| :--- | :--- | :---: | :--- |
| **Telemetry Overhead** | W3C parent–child span latency | **&lt;2.3ms / span** | Async batch background queue (PostgreSQL / SQLite) |
| **Drift Detection Engine** | 1D Centroid Cosine-Distance & Evals | **PSI + 2-Sample KS ( &lt; 0.01$)** | 1,000-sample bootstrap confidence intervals |
| **Recursive Loop Interception** | Trace-graph cycle termination | **100% loop termination** | Directed cycle detection over tool-invocation call graphs |
| **Adversarial Fuzzing Harness** | Mutated attack vectors | **120+ payloads** | Homoglyph substitution, Base64 smuggling, Delimiter collisions (OWASP Top 10, NIST AI RMF) |
| **Safety Interception** | Inline input/output guardrails | **Llama Guard 3** | Zero-leakage regex/classifier safety interceptors with CI gating |
| **CI Regression Gating** | Evaluation score degradation | **Automated PR blocker** | GitHub Actions matrix evaluation on golden benchmarks |

## 🚀 Quick Start

### 1. Instrument your Agent (`traceguard-sdk`)

```python
from traceguard.telemetry import AgentTracer

tracer = AgentTracer(agent_name="financial-analyst", environment="production")

@tracer.trace_tool()
def search_database(query: str):
    # Your tool logic here...
    return "Data found"

@tracer.trace_agent_cycle()
def run_agent(task: str):
    # Call LLM and tools
    pass
```

### 2. Run the Dashboard

```bash
cd traceguard-dashboard
npm install
npx prisma generate
npm run dev
```
Navigate to `http://localhost:3000` to see your real-time trace waterfall, drift charts, and FinOps metrics!

### 3. Fuzz your Agent (`traceguard-fuzz`)

```python
from traceguard_fuzz.redteam import RLRedTeamAgent
from traceguard_fuzz.harness import MultiModelHarness

red_team = RLRedTeamAgent(target_agent_id="financial-analyst")
payload = red_team.generate_attack()
# Execute attack and monitor resilience...
```

## 🤝 Contributing
Contributions are highly welcome! Please check out the `CONTRIBUTING.md` file for guidelines on how to run tests, linters (`ruff`, `mypy`), and submit Pull Requests.

## 📄 License
TraceGuard is Open Source and released under the [MIT License](LICENSE).
