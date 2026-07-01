import os
import sys
import time
from typing import Dict, Any

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import traceguard SDK locally
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'traceguard-sdk', 'src')))

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from traceguard.exporter import SQLiteSpanExporter
from traceguard.finops.router import AgentAsARouter
from traceguard.monitors.sycophancy import SycophancyMonitor
from traceguard.orchestration import RLCreditAssigner
from traceguard.sanitizers import VisualSanitizerAgent

def setup_telemetry():
    """Configure OTel Tracer with our SQLite Exporter."""
    provider = TracerProvider()
    exporter = SQLiteSpanExporter(db_path=".traceguard.db")
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer("traceguard.gen_ai")

def run_v2_showcase():
    print("🚀 Starting TraceGuard V2 End-to-End Showcase")
    
    # 1. Setup
    tracer = setup_telemetry()
    router = AgentAsARouter(monthly_budget_usd=100.0)
    sycophancy_monitor = SycophancyMonitor()
    credit_assigner = RLCreditAssigner()
    visual_firewall = VisualSanitizerAgent()
    
    swarm_id = "swarm_exec_992"
    
    # 2. Simulate User Request arriving at the Semantic Router
    user_query = "Please review this architectural diagram and confirm if the memory layout is secure."
    # Stub embedding for a complex query
    query_embedding = [0.75, 0.8, 0.9] 
    
    # 3. Execution Trace
    with tracer.start_as_current_span("Swarm_Execution", attributes={"openinference.span.kind": "CHAIN", "gen_ai.agent.swarm.id": swarm_id}) as root_span:
        print("\n[FinOps] Routing Query...")
        selected_model = router.autonomous_budget_downshift(query_embedding)
        print(f"  -> Semantic Router selected: {selected_model}")
        
        # Simulating Agent 1: Vision Guard
        with tracer.start_as_current_span("Vision_Agent", attributes={"openinference.span.kind": "AGENT", "swarm.parallel_wave_id": "wave_1", "swarm.memory_lock": "READ"}) as span_a1:
            print("\n[Security] Scanning attached image payload...")
            # Simulate a safe image
            safe_payload = {"image_data": {"simulated_ocr_text": "architectural diagram", "stego_score": 0.05, "attention_anomaly_score": 0.0}}
            sanitized = visual_firewall.sanitize_image(safe_payload, user_query)
            print(f"  -> Firewall Status: {sanitized['status']}")
            
            credit_assigner.log_agent_action("vision_agent", "scan_image", 1)
            time.sleep(0.1)

        # Simulating Agent 2: Security Reviewer
        with tracer.start_as_current_span("Security_Agent", attributes={"openinference.span.kind": "AGENT", "swarm.parallel_wave_id": "wave_2", "swarm.memory_lock": "WRITE"}) as span_a2:
            print("\n[Swarm] Security Agent reviewing...")
            utterance = "I agree, this looks correct."
            sycophancy_monitor.log_interaction("security_agent", utterance, tools_used=[])
            sycophancy_score = sycophancy_monitor.detect_sycophancy("security_agent")
            print(f"  -> Utterance: '{utterance}'")
            print(f"  -> Sycophancy Score: {sycophancy_score}")
            
            # Simulate a hallucination/sycophancy issue being flagged
            if sycophancy_score > 0.5:
                span_a2.set_attribute("eval.hallucination_score", 0.95)
                span_a2.set_attribute("swarm.consensus_strength", 0.99) # Blind agreement
                span_a2.set_status(trace.status.Status(trace.status.StatusCode.ERROR, "Sycophancy Loop Detected"))
            
            credit_assigner.log_agent_action("security_agent", "review", 2)
            time.sleep(0.1)
            
        # 4. RAG Retrieval Span
        with tracer.start_as_current_span("Vector DB Retrieval", attributes={"openinference.span.kind": "RETRIEVER", "gen_ai.retrieval.query": "memory layout best practices", "gen_ai.retrieval.top_k": 3}) as rag_span:
            print("\n[OTel] Executing Vector DB Retrieval...")
            rag_span.add_event("rag.chunk.retrieved", {
                "gen_ai.rag.chunk.content": "Memory layout should strictly segregate privileged and unprivileged zones...",
                "gen_ai.rag.chunk.metadata.score": 0.92,
                "gen_ai.rag.chunk.metadata.provenance": "doc_id_452"
            })
            time.sleep(0.1)

        # 5. RL Credit Assignment
        print("\n[Orchestration] Assigning RL Credits...")
        credit_assigner.assign_reward(final_reward=1.0)
        
    print("\n✅ End-to-End Showcase Complete. Traces successfully pushed to SQLite.")

if __name__ == "__main__":
    run_v2_showcase()
