# 🗃️ traceguard-curate

**The Trace Distillation and Dataset Curation Pipeline for TraceGuard.**

`traceguard-curate` connects to your local TraceGuard OpenTelemetry database, extracts high-quality autonomous agent traces, and automatically formats them into JSONL datasets for LLM finetuning.

## Installation

```bash
pip install traceguard-ai-curate
```

## Usage

Use the CLI to mine your telemetry database for traces that meet specific criteria (e.g., successful executions, high user ratings) and export them for models like OpenAI's `gpt-4o-mini` or Llama-3.

### CLI 

```bash
# Export all successfully completed traces to JSONL for finetuning
traceguard-curate export --db traceguard.db --output dataset.jsonl
```

### Python API

```python
from traceguard_curate.extractor import TraceExtractor

# Initialize the extractor targeting the TraceGuard SQLite DB
extractor = TraceExtractor("traceguard.db")

# Extract only traces that represent a root agent chain
root_spans = extractor.extract_root_spans()

print(f"Found {len(root_spans)} root spans for curation.")
```

## Features
- **Zero-ETL Curation**: Directly mines OpenTelemetry SQLite databases without needing complex data pipelines.
- **Automated Formatting**: Converts complex agent traces and Swarm graphs into flat conversational JSONL formats required for finetuning.
- **Filtering**: Filter spans by status, latency, or anomaly scores before inclusion in the final dataset.
