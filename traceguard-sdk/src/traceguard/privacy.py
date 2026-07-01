import re
from typing import Dict, Any

class RealTimeRedactionEngine:
    """
    Scrubs PII and raw tool arguments with __REDACTED__ before exporting to the telemetry backend.
    """
    PII_PATTERNS = {
        "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b"
    }
    
    def __init__(self):
        self.active_patterns = self.PII_PATTERNS
        
    def redact(self, text: str) -> str:
        if not isinstance(text, str):
            return text
            
        redacted_text = text
        for category, pattern in self.active_patterns.items():
            redacted_text = re.sub(pattern, f"__REDACTED_{category.upper()}__", redacted_text)
            
        return redacted_text
        
    def redact_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact a dictionary."""
        redacted_payload = {}
        for k, v in payload.items():
            if isinstance(v, str):
                redacted_payload[k] = self.redact(v)
            elif isinstance(v, dict):
                redacted_payload[k] = self.redact_payload(v)
            elif isinstance(v, list):
                redacted_payload[k] = [self.redact(i) if isinstance(i, str) else i for i in v]
            else:
                redacted_payload[k] = v
        return redacted_payload

class ExternalStorageReference:
    """
    For highly compliant environments: store raw unredacted payloads in an isolated bucket,
    returning only a reference URL for the OTel span.
    """
    def __init__(self, bucket_name: str = "traceguard-secure-vault"):
        self.bucket_name = bucket_name
        
    def store_and_reference(self, raw_payload: Any, span_id: str) -> str:
        """
        Simulates storing the raw payload securely.
        Returns the reference URI.
        """
        return f"s3://{self.bucket_name}/payloads/{span_id}.json"
