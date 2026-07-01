import pytest
from traceguard_fuzz.interceptor import fuzz_tool

def test_fuzz_tool_injection():
    # We set injection_rate to 1.0 to guarantee fuzzing happens
    @fuzz_tool(injection_rate=1.0)
    def my_query_tool(query: str, limit: int = 10) -> dict:
        return {"query": query, "limit": limit}
        
    # The original values should NOT be returned because they get fuzzed
    result = my_query_tool("SELECT * FROM users", limit=5)
    
    # Check that at least one of the inputs was mutated
    assert result["query"] != "SELECT * FROM users" or result["limit"] != 5

def test_fuzz_tool_bypass():
    # We set injection_rate to 0.0 to guarantee NO fuzzing happens
    @fuzz_tool(injection_rate=0.0)
    def my_safe_tool(query: str, limit: int = 10) -> dict:
        return {"query": query, "limit": limit}
        
    result = my_safe_tool("SELECT * FROM users", limit=5)
    
    # Everything should remain exactly the same
    assert result["query"] == "SELECT * FROM users"
    assert result["limit"] == 5

@pytest.mark.asyncio
async def test_fuzz_tool_async():
    @fuzz_tool(injection_rate=1.0)
    async def my_async_tool(count: int) -> int:
        return count
        
    result = await my_async_tool(42)
    assert result != 42 # It should be mutated
