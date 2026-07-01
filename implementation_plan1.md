# TraceGuard SDK - Core Primitives Implementation Plan

This plan details the implementation of the `@traceguard.observe` decorator, the OpenTelemetry integration, and the asynchronous SQLite trace sync mechanism.

## User Review Required

> [!IMPORTANT]
> Please review the OpenTelemetry setup and SQLite schema proposed below. This will serve as the foundational data model for the entire TraceGuard platform (including the evaluation engine and adversarial fuzzer).

## Open Questions

> [!WARNING]
> 1. **OpenTelemetry Context Propagation:** Are we expecting users to use `traceguard-sdk` in fully asynchronous applications (e.g., FastAPI, asyncio) or synchronous applications? (OTel handles both, but for the `@traceguard.observe` decorator, we'll need to support both `async def` and regular `def` functions).
> 2. **SQLite Dependency:** OpenTelemetry's `BatchSpanProcessor` handles asynchronous exporting in a background thread. I plan to use Python's built-in `sqlite3` library inside a custom `SQLiteSpanExporter` rather than adding a heavy ORM like SQLAlchemy to the SDK. Does this lean approach align with your vision?
> 3. **Payload Size:** Tool calls and agent prompts can be large. Should we apply a truncation limit to span attributes, or store the full payload in the SQLite DB?

## Proposed Architecture

Instead of manually spinning up background threads for async SQLite writes, we will leverage **OpenTelemetry's native architecture**:
1. **`SQLiteSpanExporter`**: A custom OpenTelemetry exporter that implements `export(spans)` to write to SQLite.
2. **`BatchSpanProcessor`**: Wraps the exporter. It buffers spans in memory and flushes them in a background thread asynchronously, guaranteeing non-blocking behavior for the user's agent code.
3. **`@traceguard.observe` Decorator**: 
   - Uses `functools.wraps` and detects if the target function is async or sync.
   - Extracts `args` and `kwargs` and stringifies them as span attributes.
   - Captures the return value or exceptions.

## Proposed SQLite Schema

We will use a flat, performant schema optimized for fast inserts from the SDK and fast reads from the CLI/Evaluation engine.

```sql
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    start_time INTEGER
);

CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    start_time INTEGER NOT NULL, -- Unix time in nanoseconds
    end_time INTEGER NOT NULL,
    status_code TEXT NOT NULL,   -- 'OK', 'ERROR', 'UNSET'
    attributes TEXT,             -- JSON string of args, kwargs, returns, etc.
    events TEXT                  -- JSON string of events (e.g., exceptions)
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
```

## Proposed Changes

### traceguard-sdk

#### [NEW] src/traceguard/exporter.py
- Implement `SQLiteSpanExporter` extending `opentelemetry.sdk.trace.export.SpanExporter`.
- Handles SQLite connection pooling (or thread-local connections) and batched `INSERT` statements.
- Includes a schema initialization function.

#### [NEW] src/traceguard/config.py
- Expose a `configure_traceguard(db_path: str)` function.
- Sets up the `TracerProvider`, `BatchSpanProcessor`, and `SQLiteSpanExporter`.

#### [MODIFY] src/traceguard/decorators.py
- Enhance `observe()` to support both synchronous and asynchronous functions.
- Add OpenTelemetry tracing context.
- Serialize arguments, kwargs, and return values to JSON, handling un-serializable objects gracefully.

#### [MODIFY] pyproject.toml
- Add a dependency for `pytest-asyncio` if missing, and ensure `opentelemetry-sdk` is available.

## Verification Plan

### Automated Tests
- `pytest tests/test_decorators.py` to ensure synchronous and asynchronous functions are correctly traced.
- `pytest tests/test_exporter.py` to verify spans are correctly batched and persisted to the local SQLite database.

### Manual Verification
- Write a simple mock agent script using `@traceguard.observe`, run it, and use the `sqlite3` CLI tool to query the `.traceguard.db` file to confirm execution latency, arguments, and return values are accurately recorded without blocking the main execution thread.
