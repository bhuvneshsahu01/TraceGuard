# OpenTelemetry & Swarms

## Deep RAG Sub-span Schemas
TraceGuard provides granular visibility into Retrieval-Augmented Generation (RAG) pipelines. Instead of a monolithic block, traces are split into:
- `rag.embedding`
- `rag.retrieval`
- `rag.reranking`
- `rag.context`

This allows you to instantly isolate the exact origin of an LLM hallucination.

## Swarm Cycle Detection
When operating autonomous Multi-Agent Swarms, a critical failure mode is "Circular Delegation" (e.g., Agent A asks B, B asks C, C asks A). 
TraceGuard tracks real-time delegation graphs using a continuous Depth First Search (DFS). If a cycle is detected, it throws a `SwarmDeadlockError`, killing the swarm before it drains your API budget.

## Enterprise OTLP Export
TraceGuard is compliant with the GenAI SIG semantic conventions and ships natively with an `OTLPSpanExporter`. This means you can seamlessly route all traces from your AI Swarms directly into Enterprise tools like Jaeger, Grafana, or Datadog.
