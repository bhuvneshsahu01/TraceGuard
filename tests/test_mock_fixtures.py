"""
tests/test_mock_fixtures.py
---------------------------
Unit tests validating external service mock fixtures (Redis, PostgreSQL, LLM Provider)
and demonstrating their integration with TraceGuard decorators and firewall components.
Addresses Batch 1, Task 1.4 requirements.
"""

import pytest
from traceguard.decorators import _calculate_cost


class TestMockRedisFixture:
    """Validates InMemoryRedisDouble operations, TTL expiry, and error handling."""

    def test_basic_crud_and_increment(self, mock_redis):
        assert mock_redis.get("cache:key") is None
        mock_redis.set("cache:key", "value_abc")
        assert mock_redis.get("cache:key") == "value_abc"

        count = mock_redis.incr("rate_limit:user_1")
        assert count == 1
        count = mock_redis.incr("rate_limit:user_1", 4)
        assert count == 5

        deleted = mock_redis.delete("cache:key", "rate_limit:user_1")
        assert deleted == 2
        assert mock_redis.get("cache:key") is None

    def test_connection_failure_simulation(self, mock_redis):
        mock_redis.set("key_1", "alive")
        mock_redis.simulate_connection_failure()

        with pytest.raises(ConnectionError, match="Simulated Redis ConnectionRefusedError"):
            mock_redis.get("key_1")

        with pytest.raises(ConnectionError):
            mock_redis.set("key_2", "blocked")

        mock_redis.simulate_reconnection()
        assert mock_redis.get("key_1") == "alive"


class TestMockPostgresFixture:
    """Validates InMemoryPostgresDouble query tracking, transactions, and rollback."""

    def test_cursor_query_tracking(self, mock_postgres):
        cur = mock_postgres.cursor()
        cur.execute("SELECT span_id, trace_id FROM spans WHERE duration_ms > %s", (50,))
        assert len(cur.executed_queries) == 1
        assert "SELECT span_id" in cur.executed_queries[0]

    def test_transactional_context_commit_on_success(self, mock_postgres):
        with mock_postgres as pg:
            pg.cursor().execute("INSERT INTO audit_log (event) VALUES ('firewall_pass')")
        assert mock_postgres.committed is True
        assert mock_postgres.rolled_back is False

    def test_transactional_context_rollback_on_error(self, mock_postgres):
        with pytest.raises(RuntimeError):
            with mock_postgres as pg:
                pg.cursor().execute("INSERT INTO audit_log (event) VALUES ('firewall_blocked')")
                raise RuntimeError("DB write error")

        assert mock_postgres.rolled_back is True


class TestMockLLMProviderFixture:
    """Validates MockLLMClientDouble completions, usage counting, and decorator integration."""

    def test_deterministic_completion_and_usage(self, mock_llm_provider):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ]
        resp = mock_llm_provider.create(model="gpt-4-turbo", messages=messages)

        assert resp.model == "gpt-4-turbo"
        assert len(resp.choices) == 1
        assert resp.choices[0].message["role"] == "assistant"
        assert resp.usage.total_tokens == resp.usage.prompt_tokens + resp.usage.completion_tokens
        assert len(mock_llm_provider.call_history) == 1

    def test_simulated_llm_api_failure(self, mock_llm_provider):
        mock_llm_provider.set_failure(TimeoutError("Gateway timeout to LLM provider"))

        with pytest.raises(TimeoutError, match="Gateway timeout"):
            mock_llm_provider.create(model="gpt-4o", messages=[{"role": "user", "content": "hello"}])

    def test_token_cost_calculation_integration(self, mock_llm_provider):
        messages = [{"role": "user", "content": "Analyze trace data across cluster"}]
        resp = mock_llm_provider.create(model="gpt-4o", messages=messages)

        cost = _calculate_cost("gpt-4o", resp.usage.prompt_tokens, resp.usage.completion_tokens)
        assert cost > 0.0
