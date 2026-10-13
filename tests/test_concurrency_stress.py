"""
tests/test_concurrency_stress.py
--------------------------------
Concurrency and stress testing suite for TraceGuard SDK.
Verifies race-condition resilience, memory safety, and thread isolation
under 50 simultaneous asynchronous workers and multithreaded execution pools.
Addresses Batch 1, Task 1.5 requirements.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
import pytest

from traceguard.finops.budget import AdaptiveBudgetMonitor, BudgetExceededError
from traceguard.monitors.deadlock import SwarmCycleDetector, SwarmDeadlockError
from traceguard.firewall import FirewallMutationContext, check_indirect_prompt_injection, TraceGuardFirewallBlock
from traceguard.decorators import guardrail


# =====================================================================
# 1. Concurrent Swarm Cycle Detection
# =====================================================================

class TestSwarmConcurrency:
    """Stress tests SwarmCycleDetector under high concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_dag_delegations_no_false_deadlocks(self):
        """50 simultaneous workers building disjoint DAG branches never trigger false deadlocks."""
        detector = SwarmCycleDetector()
        num_workers = 50

        async def worker_task(worker_id: int):
            # Each worker manages its own branch: root -> sub_worker -> leaf
            root = f"root_{worker_id}"
            sub = f"sub_{worker_id}"
            leaf = f"leaf_{worker_id}"

            await asyncio.sleep(random.uniform(0.001, 0.01))
            detector.log_delegation(root, sub)
            await asyncio.sleep(random.uniform(0.001, 0.01))
            detector.log_delegation(sub, leaf)

            # Resolve in reverse
            await asyncio.sleep(random.uniform(0.001, 0.01))
            detector.resolve_delegation(sub, leaf)
            detector.resolve_delegation(root, sub)

        tasks = [worker_task(i) for i in range(num_workers)]
        await asyncio.gather(*tasks)

        # Graph should have all worker delegations resolved
        for i in range(num_workers):
            root = f"root_{i}"
            assert len(detector.delegation_graph.get(root, set())) == 0

    @pytest.mark.asyncio
    async def test_concurrent_deadlock_detection_isolated(self):
        """A single cycle introduced among 50 workers is detected without breaking unaffected workers."""
        detector = SwarmCycleDetector()
        num_workers = 50
        cycle_raised = []

        async def worker_task(worker_id: int):
            if worker_id == 25:
                # Malicious worker creates a cycle: cycle_a -> cycle_b -> cycle_a
                try:
                    detector.log_delegation("agent_cycle_a", "agent_cycle_b")
                    await asyncio.sleep(0.005)
                    detector.log_delegation("agent_cycle_b", "agent_cycle_a")
                except SwarmDeadlockError:
                    cycle_raised.append(worker_id)
            else:
                detector.log_delegation(f"clean_src_{worker_id}", f"clean_dst_{worker_id}")
                await asyncio.sleep(0.005)
                detector.resolve_delegation(f"clean_src_{worker_id}", f"clean_dst_{worker_id}")

        tasks = [worker_task(i) for i in range(num_workers)]
        await asyncio.gather(*tasks, return_exceptions=True)

        assert len(cycle_raised) == 1
        assert cycle_raised[0] == 25


# =====================================================================
# 2. Concurrent Adaptive Budget Monitoring
# =====================================================================

class TestAdaptiveBudgetConcurrency:
    """Stress tests AdaptiveBudgetMonitor under 50 simultaneous writers."""

    @pytest.mark.asyncio
    async def test_50_concurrent_budget_writers_lossless_recording(self):
        """50 asynchronous workers writing costs to the same task preserves all entries."""
        monitor = AdaptiveBudgetMonitor()
        task_name = "concurrent_llm_summarize"
        num_workers = 50

        async def write_cost(cost: float):
            await asyncio.sleep(random.uniform(0.001, 0.005))
            monitor.log_historical_cost(task_name, cost)

        tasks = [write_cost(1.0 + (i * 0.01)) for i in range(num_workers)]
        await asyncio.gather(*tasks)

        recorded = monitor.historical_costs.get(task_name, [])
        assert len(recorded) == num_workers

        # Subsequent check within 95% CI bounds passes
        monitor.check_runtime_cost(task_name, 1.25)

        # Extreme runaway spend raises BudgetExceededError
        with pytest.raises(BudgetExceededError):
            monitor.check_runtime_cost(task_name, 500.0)


# =====================================================================
# 3. Concurrent Firewall & Mutation Isolation
# =====================================================================

class TestFirewallMutationConcurrency:
    """Verifies strict thread and task context isolation during mutation."""

    def test_multithreaded_parameter_mutation_isolation(self):
        """50 threads mutating distinct FirewallMutationContexts encounter zero cross-talk."""
        num_threads = 50
        results = []

        def thread_worker(worker_id: int):
            raw_path = f"/data/../../tenant_{worker_id}/secret.txt"
            ctx = FirewallMutationContext({"path": raw_path, "worker": worker_id})
            ctx.sanitize_path("path")
            sanitized = ctx.kwargs["path"]
            return (worker_id, sanitized, ctx.kwargs["worker"])

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(thread_worker, i) for i in range(num_threads)]
            for f in futures:
                results.append(f.result())

        assert len(results) == num_threads
        for wid, path, w_field in results:
            assert f"tenant_{wid}/secret.txt" in path
            assert "../" not in path
            assert w_field == wid


# =====================================================================
# 4. Concurrent Guardrail Decorators
# =====================================================================

class TestGuardrailDecoratorConcurrency:
    """Tests @guardrail decorated async functions under concurrent load."""

    @pytest.mark.asyncio
    async def test_50_concurrent_async_guardrail_invocations(self):
        """50 concurrent invocations through @guardrail complete with accurate results."""

        @guardrail(direction="both")
        async def mock_async_llm_inference(prompt: str, delay_ms: float = 5.0) -> dict:
            await asyncio.sleep(delay_ms / 1000.0)
            return {"status": "success", "echo": prompt, "tokens": len(prompt.split())}

        async def call_inference(i: int):
            return await mock_async_llm_inference(f"Hello prompt number {i} for cluster evaluation")

        tasks = [call_inference(i) for i in range(50)]
        outcomes = await asyncio.gather(*tasks)

        assert len(outcomes) == 50
        for i, res in enumerate(outcomes):
            assert res["status"] == "success"
            assert str(i) in res["echo"]
