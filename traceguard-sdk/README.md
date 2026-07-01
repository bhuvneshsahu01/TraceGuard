# TraceGuard SDK

The TraceGuard SDK is the core OpenTelemetry-based tracing and evaluation library for AI agents.

## Features
- `@traceguard.observe` decorator to automatically trace agent executions.
- Sync traces to local SQLite or TraceGuard Cloud.
- Evaluate traces using local or remote LLM-as-a-judge.

## Installation
```bash
pip install traceguard
```

## Usage
```python
from traceguard import observe

@observe()
def my_agent_step(input_text: str):
    # Call your LLM here
    return "Output"
```
