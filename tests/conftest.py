"""
tests/conftest.py
-----------------
Pytest configuration, mock fixtures, and in-memory test doubles for external services
including Redis, PostgreSQL, and remote LLM providers (OpenAI / Anthropic).
Addresses Batch 1, Task 1.4 requirements.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
import pytest


# =====================================================================
# 1. In-Memory Redis Test Double
# =====================================================================

class InMemoryRedisDouble:
    """Zero-dependency in-memory test double matching redis-py sync interface."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttls: Dict[str, float] = {}
        self._connected = True

    def simulate_connection_failure(self):
        self._connected = False

    def simulate_reconnection(self):
        self._connected = True

    def _check_connection(self):
        if not self._connected:
            raise ConnectionError("Simulated Redis ConnectionRefusedError")

    def _is_expired(self, key: str) -> bool:
        if key in self._ttls and time.time() > self._ttls[key]:
            del self._store[key]
            del self._ttls[key]
            return True
        return False

    def get(self, key: str) -> Optional[str]:
        self._check_connection()
        if self._is_expired(key) or key not in self._store:
            return None
        return str(self._store[key])

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._check_connection()
        self._store[key] = value
        if ex is not None:
            self._ttls[key] = time.time() + ex
        elif key in self._ttls:
            del self._ttls[key]
        return True

    def incr(self, key: str, amount: int = 1) -> int:
        self._check_connection()
        if self._is_expired(key) or key not in self._store:
            self._store[key] = amount
        else:
            self._store[key] = int(self._store[key]) + amount
        return self._store[key]

    def delete(self, *keys: str) -> int:
        self._check_connection()
        deleted = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                deleted += 1
        return deleted

    def flushdb(self):
        self._check_connection()
        self._store.clear()
        self._ttls.clear()


# =====================================================================
# 2. In-Memory PostgreSQL Test Double
# =====================================================================

@dataclass
class MockCursor:
    """Mock cursor recording executed SQL queries and returning configured rowsets."""
    executed_queries: List[str] = field(default_factory=list)
    _results: List[Any] = field(default_factory=list)
    _idx: int = 0

    def execute(self, query: str, params: Optional[tuple] = None):
        self.executed_queries.append(query)

    def fetchone(self) -> Optional[Any]:
        if self._idx < len(self._results):
            row = self._results[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self) -> List[Any]:
        return self._results


class InMemoryPostgresDouble:
    """In-memory PostgreSQL test double supporting cursor contexts and rollback."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.cursor_instance = MockCursor()

    def cursor(self) -> MockCursor:
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


# =====================================================================
# 3. Remote LLM Provider Test Double (OpenAI-compatible)
# =====================================================================

@dataclass
class MockLLMChoice:
    index: int
    message: Dict[str, str]
    finish_reason: str = "stop"


@dataclass
class MockLLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class MockLLMResponse:
    id: str
    choices: List[MockLLMChoice]
    usage: MockLLMUsage
    model: str = "gpt-4-turbo"


class MockLLMClientDouble:
    """Mock remote LLM provider client supporting deterministic completions and streaming."""

    def __init__(self, default_response: str = "Mocked LLM generation output"):
        self.default_response = default_response
        self.call_history: List[Dict[str, Any]] = []
        self.fail_with_error: Optional[Exception] = None

    def set_failure(self, error: Exception):
        self.fail_with_error = error

    def create(self, model: str, messages: List[Dict[str, str]], **kwargs) -> MockLLMResponse:
        if self.fail_with_error:
            raise self.fail_with_error

        self.call_history.append({"model": model, "messages": messages, "kwargs": kwargs})

        prompt_text = " ".join(m.get("content", "") for m in messages)
        prompt_tokens = max(1, len(prompt_text.split()))
        completion_tokens = max(1, len(self.default_response.split()))

        return MockLLMResponse(
            id="mock-llm-12345",
            choices=[
                MockLLMChoice(
                    index=0,
                    message={"role": "assistant", "content": self.default_response},
                    finish_reason="stop",
                )
            ],
            usage=MockLLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            model=model,
        )


# =====================================================================
# Pytest Fixtures
# =====================================================================

@pytest.fixture
def mock_redis():
    """Provides a fresh isolated in-memory Redis test double."""
    client = InMemoryRedisDouble()
    yield client
    client.flushdb()


@pytest.fixture
def mock_postgres():
    """Provides an isolated in-memory PostgreSQL test double."""
    return InMemoryPostgresDouble()


@pytest.fixture
def mock_llm_provider():
    """Provides an isolated mock LLM provider client double."""
    return MockLLMClientDouble()
