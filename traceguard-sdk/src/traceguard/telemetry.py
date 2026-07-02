from typing import Optional, Dict, Any
from opentelemetry import trace
from .privacy import RealTimeRedactionEngine, ExternalStorageReference

class DualLayerTelemetry:
    """
    Harmonizes OpenInference's agentic granularity with OTel GenAI SIG standards.
    """
    def __init__(self):
        self.tracer = trace.get_tracer("traceguard.gen_ai")
        self.redaction_engine = RealTimeRedactionEngine()
        self.secure_storage = ExternalStorageReference()
        
    def start_root_span(self, task_name: str, attributes: Dict[str, Any] = None):
        """Starts the overall user task span."""
        return self.tracer.start_as_current_span(
            task_name, 
            attributes={"openinference.span.kind": "CHAIN", **(attributes or {})}
        )
        
    def start_internal_span(self, agent_name: str, span_kind: str = "AGENT", attributes: Dict[str, Any] = None):
        """Starts an internal reasoning/routing span."""
        return self.tracer.start_as_current_span(
            agent_name, 
            attributes={"openinference.span.kind": span_kind, **(attributes or {})}
        )
        
    def start_client_span(self, model_name: str, system_prompt: str, is_compliant_env: bool = False, swarm_id: str = None):
        """
        Starts an outbound LLM call span, mapped to `gen_ai.operation.name` = 'chat'.
        Applies redaction automatically.
        """
        attributes = {
            "openinference.span.kind": "LLM", 
            "gen_ai.system": model_name,
            "gen_ai.operation.name": "chat"
        }
        if swarm_id:
            attributes["gen_ai.agent.swarm.id"] = swarm_id
            
        span = self.tracer.start_as_current_span(
            f"LLM Call: {model_name}",
            attributes=attributes
        )
        
        if is_compliant_env:
            ref_url = self.secure_storage.store_and_reference(system_prompt, str(span.get_span_context().span_id))
            span.set_attribute("gen_ai.prompt.reference", ref_url)
        else:
            safe_prompt = self.redaction_engine.redact(system_prompt)
            span.set_attribute("gen_ai.prompt", safe_prompt)
            
        return span

    def record_completion(self, span: trace.Span, completion_text: str):
        """Records the unredacted completion text securely."""
        safe_completion = self.redaction_engine.redact(completion_text)
        span.set_attribute("gen_ai.completion", safe_completion)

    def start_rag_query_parent(self, query: str, swarm_id: str = None):
        """Starts the parent context for a granular RAG pipeline."""
        attributes = {"openinference.span.kind": "CHAIN", "gen_ai.rag.query": query}
        if swarm_id: attributes["gen_ai.agent.swarm.id"] = swarm_id
        return self.tracer.start_as_current_span("rag.query", attributes=attributes)
        
    def start_rag_embedding_span(self, model_name: str):
        """Phase 27: Granular RAG - Embedding generation."""
        attributes = {"openinference.span.kind": "EMBEDDING", "rag.embedding.model": model_name}
        return self.tracer.start_as_current_span("rag.embedding", attributes=attributes)
        
    def start_rag_retrieval_span(self, query: str, top_k: int):
        """Phase 27: Granular RAG - Vector DB search."""
        attributes = {
            "openinference.span.kind": "RETRIEVER",
            "rag.retrieval.query": query,
            "rag.retrieval.top_k": top_k
        }
        return self.tracer.start_as_current_span("rag.retrieval", attributes=attributes)
        
    def start_rag_reranking_span(self, reranking_model: str):
        """Phase 27: Granular RAG - Cross-encoder reranking."""
        attributes = {"openinference.span.kind": "RERANKER", "rag.reranking.model": reranking_model}
        return self.tracer.start_as_current_span("rag.reranking", attributes=attributes)
        
    def start_rag_context_span(self, token_count: int, truncated: bool = False):
        """Phase 27: Granular RAG - Context construction."""
        attributes = {
            "openinference.span.kind": "TOOL",
            "rag.context.token_count": token_count,
            "rag.context.truncated": truncated
        }
        return self.tracer.start_as_current_span("rag.context", attributes=attributes)
        
    def record_rag_chunk(self, span: trace.Span, chunk_content: str, score: float, provenance: str):
        """Records highly granular RAG metadata."""
        # Using events to append multiple chunks to a single span
        span.add_event("rag.chunk.retrieved", {
            "gen_ai.rag.chunk.content": chunk_content[:200], # Trucate for size
            "gen_ai.rag.chunk.metadata.score": score,
            "gen_ai.rag.chunk.metadata.provenance": provenance
        })

    def track_fallback(self, original_span_name: str, fallback_span_name: str, error: Exception):
        """Explicitly tracks complex routing fallbacks."""
        span = self.tracer.start_as_current_span(f"Fallback: {fallback_span_name}")
        span.set_attribute("traceguard.fallback.from", original_span_name)
        span.set_attribute("traceguard.fallback.reason", str(error))
        return span
