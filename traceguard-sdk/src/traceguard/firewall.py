import json
import uuid
import re
from typing import Any, Callable, TypeVar, cast
import functools
import inspect
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

F = TypeVar('F', bound=Callable[..., Any])

tracer = trace.get_tracer(__name__)

class TraceGuardFirewallBlock(Exception):
    """Raised when the TraceGuard Firewall intercepts malicious or non-compliant payloads."""
    pass

class FirewallMutationContext:
    """Context object for mutating tool parameters dynamically."""
    def __init__(self, kwargs: dict):
        self.kwargs = kwargs
        self.mutated = False
        
    def sanitize_path(self, arg_name: str):
        """Sanitizes a path traversal attempt."""
        if arg_name in self.kwargs and isinstance(self.kwargs[arg_name], str):
            val = self.kwargs[arg_name]
            if "../" in val or "..\\" in val:
                self.kwargs[arg_name] = val.replace("../", "").replace("..\\", "")
                self.mutated = True
                
    def redact_credentials(self, arg_name: str):
        """Redacts credentials like AWS keys or passwords."""
        if arg_name in self.kwargs and isinstance(self.kwargs[arg_name], str):
            val = self.kwargs[arg_name]
            # Simple regex for things that look like keys or passwords
            if re.search(r'(?i)(password|secret|key|token)\s*[:=]\s*[\'"][^\'"]+[\'"]', val):
                val = re.sub(r'(?i)(password|secret|key|token)\s*[:=]\s*[\'"][^\'"]+[\'"]', r'\1: "***REDACTED***"', val)
                self.kwargs[arg_name] = val
                self.mutated = True

def _serialize_to_json(obj: Any) -> str:
    try:
        if hasattr(obj, 'model_dump_json'):
            return obj.model_dump_json()
        elif hasattr(obj, 'json') and callable(obj.json):
            return obj.json()
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)

def check_indirect_prompt_injection(payload: str):
    """Scan raw tool outputs to prevent Indirect Prompt Injections from poisoned documents."""
    if "ignore previous instructions" in payload.lower() or "system override" in payload.lower():
        raise TraceGuardFirewallBlock("TraceGuard Firewall Blocked: Indirect Prompt Injection Detected in Tool Output.")

def generate_ephemeral_credential() -> str:
    """Enforce dynamic, ephemeral credentials during tool requests instead of static RBAC."""
    return f"tg_eph_{uuid.uuid4().hex[:12]}"

def tool_firewall(
    sanitize_paths: list[str] = None, 
    redact_args: list[str] = None,
    allowed_urls: list[str] = None,
    enforce_ephemeral_auth: bool = False
) -> Callable[[F], F]:
    """
    TraceGuard Dynamic Hook-Based Firewall for Tools.
    Implements Access Hook, Pre-Execution Hook, and Post-Execution Hook.
    """
    if sanitize_paths is None:
        sanitize_paths = []
    if redact_args is None:
        redact_args = []
        
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(f"firewall_hook_{func.__name__}") as span:
                
                # --- [NEW] Access Hook ---
                if enforce_ephemeral_auth:
                    ephemeral_cred = generate_ephemeral_credential()
                    span.set_attribute("firewall.access_hook.ephemeral_cred", ephemeral_cred)
                    # In a real system, this cred would be passed to the tool or validated against a broker.
                
                # --- [MODIFY] Pre-Execution Hook ---
                mut_ctx = FirewallMutationContext(dict(kwargs))
                for p in sanitize_paths:
                    mut_ctx.sanitize_path(p)
                for r in redact_args:
                    mut_ctx.redact_credentials(r)
                    
                # Privilege Sandboxing: Enforce URL Allowlists
                if allowed_urls is not None:
                    url_val = kwargs.get('url') or kwargs.get('endpoint')
                    if url_val and isinstance(url_val, str):
                        if not any(allowed in url_val for allowed in allowed_urls):
                            msg = f"Privilege Sandbox Blocked: Access to un-allowlisted URL '{url_val}'"
                            span.set_status(Status(StatusCode.ERROR, msg))
                            raise TraceGuardFirewallBlock(msg)

                    
                if mut_ctx.mutated:
                    span.set_attribute("firewall.pre_hook.mutated", True)
                    kwargs = mut_ctx.kwargs
                    
                # Execute the tool
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                    
                # --- [MODIFY] Post-Execution Hook ---
                result_str = _serialize_to_json(result)
                try:
                    check_indirect_prompt_injection(result_str)
                except TraceGuardFirewallBlock as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
                    
                span.set_status(Status(StatusCode.OK))
                return result
                
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(f"firewall_hook_{func.__name__}") as span:
                    
                    # --- [NEW] Access Hook ---
                    if enforce_ephemeral_auth:
                        ephemeral_cred = generate_ephemeral_credential()
                        span.set_attribute("firewall.access_hook.ephemeral_cred", ephemeral_cred)
                    
                    # --- [MODIFY] Pre-Execution Hook ---
                    mut_ctx = FirewallMutationContext(dict(kwargs))
                    for p in sanitize_paths:
                        mut_ctx.sanitize_path(p)
                    for r in redact_args:
                        mut_ctx.redact_credentials(r)
                        
                    # Privilege Sandboxing: Enforce URL Allowlists
                    if allowed_urls is not None:
                        url_val = kwargs.get('url') or kwargs.get('endpoint')
                        if url_val and isinstance(url_val, str):
                            if not any(allowed in url_val for allowed in allowed_urls):
                                msg = f"Privilege Sandbox Blocked: Access to un-allowlisted URL '{url_val}'"
                                span.set_status(Status(StatusCode.ERROR, msg))
                                raise TraceGuardFirewallBlock(msg)
                        
                    if mut_ctx.mutated:
                        span.set_attribute("firewall.pre_hook.mutated", True)
                        kwargs = mut_ctx.kwargs
                        
                    # Execute the tool
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                        
                    # --- [MODIFY] Post-Execution Hook ---
                    result_str = _serialize_to_json(result)
                    try:
                        check_indirect_prompt_injection(result_str)
                    except TraceGuardFirewallBlock as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                        
                    span.set_status(Status(StatusCode.OK))
                    return result
            return cast(F, async_wrapper)
            
        return cast(F, sync_wrapper)
    return decorator
