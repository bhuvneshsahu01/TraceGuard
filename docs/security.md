# Security Firewalls

## Audio & Visual Sanitization
TraceGuard uses advanced heuristic and machine-learning agents to sanitize multimodal inputs.
For example, the `AudioSanitizerAgent` runs FFT (Fast Fourier Transforms) to detect ultrasonic frequencies (like DolphinAttack payloads) hidden in `.wav` files before they reach your speech-to-text models.

## Differential Exfiltration Monitoring
TraceGuard actively defends against RAG poisoning via the `SemanticDLPEngine`. By analyzing the ratio between inbound context tokens and outbound API tool tokens, TraceGuard detects if a malicious prompt is attempting to dump the entirety of your backend database to an external server.
