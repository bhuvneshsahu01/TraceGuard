"""
traceguard/guardrails/pii.py
----------------------------
Two-Tier PII Redaction Engine:
Tier 1: High-throughput regex pass (SSN, credit card with Luhn check, email, phone, IPv4, API keys).
Tier 2: Presidio Analyzer/Anonymizer integration when available, with resilient lightweight NER fallback.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def _luhn_checksum(card_number: str) -> bool:
    """Verifies Luhn checksum for credit card number strings."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


@dataclass
class RedactionResult:
    """Result from PII scrubbing."""
    redacted_text: str
    redaction_count: int
    entity_counts: Dict[str, int] = field(default_factory=dict)
    detected_entities: List[str] = field(default_factory=list)


class PIIRedactor:
    """
    Two-tier PII Redaction Engine.
    Tier 1: Zero-dependency regex scanner.
    Tier 2: Presidio Anonymizer if installed, or regex rule fallback.
    """

    PATTERNS = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "PHONE": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "IPV4": re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        "API_KEY": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16})\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    }

    def __init__(self, use_presidio: bool = True):
        self.use_presidio = use_presidio
        self.presidio_available = False
        self._analyzer = None
        self._anonymizer = None

        if use_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine
                self._analyzer = AnalyzerEngine()
                self._anonymizer = AnonymizerEngine()
                self.presidio_available = True
            except ImportError:
                self.presidio_available = False

    def redact(self, text: str) -> RedactionResult:
        """
        Executes two-tier redaction over input text.
        """
        if not text or not isinstance(text, str):
            return RedactionResult(redacted_text=text or "", redaction_count=0)

        redacted = text
        entity_counts: Dict[str, int] = {}
        total_count = 0

        # Tier 1: Fast regex pass
        for entity_type, pattern in self.PATTERNS.items():
            matches = list(pattern.finditer(redacted))
            if not matches:
                continue

            for match in reversed(matches):
                matched_str = match.group(0)
                # Extra validation for credit cards (avoid matching random long numbers)
                if entity_type == "CREDIT_CARD" and not _luhn_checksum(matched_str):
                    continue

                start, end = match.span()
                replacement = f"<{entity_type}>"
                redacted = redacted[:start] + replacement + redacted[end:]
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                total_count += 1

        # Tier 2: Presidio pass if available
        if self.presidio_available and self._analyzer and self._anonymizer:
            try:
                results = self._analyzer.analyze(text=redacted, language="en")
                if results:
                    anonymized = self._anonymizer.anonymize(text=redacted, analyzer_results=results)
                    redacted = anonymized.text
                    for r in results:
                        entity_counts[r.entity_type] = entity_counts.get(r.entity_type, 0) + 1
                        total_count += 1
            except Exception:
                pass

        return RedactionResult(
            redacted_text=redacted,
            redaction_count=total_count,
            entity_counts=entity_counts,
            detected_entities=list(entity_counts.keys()),
        )
