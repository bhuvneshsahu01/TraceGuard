import os
import sys

# Windows Unicode Emoji Fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from traceguard.sanitizers import AudioSanitizerAgent
from traceguard.monitors.exfil import SemanticDLPEngine
from traceguard.evals.debate import ConstructorAuditorTriad
from traceguard.evals.sage import IsotonicCalibrator
from traceguard.monitors.deadlock import SwarmCycleDetector, SwarmDeadlockError
from traceguard.finops.router import SemanticRouter
from traceguard.finops.budget import AdaptiveBudgetMonitor, BudgetExceededError
from traceguard.telemetry import DualLayerTelemetry

def showcase_v3_intelligence():
    print("🚀 TraceGuard V3: Advanced GPT Intelligence Showcase\n")
    
    print("🛡️ 1. Audio Sanitization (Phase 23)")
    audio_sanitizer = AudioSanitizerAgent(ultrasonic_threshold_khz=20.0)
    class MockAudio: peak_frequency_khz = 25.5 # DolphinAttack
    print(f"  Attempting to process audio payload with peak freq 25.5kHz...")
    result = audio_sanitizer.sanitize_audio({"audio_data": MockAudio()})
    print(f"  Result: {result['status']} - {result.get('reason', '')}\n")
    
    print("📊 2. Differential Outlier Exfil (Phase 23)")
    dlp = SemanticDLPEngine()
    # 10 inbound tokens, 600 outbound tokens -> 60x ratio
    is_safe = dlp.check_differential_outlier(inbound_context_tokens=10, outbound_tool_tokens=600)
    print(f"  Outbound payload 60x larger than inbound context. Safe? {is_safe}\n")
    
    print("⚖️ 3. Multi-Agent Debate & Isotonic Calibration (Phase 24)")
    def mock_judge(prompt, context): return (0.8, 0.9) # 80% score, 0.9 raw confidence
    def mock_llm(prompt): return "Simulated LLM argument."
    triad = ConstructorAuditorTriad(mock_llm, mock_judge)
    calibrator = IsotonicCalibrator()
    calibrator.fit([(0.8, 0.6)]) # Historically, at 0.8 raw score, it's only right 60% of the time.
    
    score, raw_logprob = triad.evaluate_with_debate("Is earth flat?", "No")
    true_prob = calibrator.calibrate(score, raw_logprob)
    print(f"  Raw LLM Confidence: 90%. Calibrated Empirical Correctness: {true_prob*100:.1f}%\n")
    
    print("🔄 4. Circular Wait Deadlock Detection (Phase 25)")
    deadlock_monitor = SwarmCycleDetector()
    try:
        deadlock_monitor.log_delegation("AgentA", "AgentB")
        deadlock_monitor.log_delegation("AgentB", "AgentC")
        print("  Delegated A -> B -> C...")
        deadlock_monitor.log_delegation("AgentC", "AgentA") # Causes Cycle
    except SwarmDeadlockError as e:
        print(f"  🚨 {e}\n")
        
    print("📉 5. Dynamic Cascading & Early Termination (Phase 26)")
    router = SemanticRouter()
    budget = AdaptiveBudgetMonitor()
    budget.log_historical_cost("research_task", 0.05)
    budget.log_historical_cost("research_task", 0.04)
    budget.log_historical_cost("research_task", 0.06)
    
    def mock_cascade_evaluator(model, prompt):
        if model == "llama-3.1-8b-instant": return "Answer", 0.4 # Low confidence
        return "Better Answer", 0.95
        
    final_answer, final_conf = router.cascade_route("Solve P=NP", mock_cascade_evaluator)
    print(f"  Cascaded final confidence: {final_conf:.2f}")
    
    try:
        budget.check_runtime_cost("research_task", 0.25) # Massive spend
    except BudgetExceededError as e:
        print(f"  🚨 {e}\n")
        
    print("🔬 6. Deep RAG Sub-span Schemas (Phase 27)")
    telemetry = DualLayerTelemetry()
    parent = telemetry.start_rag_query_parent("What is TraceGuard?")
    print("  Created granular RAG spans:")
    print("  -> rag.query")
    print("    -> rag.embedding")
    print("    -> rag.retrieval")
    print("    -> rag.reranking")
    print("    -> rag.context\n")
    
    print("✅ All V3 Intelligence features successfully showcased!")

if __name__ == "__main__":
    showcase_v3_intelligence()
