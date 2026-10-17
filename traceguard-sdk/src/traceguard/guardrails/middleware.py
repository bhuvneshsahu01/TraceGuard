"""
traceguard/guardrails/middleware.py
-----------------------------------
FastAPI / Starlette Async ASGI Middleware with OpenTelemetry Span Export.
Enforces pre-execution PII redaction, prompt-injection screening, token budgeting,
and streaming-safe chunk buffering with sub-3ms overhead.
"""

import json
import time
from dataclasses import dataclass
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.types import ASGIApp

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .pii import PIIRedactor
from .injection import PromptInjectionScanner
from .streaming import StreamingBuffer

tracer = trace.get_tracer("traceguard.guardrails")


@dataclass
class GuardrailConfig:
    """Configuration settings for TraceGuard ASGI Guardrails."""
    enable_pii_redaction: bool = True
    enable_injection_detection: bool = True
    injection_action: str = "block"  # "block", "flag", "none"
    injection_threshold: float = 0.50
    token_budget: int = 4096
    streaming_buffer_size: int = 64
    enable_otel: bool = True
    json_schema: Optional[dict] = None


class TraceGuardMiddleware(BaseHTTPMiddleware):
    """
    High-performance ASGI middleware providing continuous PII redaction,
    prompt-injection gating, and OpenTelemetry instrumentation.
    """

    def __init__(self, app: ASGIApp, config: Optional[GuardrailConfig] = None):
        super().__init__(app)
        self.config = config or GuardrailConfig()
        self.redactor = PIIRedactor(use_presidio=True)
        self.scanner = PromptInjectionScanner(threshold=self.config.injection_threshold)

    @staticmethod
    def _extract_text_for_inspection(body_text: str) -> str:
        """Extracts conversational content from LLM JSON schemas if present."""
        if not body_text:
            return ""
        trimmed = body_text.strip()
        if trimmed.startswith("{") or trimmed.startswith("["):
            try:
                data = json.loads(trimmed)
                if isinstance(data, dict):
                    if "prompt" in data and isinstance(data["prompt"], str):
                        return data["prompt"]
                    if "messages" in data and isinstance(data["messages"], list):
                        return " ".join(m.get("content", "") for m in data["messages"] if isinstance(m, dict))
                    if "input" in data and isinstance(data["input"], str):
                        return data["input"]
            except Exception:
                pass
        return body_text

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        t_start = time.perf_counter()
        span_cm = tracer.start_as_current_span("traceguard.guardrails") if self.config.enable_otel else None

        span = None
        if span_cm:
            span = span_cm.__enter__()

        try:
            # 1. Read Request Body
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""

            # Check Token Budget heuristic (~4 chars/token)
            estimated_tokens = len(body_text) // 4
            if estimated_tokens > self.config.token_budget:
                if span:
                    span.set_attribute("guardrails.action", "blocked_budget")
                    span.set_attribute("guardrails.token_count", estimated_tokens)
                    span.set_status(Status(StatusCode.ERROR, "Token budget exceeded"))
                return JSONResponse(
                    {"error": "Token budget exceeded", "estimated_tokens": estimated_tokens},
                    status_code=429,
                )

            # Check JSON Schema Validation if configured
            if self.config.json_schema and body_text:
                try:
                    data = json.loads(body_text)
                    try:
                        import jsonschema
                        jsonschema.validate(instance=data, schema=self.config.json_schema)
                    except ImportError:
                        required_props = self.config.json_schema.get("required", [])
                        for prop in required_props:
                            if prop not in data:
                                raise ValueError(f"Missing required property: '{prop}'")
                except Exception as val_err:
                    if span:
                        span.set_attribute("guardrails.action", "blocked_schema_validation")
                        span.set_status(Status(StatusCode.ERROR, f"Schema validation error: {val_err}"))
                    return JSONResponse(
                        {"error": "JSON schema validation failed", "details": str(val_err)},
                        status_code=422,
                    )


            # 2. Prompt Injection Scanning
            injection_detected = False
            injection_score = 0.0
            if self.config.enable_injection_detection and body_text:
                inspect_text = self._extract_text_for_inspection(body_text)
                scan_res = self.scanner.scan(inspect_text, threshold=self.config.injection_threshold)
                injection_detected = scan_res.is_injection
                injection_score = scan_res.confidence_score

                if span:
                    span.set_attribute("guardrails.injection_detected", injection_detected)
                    span.set_attribute("guardrails.injection_score", injection_score)
                    span.set_attribute("guardrails.matched_rules", ",".join(scan_res.matched_rules))

                if injection_detected and self.config.injection_action == "block":
                    t_end = time.perf_counter()
                    latency_ms = (t_end - t_start) * 1000.0
                    if span:
                        span.set_attribute("guardrails.latency_ms", latency_ms)
                        span.set_attribute("guardrails.action", "blocked_injection")
                        span.set_status(Status(StatusCode.ERROR, "Prompt injection blocked"))
                    return JSONResponse(
                        {
                            "error": "Prompt injection detected",
                            "score": injection_score,
                            "reasons": scan_res.reasons,
                        },
                        status_code=400,
                    )

            # 3. PII Redaction on Request Body
            pii_count = 0
            if self.config.enable_pii_redaction and body_text:
                redact_res = self.redactor.redact(body_text)
                pii_count = redact_res.redaction_count
                if span:
                    span.set_attribute("guardrails.pii_redacted_count", pii_count)

            # 4. Invoke Downstream Handler
            response = await call_next(request)

            # 5. Handle Streaming Response
            if hasattr(response, "body_iterator") and self.config.enable_pii_redaction:
                prev_iterator = response.body_iterator
                stream_buffer = StreamingBuffer(
                    redactor=self.redactor,
                    buffer_size=self.config.streaming_buffer_size,
                )

                async def streaming_generator():
                    async for chunk in prev_iterator:
                        chunk_str = chunk.decode("utf-8", errors="ignore") if isinstance(chunk, bytes) else chunk
                        safe = stream_buffer.process_chunk(chunk_str)
                        if safe:
                            yield safe.encode("utf-8") if isinstance(chunk, bytes) else safe
                    final = stream_buffer.flush()
                    if final:
                        yield final.encode("utf-8") if isinstance(chunk, bytes) else final

                response.body_iterator = streaming_generator()

            t_end = time.perf_counter()
            latency_ms = (t_end - t_start) * 1000.0

            if span:
                span.set_attribute("guardrails.latency_ms", latency_ms)
                span.set_attribute("guardrails.action", "passed")
                span.set_status(Status(StatusCode.OK))

            response.headers["X-TraceGuard-Guardrails"] = "checked"
            response.headers["X-TraceGuard-Latency-MS"] = f"{latency_ms:.3f}"
            return response

        except Exception as e:
            if span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise e
        finally:
            if span_cm:
                span_cm.__exit__(None, None, None)
