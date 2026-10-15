"""
tests/test_benchmark_overhead.py
--------------------------------
Pytest suite verifying OpenTelemetry decorator latency overhead and memory stability.
Ensures @guardrail decorator overhead is strictly < 2.5 ms per request and 
validates memory growth under sustained span generation.
Addresses Batch 2, Task 2.2 requirements.
"""

import gc
import time
import tracemalloc
from opentelemetry import trace

from traceguard.decorators import guardrail


def test_guardrail_latency_overhead_under_sla():
    """Validates that @guardrail wrapper overhead is < 2.5 ms per invocation on p95."""

    def raw_task(x: int) -> int:
        return x * 2

    @guardrail(direction="both")
    def guarded_task(x: int) -> int:
        return x * 2

    # Warmup
    for i in range(20):
        raw_task(i)
        guarded_task(i)

    raw_times = []
    guarded_times = []
    iterations = 250

    for i in range(iterations):
        t0 = time.perf_counter()
        raw_task(i)
        raw_times.append((time.perf_counter() - t0) * 1000.0)

    for i in range(iterations):
        t0 = time.perf_counter()
        guarded_task(i)
        guarded_times.append((time.perf_counter() - t0) * 1000.0)

    overheads = [g - r for g, r in zip(guarded_times, raw_times)]
    p95_overhead = sorted(overheads)[int(iterations * 0.95)]

    # SLA requirement from CV and requirements: < 2.5 ms
    assert p95_overhead < 2.5, f"Overhead {p95_overhead:.4f} ms exceeded 2.5 ms SLA threshold"


def test_sustained_spans_memory_stability():
    """Validates memory stability and absence of memory leaks across 2,000 sustained spans."""
    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    tracer = trace.get_tracer("test.leak_check")
    num_spans = 2000

    for i in range(num_spans):
        with tracer.start_as_current_span(f"test_span_{i % 20}") as span:
            span.set_attribute("index", i)
            span.set_attribute("status", "ok")

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats_diff = snapshot_after.compare_to(snapshot_before, "lineno")
    total_diff_kb = sum(stat.size_diff for stat in stats_diff) / 1024.0

    # Total memory growth must be well below 5 MB (5120 KB)
    assert total_diff_kb < 5120.0, f"Memory growth {total_diff_kb:.2f} KB exceeded 5 MB threshold"
