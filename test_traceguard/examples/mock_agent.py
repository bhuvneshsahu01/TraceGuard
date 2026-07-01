import time
import random
from traceguard import configure_traceguard, observe
from traceguard_fuzz import fuzz_tool

# Initialize the TraceGuard global provider
configure_traceguard(db_path=".traceguard.db")

@observe()
@fuzz_tool(injection_rate=0.4) # High injection rate for testing
def fetch_user_data(user_id: int) -> dict:
    # If the fuzzer injects something that isn't an int (like a massive string or None), this might crash
    if not isinstance(user_id, int):
        raise ValueError(f"CRITICAL ERROR: user_id must be an int, got {type(user_id)}")
        
    time.sleep(random.uniform(0.1, 0.3)) # Simulate latency
    return {"user_id": user_id, "name": "Alice", "plan": "Enterprise"}

@observe()
@fuzz_tool(injection_rate=0.2)
def generate_response(query: str, data: dict) -> str:
    if not isinstance(query, str) or len(query) == 0:
        raise ValueError("CRITICAL ERROR: Query cannot be empty or non-string")
    if not isinstance(data, dict):
        raise TypeError("CRITICAL ERROR: Data must be a dictionary")
        
    time.sleep(random.uniform(0.2, 0.8)) # Simulate LLM thinking latency
    
    # Simulate a timeout error randomly
    if random.random() < 0.1:
        time.sleep(3.0)
        raise TimeoutError("LLM Provider Timeout")
        
    return f"Response for {data.get('name')}: Your query '{query}' has been processed."

def run_agent():
    print("--- Starting Agent Run ---")
    try:
        user_data = fetch_user_data(12345)
        response = generate_response("How do I upgrade?", user_data)
        print("[SUCCESS]", response)
    except Exception as e:
        print("[CRASHED]", e)

if __name__ == "__main__":
    print("Running Mock Agent 20 times to generate traces...")
    for i in range(20):
        run_agent()
