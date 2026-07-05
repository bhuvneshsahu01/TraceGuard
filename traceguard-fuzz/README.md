# 🎯 traceguard-fuzz

**The Adversarial Security and Red Teaming Engine for TraceGuard.**

`traceguard-fuzz` uses Reinforcement Learning and Multimodal attacks to automatically stress-test and red-team your LLM agents in CI/CD pipelines.

## Installation

```bash
pip install traceguard-ai-fuzz
```

## Usage

Fuzzing an agent involves generating adversarial payloads and evaluating if your system sanitizes them properly.

### Python API

```python
from traceguard_fuzz.redteam import RLRedTeamAgent
from traceguard_fuzz.multimodal import AudioSanitizerAgent

# 1. Text-based Prompt Injection Fuzzing
red_team = RLRedTeamAgent(target_agent_id="customer-support-bot")

# Generate a targeted adversarial payload
payload = red_team.generate_attack()
print(f"Generated Payload: {payload}")

# 2. Multimodal Audio Attack Mitigation
# Filters out ultrasonic frequencies commonly used to bypass Voice LLMs
sanitizer = AudioSanitizerAgent(ultrasonic_threshold_khz=20.0)

clean_payload = sanitizer.sanitize_audio({"audio_data": {"peak_frequency_khz": 25.5}})
print(f"Sanitized Audio Payload: {clean_payload}")
```

### Multi-Model Harness

Fuzz your application across multiple provider models simultaneously to test cross-model security guardrails:

```python
from traceguard_fuzz.harness import MultiModelHarness

harness = MultiModelHarness(models=["gpt-4o", "claude-3-5-sonnet-20240620", "llama3"])
results = harness.run_eval("Analyze this potentially malicious payload", expected_output="Block")
```

## Features
- **RL-Driven Red Teaming**: Learns from failed attacks to generate highly evasive prompt injections.
- **Multimodal Defenses**: Guardrails for Voice LLMs and Vision inputs (e.g., blocking ultrasonic DolphinAttacks).
- **Multi-Model Harness**: Instantly route evaluation payloads across OpenAI, Anthropic, Google, and OpenRouter for robustness testing.
