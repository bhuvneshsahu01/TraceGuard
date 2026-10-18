"""
traceguard/guardrails/streaming.py
----------------------------------
Streaming-Safe Chunk Buffering for SSE and LLM Streaming Responses.
Holds a sliding character tail buffer across chunk boundaries so PII split across
adjacent chunks is detected and redacted before flushing to the client.
"""

from typing import Optional
from .pii import PIIRedactor


class StreamingBuffer:
    """
    Sliding tail buffer for stream chunk processing.
    Ensures zero PII leakage when sensitive tokens cross chunk boundaries.
    """

    def __init__(self, redactor: Optional[PIIRedactor] = None, buffer_size: int = 64):
        self.redactor = redactor or PIIRedactor(use_presidio=False)
        self.buffer_size = buffer_size
        self._tail = ""

    def process_chunk(self, chunk: str) -> str:
        """
        Receives an incoming stream chunk, merges with tail buffer, scrubs PII,
        and returns safe output while retaining the new tail.
        """
        if not chunk:
            return ""

        combined = self._tail + chunk

        if len(combined) <= self.buffer_size:
            # Retain in buffer, do not emit yet
            self._tail = combined
            return ""

        # Emit the safe prefix, hold back the trailing window
        emit_len = len(combined) - self.buffer_size
        to_check = combined[:emit_len + self.buffer_size]

        res = self.redactor.redact(to_check)
        redacted = res.redacted_text

        # Safe part to emit
        safe_to_emit = redacted[:emit_len]
        # Keep remaining for next chunk
        self._tail = redacted[emit_len:]
        return safe_to_emit

    def flush(self) -> str:
        """Flushes the final tail buffer upon stream end."""
        if not self._tail:
            return ""
        res = self.redactor.redact(self._tail)
        final_text = res.redacted_text
        self._tail = ""
        return final_text
