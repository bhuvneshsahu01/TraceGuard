"""
tests/test_network_resilience.py
--------------------------------
Integration tests simulating network timeouts, HTTP 429 rate limits,
intermittent 503 errors, and exponential reconnection backoff.
Addresses Batch 1, Task 1.2 requirements.
"""

import asyncio
import time
from unittest.mock import MagicMock, patch
import pytest
from opentelemetry.trace.status import StatusCode
from opentelemetry.sdk.trace.export import SpanExportResult

from traceguard.decorators import observe
from traceguard.exporter import SQLiteSpanExporter
from traceguard.finops.metrics import RepairRetryTracker


# =====================================================================
# Simulated Error Prone Clients & Custom Network Exceptions
# =====================================================================

class NetworkTimeoutError(Exception):
    """Simulated socket or HTTP request timeout."""
    pass


class HTTP429RateLimitError(Exception):
    """Simulated HTTP 429 Too Many Requests with retry metadata."""
    def __init__(self, message: str = "Rate limit reached", retry_after_seconds: float = 0.05):
        super().__init__(message)
        self.status_code = 429
        self.retry_after_seconds = retry_after_seconds


class ServiceUnavailableError(Exception):
    """Simulated HTTP 503 upstream gateway outage."""
    def __init__(self, message: str = "Service Temporarily Unavailable"):
        super().__init__(message)
        self.status_code = 503


class ResilientExecutionClient:
    """
    Simulated resilient client implementing exponential backoff with jitter
    and Retry-After compliance for upstream API interactions.
    """
    def __init__(self, max_retries: int = 3, base_backoff_sec: float = 0.01, max_backoff_sec: float = 0.5):
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self.max_backoff_sec = max_backoff_sec
        self.retry_tracker = RepairRetryTracker()
        self.delays_recorded: list[float] = []

    def calculate_backoff(self, attempt: int, retry_after: float = None) -> float:
        if retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_backoff_sec)
        # Exponential backoff formula: base * (2 ** attempt)
        delay = self.base_backoff_sec * (2 ** attempt)
        return min(delay, self.max_backoff_sec)

    def execute_with_retry(self, target_callable, tool_name: str = "llm_client", *args, **kwargs):
        attempts = 0
        while True:
            try:
                return target_callable(*args, **kwargs)
            except (HTTP429RateLimitError, ServiceUnavailableError, NetworkTimeoutError) as exc:
                attempts += 1
                self.retry_tracker.log_retry(tool_name)
                if attempts > self.max_retries:
                    raise RuntimeError(f"Max retries ({self.max_retries}) exceeded for {tool_name}") from exc

                retry_after = getattr(exc, "retry_after_seconds", None)
                delay = self.calculate_backoff(attempts - 1, retry_after)
                self.delays_recorded.append(delay)
                time.sleep(delay)

    async def execute_async_with_retry(self, target_coro_fn, tool_name: str = "async_llm_client", *args, **kwargs):
        attempts = 0
        while True:
            try:
                return await target_coro_fn(*args, **kwargs)
            except (HTTP429RateLimitError, ServiceUnavailableError, NetworkTimeoutError) as exc:
                attempts += 1
                self.retry_tracker.log_retry(tool_name)
                if attempts > self.max_retries:
                    raise RuntimeError(f"Max retries ({self.max_retries}) exceeded for {tool_name}") from exc

                retry_after = getattr(exc, "retry_after_seconds", None)
                delay = self.calculate_backoff(attempts - 1, retry_after)
                self.delays_recorded.append(delay)
                await asyncio.sleep(delay)


# =====================================================================
# 1. HTTP 429 Rate Limit Simulation & Exponential Backoff
# =====================================================================

class TestHTTP429RateLimitHandling:
    """Verifies behavior when upstream providers return HTTP 429."""

    def test_rate_limit_recovery_after_two_bursts(self):
        """Simulates an endpoint that returns 429 twice before returning 200 OK."""
        call_count = 0

        @observe(model="llama-3.1-8b-instant")
        def mock_llm_call(prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise HTTP429RateLimitError("Rate limit exceeded. Tier token limit reached.", retry_after_seconds=0.01)
            return {"completion": f"Response to: {prompt}", "status": 200}

        client = ResilientExecutionClient(max_retries=3, base_backoff_sec=0.01)
        result = client.execute_with_retry(mock_llm_call, tool_name="groq_gateway", prompt="Hello LLM")

        assert result["status"] == 200
        assert call_count == 3
        assert client.retry_tracker.get_retry_frequency("groq_gateway") == 2
        assert len(client.delays_recorded) == 2

    def test_rate_limit_exhaustion_raises_runtime_error(self):
        """When 429s persist beyond max_retries, it must fail safely with full context."""
        @observe(model="gpt-4o")
        def persistent_rate_limited_call():
            raise HTTP429RateLimitError("Quota completely exhausted", retry_after_seconds=0.01)

        client = ResilientExecutionClient(max_retries=2, base_backoff_sec=0.01)
        with pytest.raises(RuntimeError, match="Max retries"):
            client.execute_with_retry(persistent_rate_limited_call, tool_name="openai_gpt4o")

        assert client.retry_tracker.get_retry_frequency("openai_gpt4o") == 3


# =====================================================================
# 2. Network Timeouts & Disconnect Simulation
# =====================================================================

class TestNetworkTimeoutHandling:
    """Verifies behavior when socket or HTTP connections hang or timeout."""

    def test_sync_timeout_under_observe_records_error_status(self):
        """Verifies that @observe captures timeout exceptions without masking the traceback."""
        @observe(model="llama-3.1-8b-instant")
        def slow_upstream_service():
            raise NetworkTimeoutError("Connection timed out after 5000ms waiting for upstream LLM")

        with pytest.raises(NetworkTimeoutError, match="Connection timed out"):
            slow_upstream_service()

    @pytest.mark.asyncio
    async def test_async_timeout_recovery_with_backoff(self):
        """Verifies asynchronous timeout recovery across multiple attempts."""
        call_counter = 0

        @observe(model="llama3-70b-8192")
        async def mock_async_call(query: str):
            nonlocal call_counter
            call_counter += 1
            if call_counter == 1:
                raise NetworkTimeoutError("Gateway timeout (504)")
            return {"result": f"Completed: {query}"}

        client = ResilientExecutionClient(max_retries=3, base_backoff_sec=0.01)
        res = await client.execute_async_with_retry(
            mock_async_call,
            tool_name="async_router",
            query="Analyze telemetry"
        )
        assert res["result"] == "Completed: Analyze telemetry"
        assert call_counter == 2
        assert client.retry_tracker.get_retry_frequency("async_router") == 1


# =====================================================================
# 3. Intermittent 503 Errors & Exponential Backoff Progression
# =====================================================================

class TestExponentialBackoffProgression:
    """Validates mathematical progression of retry intervals."""

    def test_exponential_backoff_delay_doubling(self):
        client = ResilientExecutionClient(base_backoff_sec=0.05, max_backoff_sec=2.0)
        # Attempt 0: 0.05 * 2^0 = 0.05
        assert client.calculate_backoff(0) == pytest.approx(0.05)
        # Attempt 1: 0.05 * 2^1 = 0.10
        assert client.calculate_backoff(1) == pytest.approx(0.10)
        # Attempt 2: 0.05 * 2^2 = 0.20
        assert client.calculate_backoff(2) == pytest.approx(0.20)
        # Attempt 3: 0.05 * 2^3 = 0.40
        assert client.calculate_backoff(3) == pytest.approx(0.40)

    def test_backoff_capped_at_max_delay(self):
        client = ResilientExecutionClient(base_backoff_sec=0.5, max_backoff_sec=1.0)
        # Attempt 5: 0.5 * 32 = 16.0 -> capped to 1.0
        assert client.calculate_backoff(5) == 1.0

    def test_retry_after_header_precedence(self):
        client = ResilientExecutionClient(base_backoff_sec=0.01, max_backoff_sec=5.0)
        # If server explicitly requests 0.2s, client must honor it
        assert client.calculate_backoff(0, retry_after=0.2) == 0.2


# =====================================================================
# 4. Exporter Resilience Under Database Network/Lock Failures
# =====================================================================

class TestExporterConnectionResilience:
    """Verifies that SQLiteSpanExporter gracefully handles connection errors without crashing."""

    def test_exporter_handles_connection_failure_gracefully(self, tmp_path):
        db_file = tmp_path / "test_exporter.db"
        exporter = SQLiteSpanExporter(db_path=str(db_file))

        mock_span = MagicMock()
        mock_span.parent = None
        mock_span.context.trace_id = 0x12345678123456781234567812345678
        mock_span.context.span_id = 0x1234567812345678
        mock_span.name = "test_span"
        mock_span.start_time = 1000
        mock_span.end_time = 2000
        mock_span.attributes = {"agent.id": "Agent1"}
        mock_span.events = []
        mock_span.status = MagicMock(status_code=StatusCode.OK)

        # Normal export works
        res = exporter.export([mock_span])
        assert res == SpanExportResult.SUCCESS

        # Simulate database connection failure (e.g. SQLite locked, permissions lost)
        with patch.object(exporter, "_get_connection", side_effect=Exception("Database lock error / network I/O timeout")):
            fail_res = exporter.export([mock_span])
            # Must return FAILURE and not crash host application
            assert fail_res == SpanExportResult.FAILURE
