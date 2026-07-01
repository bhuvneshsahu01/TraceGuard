"""
TraceGuard decorators for observing agent execution.
"""
from typing import Any, Callable, TypeVar, cast
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

def observe() -> Callable[[F], F]:
    """
    A decorator to trace an agent's execution path, tracking 
    arguments, return values, and latency using OpenTelemetry.
    """
    def decorator(func: F) -> F:
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
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return cast(F, sync_wrapper)
    return decorator
