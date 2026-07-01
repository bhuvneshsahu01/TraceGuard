<div align="center">
  <h1>🛡️ TraceGuard</h1>
  <p><strong>The "pytest for AI": Enterprise-grade AI Agent Continuous Integration, Observability, and Evaluation.</strong></p>
</div>

---

> 85%+ of AI agent projects fail in production because developers test probabilistic systems with deterministic tools. TraceGuard fixes this by bringing rigorous mathematical evaluation to the AI agent lifecycle.

TraceGuard unifies the entire AI evaluation flywheel:
**Trace → Failure Detection → Dataset Curation → Statistical Eval → CI/CD Gating.**

## 🧠 The Moat: Mathematical Rigor
Unlike basic LLM dashboards, TraceGuard's evaluation engine is built on pure statistical mathematics to guarantee deployment safety:
- **Bootstrap Confidence Intervals:** We don't just output "Pass/Fail". We calculate the minimum detectable difference and output statistical confidence (e.g., *"95% confident the new PR degrades faithfulness"*).
- **Statistical Drift:** We detect agent degradation using Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests.
- **Limit Cycle Detection:** We apply dynamical systems theory to track agent loops and catch infinite looping behavior before it burns your token budget.

---

## 🏗️ Architecture

TraceGuard is a monorepo consisting of 5 seamlessly integrated modules:

### 1. `traceguard-sdk` (Observability)
A lightweight OpenTelemetry-compliant Python SDK. Wrap your agent's tools with `@traceguard.observe` to automatically capture inputs, outputs, errors, and latencies into a highly-performant SQLite database (`.traceguard.db`).

### 2. `traceguard-curate` (Dataset Curation)
A pipeline that scans production traces, flags anomalies (using configurable rules like `ErrorRule` and `LatencyRule`), and extracts the exact failed states into version-controlled JSON Lines (`test_cases.jsonl`) datasets.

### 3. `traceguard-run` (Evaluation Engine)
The core mathematical engine. A beautiful Typer/Rich CLI that evaluates new code against curated datasets. Computes Bootstrap CIs and runs KS Drift tests. Intended to be run in CI/CD pipelines to block mathematically unsafe pull requests.

### 4. `traceguard-fuzz` (Adversarial Testing)
A robustness testing layer. Wrap tools with `@fuzz_tool(injection_rate=0.2)` to intercept function calls at runtime and intelligently inject malicious payloads (SQL injection, massive strings, null bytes) based on Python type-hints.

### 5. `traceguard-dashboard` (Enterprise UI)
A premium Next.js 15+ App Router web application featuring a stunning dark-mode Glassmorphism design. Connects directly to the OpenTelemetry SQLite database to visualize trace latencies, statistical drift, and pass rates in real-time.

---

## 🚀 Getting Started

### Local Dashboard
To view your agent's telemetry locally:
```bash
cd traceguard-dashboard
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

### CI/CD Integration
TraceGuard includes a pre-configured GitHub Actions workflow (`.github/workflows/evaluate.yml`). It automatically runs `traceguard-run` on every pull request targeting `main`, blocking the merge if statistical degradation is detected.

---

## 📄 License
MIT License.
