from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import trace

from traceguard.telemetry import DualLayerTelemetry

tracer = trace.get_tracer("traceguard.integrations.langchain")

class TraceGuardCallbackHandler(BaseCallbackHandler):
    """
    LangChain Callback Handler for TraceGuard.
    Automatically intercepts LangChain events and pipes them into TraceGuard's
    Security Firewalls and OpenTelemetry Spans.
    """
    
    def __init__(self, swarm_id: Optional[str] = None):
        self.swarm_id = swarm_id
        self.tg_telemetry = DualLayerTelemetry()
        # To maintain nested span contexts during LangChain callbacks, we keep a mapping of run_id to span
        self.run_spans: Dict[UUID, Any] = {}
        
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        model_name = kwargs.get("invocation_params", {}).get("model", "unknown-model")
        prompt_text = "\n".join(prompts)
        
        span = self.tg_telemetry.start_client_span(
            model_name=model_name,
            system_prompt=prompt_text,
            swarm_id=self.swarm_id
        )
        self.run_spans[run_id] = span

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        span = self.run_spans.get(run_id)
        if span:
            completion_text = response.generations[0][0].text if response.generations and response.generations[0] else ""
            self.tg_telemetry.record_completion(span, completion_text)
            span.end()
            del self.run_spans[run_id]

    def on_llm_error(self, error: BaseException, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        """Run when LLM errors."""
        span = self.run_spans.get(run_id)
        if span:
            span.record_exception(error)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
            span.end()
            del self.run_spans[run_id]

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        chain_name = serialized.get("name", "langchain.chain")
        attributes = {"openinference.span.kind": "CHAIN"}
        if self.swarm_id:
            attributes["gen_ai.agent.swarm.id"] = self.swarm_id
            
        span = tracer.start_span(chain_name, attributes=attributes)
        self.run_spans[run_id] = span

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        """Run when chain ends running."""
        span = self.run_spans.get(run_id)
        if span:
            span.end()
            del self.run_spans[run_id]

    def on_chain_error(self, error: BaseException, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        """Run when chain errors."""
        span = self.run_spans.get(run_id)
        if span:
            span.record_exception(error)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
            span.end()
            del self.run_spans[run_id]
            
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, parent_run_id: Optional[UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        tool_name = serialized.get("name", "langchain.tool")
        attributes = {"openinference.span.kind": "TOOL", "tool.input": input_str}
        if self.swarm_id:
            attributes["gen_ai.agent.swarm.id"] = self.swarm_id
            
        span = tracer.start_span(tool_name, attributes=attributes)
        self.run_spans[run_id] = span

    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        span = self.run_spans.get(run_id)
        if span:
            span.set_attribute("tool.output", str(output))
            span.end()
            del self.run_spans[run_id]
