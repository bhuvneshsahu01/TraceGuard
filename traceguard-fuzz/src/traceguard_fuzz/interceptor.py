import functools
import inspect
import random
from typing import Any, Callable, TypeVar, cast, get_type_hints
from .payloads import PayloadGenerator

F = TypeVar('F', bound=Callable[..., Any])

def fuzz_tool(injection_rate: float = 0.2) -> Callable[[F], F]:
    """
    A decorator that randomly injects malicious payloads into the function's arguments.
    Works seamlessly with @traceguard.observe so that injected payloads are traced.
    
    Args:
        injection_rate: Probability (0.0 to 1.0) that a given function call will be fuzzed.
    """
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        
        # Try to extract type hints safely
        try:
            type_hints = get_type_hints(func)
        except Exception:
            type_hints = {}

        def _apply_fuzzing(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
            """Mutates args and kwargs."""
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Decide if we fuzz this specific invocation
            if random.random() > injection_rate:
                return args, kwargs
                
            # If we decide to fuzz, we randomly pick ONE argument to mutate
            # to keep the fuzzing targeted and traceable
            if not bound_args.arguments:
                return args, kwargs
                
            target_arg_name = random.choice(list(bound_args.arguments.keys()))
            original_value = bound_args.arguments[target_arg_name]
            expected_type = type_hints.get(target_arg_name, type(original_value))
            
            mutated_value = PayloadGenerator.mutate(original_value, expected_type)
            bound_args.arguments[target_arg_name] = mutated_value
            
            return bound_args.args, bound_args.kwargs

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                mutated_args, mutated_kwargs = _apply_fuzzing(*args, **kwargs)
                return await func(*mutated_args, **mutated_kwargs)
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                mutated_args, mutated_kwargs = _apply_fuzzing(*args, **kwargs)
                return func(*mutated_args, **mutated_kwargs)
            return cast(F, sync_wrapper)
            
    return decorator
