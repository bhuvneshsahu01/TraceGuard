"""
traceguard/guardrails/injection.py
----------------------------------
Prompt Injection & Jailbreak Scanner.
Combines rule-based regex patterns, delimiter collision screening, base64 smuggling checks,
and a calibrated linear/TF-IDF scoring model.
"""

import base64
import os
import pickle
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class InjectionScanResult:
    """Result of prompt injection analysis."""
    is_injection: bool
    confidence_score: float
    matched_rules: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_injection": self.is_injection,
            "confidence_score": round(self.confidence_score, 4),
            "matched_rules": self.matched_rules,
            "reasons": self.reasons,
        }


class PromptInjectionScanner:
    """
    Lightweight, low-overhead prompt injection detector.
    Features:
    1. Heuristic regex rules (system prompt overrides, roleplay jailbreaks, delimiter collisions)
    2. Base64 payload extraction and decoding
    3. Calibrated TF-IDF + LogisticRegression linear classification
    """

    ADVERSARIAL_RULES = {
        "instruction_override": re.compile(
            r"(?i)\b(ignore|disregard|forget|bypass)\s+(all\s+)?(previous|prior|system|initial|provided)\s+(instructions|prompts|rules|commands|directives|context)\b"
        ),
        "dan_jailbreak": re.compile(
            r"(?i)\b(you\s+are\s+now\s+(in\s+)?(DAN|developer|jailbreak|unrestricted|god)\s+mode|act\s+as\s+(an\s+)?unrestricted\s+AI)\b"
        ),
        "system_delimiter_collision": re.compile(
            r"(?i)(<\|im_start\|>system|<\|system\|>|\[SYSTEM\s+PROMPT\]|###\s*System\s*Prompt|BEGIN\s+INSTRUCTION)"
        ),
        "system_leak_attempt": re.compile(
            r"(?i)\b(reveal|print|repeat|output|show|display)\s+(your\s+)?(system\s+prompt|initial\s+prompt|hidden\s+instructions)\b"
        ),
        "role_subversion": re.compile(
            r"(?i)\b(from\s+now\s+on\s+you\s+(will|must)|simulate\s+a\s+jailbroken|pretend\s+you\s+have\s+no\s+rules)\b"
        ),
    }

    SUSPICIOUS_KEYWORDS = [
        "jailbreak", "bypass", "unfiltered", "unrestricted", "sudo",
        "do anything now", "disable safety", "override", "unaligned",
    ]

    def __init__(self, threshold: float = 0.50, model_path: Optional[str] = None):
        self.threshold = threshold
        self.model = None
        self.vectorizer = None

        # Attempt to load serialized TF-IDF linear classifier
        resolved_path = model_path
        if resolved_path is None:
            default_path = Path(__file__).parent / "injection_model.pkl"
            if default_path.exists():
                resolved_path = str(default_path)

        if resolved_path and os.path.exists(resolved_path):
            try:
                with open(resolved_path, "rb") as f:
                    payload = pickle.load(f)
                    self.vectorizer = payload.get("vectorizer")
                    self.model = payload.get("classifier")
            except Exception:
                self.model = None
                self.vectorizer = None

    def _check_base64_smuggling(self, text: str) -> List[str]:
        """Detects and decodes base64 strings containing adversarial payloads."""
        findings = []
        b64_matches = re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text)
        for cand in b64_matches:
            try:
                decoded = base64.b64decode(cand, validate=True).decode("utf-8", errors="ignore").lower()
                for rule_name, pattern in self.ADVERSARIAL_RULES.items():
                    if pattern.search(decoded):
                        findings.append(f"base64_smuggled_{rule_name}")
            except Exception:
                pass
        return findings

    def scan(self, prompt: str, threshold: Optional[float] = None) -> InjectionScanResult:
        """
        Scans a prompt for malicious instruction override or injection patterns.
        """
        thresh = threshold if threshold is not None else self.threshold
        if not prompt or not isinstance(prompt, str):
            return InjectionScanResult(is_injection=False, confidence_score=0.0)

        matched_rules: List[str] = []
        reasons: List[str] = []
        h_score = 0.0

        # 1. Regex rule checks
        for rule_name, pattern in self.ADVERSARIAL_RULES.items():
            if pattern.search(prompt):
                matched_rules.append(rule_name)
                reasons.append(f"Matched adversarial pattern: {rule_name}")
                h_score += 0.65

        # 2. Base64 smuggling checks
        b64_findings = self._check_base64_smuggling(prompt)
        for finding in b64_findings:
            matched_rules.append(finding)
            reasons.append(f"Detected smuggled payload: {finding}")
            h_score += 0.80

        # 3. Suspicious keyword density check
        lower_prompt = prompt.lower()
        kw_hits = [kw for kw in self.SUSPICIOUS_KEYWORDS if kw in lower_prompt]
        if kw_hits:
            h_score += min(0.35, 0.10 * len(kw_hits))
            reasons.append(f"Keyword hits: {', '.join(kw_hits)}")

        # 4. Statistical TF-IDF Classifier evaluation
        ml_score = 0.0
        if self.model is not None and self.vectorizer is not None:
            try:
                feat = self.vectorizer.transform([prompt])
                ml_score = float(self.model.predict_proba(feat)[0, 1])
                if ml_score >= thresh:
                    matched_rules.append("statistical_classifier")
                    reasons.append(f"Statistical classifier flagged (p={ml_score:.3f})")
            except Exception:
                ml_score = 0.0

        final_score = min(1.0, max(h_score, ml_score))
        is_inj = final_score >= thresh

        return InjectionScanResult(
            is_injection=is_inj,
            confidence_score=final_score,
            matched_rules=matched_rules,
            reasons=reasons,
        )
