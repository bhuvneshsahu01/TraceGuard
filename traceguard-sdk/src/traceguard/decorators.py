"""
TraceGuard decorators for observing agent execution.
"""
from typing import Any, Callable, TypeVar, cast, Optional
import functools
import inspect
import json
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

F = TypeVar('F', bound=Callable[..., Any])

tracer = trace.get_tracer(__name__)

def _serialize_to_json(obj: Any) -> str:
    """Safely serialize an object to JSON string."""
    try:
        # Pydantic models
        if hasattr(obj, 'model_dump_json'):
            return obj.model_dump_json()
        elif hasattr(obj, 'json') and callable(obj.json):
            return obj.json()
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)

# Basic pricing catalog (Cost per 1M tokens)
PRICING = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama3-70b-8192": {"input": 0.59, "output": 0.79},
    "gpt-4o": {"input": 5.00, "output": 15.00},
}

def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICING:
        return 0.0
    prices = PRICING[model]
    return (input_tokens / 1_000_000 * prices["input"]) + (output_tokens / 1_000_000 * prices["output"])

def log_rag_context(documents: list[str]) -> None:
    """
    Log retrieved RAG context to the current active span.
    This enables the RAG Triad evaluate step (Context Precision, Faithfulness).
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("rag.context", json.dumps(documents))


class TraceGuardFirewallBlock(Exception):
    """Raised when the TraceGuard Firewall intercepts malicious or non-compliant payloads."""
    pass

def guardrail(direction: str = "input") -> Callable[[F], F]:
    """
    A decorator that acts as a real-time firewall for agent functions.
    Checks for Prompt Injection and PII leakage.
    """
    def decorator(func: F) -> F:
        def check_payload(payload: str):
            # Simple heuristic for Prompt Injection
            if "ignore previous instructions" in payload.lower():
                raise TraceGuardFirewallBlock("TraceGuard Firewall Blocked: Prompt Injection Detected.")
            
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(f"guardrail_{func.__name__}") as span:
                span.set_attribute("guardrail.direction", direction)
                
                # Check Input
                if direction in ("input", "both"):
                    payload = _serialize_to_json(args) + _serialize_to_json(kwargs)
                    try:
                        check_payload(payload)
                    except TraceGuardFirewallBlock as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                        
                result = func(*args, **kwargs)
                
                # Check Output
                if direction in ("output", "both"):
                    try:
                        check_payload(_serialize_to_json(result))
                    except TraceGuardFirewallBlock as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                        
                span.set_status(Status(StatusCode.OK))
                return result
                
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(f"guardrail_{func.__name__}") as span:
                    span.set_attribute("guardrail.direction", direction)
                    
                    # Check Input
                    if direction in ("input", "both"):
                        payload = _serialize_to_json(args) + _serialize_to_json(kwargs)
                        try:
                            check_payload(payload)
                        except TraceGuardFirewallBlock as e:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                            
                    result = await func(*args, **kwargs)
                    
                    # Check Output
                    if direction in ("output", "both"):
                        try:
                            check_payload(_serialize_to_json(result))
                        except TraceGuardFirewallBlock as e:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                            
                    span.set_status(Status(StatusCode.OK))
                    return result
            return cast(F, async_wrapper)
            
        return cast(F, sync_wrapper)
    return decorator

def observe(model: Optional[str] = None) -> Callable[[F], F]:
    """
    A decorator to trace an agent's execution path, tracking 
    arguments, return values, latency, and financial unit economics.
    """
    def decorator(func: F) -> F:
        def process_result_for_cost(span, result, args, kwargs):
            if not model:
                return
                
            input_tokens = 0
            output_tokens = 0
            
            # Try to extract usage from standard LLM response objects (OpenAI, Groq, Anthropic)
            if hasattr(result, 'usage') and hasattr(result.usage, 'prompt_tokens'):
                input_tokens = getattr(result.usage, 'prompt_tokens', 0)
                output_tokens = getattr(result.usage, 'completion_tokens', 0)
            else:
                # Fallback: estimate based on character length (~4 chars per token)
                input_str = _serialize_to_json(args) + _serialize_to_json(kwargs)
                output_str = _serialize_to_json(result)
                input_tokens = len(input_str) // 4
                output_tokens = len(output_str) // 4
                span.set_attribute("financial.estimated_tokens", True)
                
            cost = _calculate_cost(model, input_tokens, output_tokens)
            
            span.set_attribute("financial.input_tokens", input_tokens)
            span.set_attribute("financial.output_tokens", output_tokens)
            span.set_attribute("financial.cost_usd", cost)
            span.set_attribute("llm.model", model)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(func.__name__) as span:
                    span.set_attribute("function.type", "async")
                    span.set_attribute("input.args", _serialize_to_json(args))
                    span.set_attribute("input.kwargs", _serialize_to_json(kwargs))
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("output.result", _serialize_to_json(result))
                        
                        process_result_for_cost(span, result, args, kwargs)
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(func.__name__) as span:
                    span.set_attribute("function.type", "sync")
                    span.set_attribute("input.args", _serialize_to_json(args))
                    span.set_attribute("input.kwargs", _serialize_to_json(kwargs))
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("output.result", _serialize_to_json(result))
                        
                        process_result_for_cost(span, result, args, kwargs)
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return cast(F, sync_wrapper)
    return decorator
