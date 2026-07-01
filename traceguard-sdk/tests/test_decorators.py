import pytest
import sqlite3
import time
from traceguard import configure_traceguard, observe
from opentelemetry import trace
import asyncio

@pytest.fixture(scope="session", autouse=True)
def setup_tracing():
    configure_traceguard(db_path=".traceguard_test.db")
    # Wait a bit if needed, but not strictly necessary for setup
    yield
    # Cleanup DB if desired

def test_sync_observe():
    @observe()
    def my_sync_agent(prompt: str):
        return f"Processed: {prompt}"

    result = my_sync_agent("Hello World")
    assert result == "Processed: Hello World"
    
    # Force flush the tracer provider to ensure spans are exported
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush()

    conn = sqlite3.connect(".traceguard_test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, attributes, status_code FROM spans WHERE name = 'my_sync_agent'")
    rows = cursor.fetchall()
    assert len(rows) >= 1
    
    name, attributes, status_code = rows[-1]
    assert name == "my_sync_agent"
    assert status_code == "OK"
    assert "Hello World" in attributes
    conn.close()

@pytest.mark.asyncio
async def test_async_observe():
    @observe()
    async def my_async_agent(prompt: str):
        await asyncio.sleep(0.1)
        if prompt == "fail":
            raise ValueError("Intentional failure")
        return f"Async: {prompt}"

    result = await my_async_agent("Hello Async")
    assert result == "Async: Hello Async"
    
    with pytest.raises(ValueError):
        await my_async_agent("fail")

    # Force flush the tracer provider to ensure spans are exported
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush()

    conn = sqlite3.connect(".traceguard_test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, attributes, status_code, events FROM spans WHERE name = 'my_async_agent' ORDER BY start_time ASC")
    rows = cursor.fetchall()
    
    # Check the successful call
    success_row = rows[-2]
    assert success_row[2] == "OK"
    assert "Hello Async" in success_row[1]

    # Check the failed call
    fail_row = rows[-1]
    assert fail_row[2] == "ERROR"
    assert "fail" in fail_row[1]
    assert "Intentional failure" in fail_row[3] # exception in events
    conn.close()
