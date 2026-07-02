# Evaluation & Calibration

## Constructor/Auditor/Judge Triad
TraceGuard utilizes Multi-Agent Debate to eliminate LLM-as-a-Judge biases (verbosity, position bias).
1. The **Constructor Agent** defends the answer.
2. The **Auditor Agent** ruthlessly critiques the answer.
3. The **Judge Agent** scores the objective debate context.

## Isotonic Calibration
LLM Log probabilities are mathematically flawed. TraceGuard's `IsotonicCalibrator` uses historical human labels to build a piecewise empirical function. It maps a model's raw 90% confidence score to the actual statistical reality (e.g., it may only be correct 60% of the time when it claims 90%).
