# 📈 traceguard-run

**The Mathematical Evaluation Engine for TraceGuard.**

`traceguard-run` is a dedicated CLI and mathematical library for rigorously evaluating LLM output quality, monitoring data drift over time, and detecting infinite agent loops.

## Installation

```bash
pip install traceguard-ai-run
```

## Usage

You can use the evaluation engine via the Command Line Interface (CLI) or import it into your CI/CD pipelines.

### Using the CLI

Run a Kolmogorov-Smirnov (KS) test or Population Stability Index (PSI) drift calculation directly from your terminal:

```bash
traceguard evaluate --metric drift --input data.json
traceguard evaluate --metric limit-cycles --input traces.json
```

### Python API

```python
from traceguard_run.math.drift import calculate_psi, calculate_ks_test

# Baseline distribution (e.g., latency from last week)
baseline = [120, 130, 125, 140, 135]
# Current distribution (e.g., latency from today)
current = [122, 131, 128, 142, 136]

# Calculate Drift using PSI
psi_score = calculate_psi(baseline, current, buckets=3)
print(f"Population Stability Index: {psi_score}")

# Calculate Statistical Drift using KS Test
p_value = calculate_ks_test(baseline, current)
print(f"KS Test P-Value: {p_value}")
```

## Core Features
- **Statistical Drift (PSI & KS-Test)**: Detect when LLM output lengths, latencies, or logprobs shift significantly in production.
- **Limit Cycle Detection**: Identify graphs where Swarm Agents are stuck in recursive loops (e.g. Agent A calls Agent B, which calls Agent A forever).
- **Bootstrap Confidence Intervals**: Rigorously calculate error margins for LLM evaluation benchmarks.
