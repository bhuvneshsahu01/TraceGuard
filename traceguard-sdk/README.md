# 🛡️ traceguard-sdk

**The core instrumentation library for the TraceGuard platform.**

`traceguard-sdk` provides lightweight, OpenTelemetry-backed decorators and context managers to automatically trace your LLM agents, tools, and swarm topologies.

## Installation

```bash
pip install traceguard
```

## Usage

Instrumenting an Agent and a Tool is as simple as adding decorators.

```python
import os
from traceguard.telemetry import AgentTracer

# Initialize the tracer
tracer = AgentTracer(agent_name="my-research-agent", environment="production")

# Trace a tool call
@tracer.trace_tool()
def search_web(query: str):
    # Simulated search
    return f"Results for {query}"

# Trace an entire agent execution cycle
@tracer.trace_agent_cycle()
def run_agent_loop(task: str):
    print(f"Executing task: {task}")
    result = search_web(task)
    return result

if __name__ == "__main__":
    run_agent_loop("Quantum computing startups")
```

## Features
- **OpenTelemetry Standard**: 100% compliant with OTLP. Export traces to Jaeger, Datadog, or the local TraceGuard SQLite database.
- **Swarm Cycle Detection**: Automatically detect graph cycles in multi-agent environments.
- **Granular RAG Tracing**: Trace chunk retrieval and vector store latency.

For full documentation, visit the [TraceGuard Github Repository](https://github.com/bhuvneshsahu01/TraceGuard).
