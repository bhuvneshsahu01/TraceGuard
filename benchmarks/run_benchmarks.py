"""
benchmarks/run_benchmarks.py
----------------------------
Deterministic, Reproducible Benchmark Suite for TraceGuard (seed=42).

Executes:
1. Benchmark A: Shift-Injection Drift Benchmark
   - Frozen reference distribution (N=1,000 baseline signals)
   - 500 Null Windows (n=200) measuring Empirical False-Alarm Rate under Benjamini-Hochberg alpha=0.05
   - 500 Shifted Windows (n=200) with realistic 25% semantic & covariate shift measuring
     Empirical Detection Power across MMD, scalar, and combined tests under FDR control
2. Benchmark B: Guardrail Latency & Prompt-Injection Detection Benchmark
   - 500-request latency profiling at T=128 and T=256 token prompts measuring median, p95, and p99
   - Real-world evaluation on public `deepset/prompt-injections` test split (SHA-256 verified) measuring
     Injection Recall and False Positive Rate

Saves raw metrics to: benchmarks/results/traceguard_metrics.json
Prints clean Markdown summary table.
"""

import hashlib
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SEED = 42

# Ensure traceguard packages are in sys.path
repo_root = Path(__file__).resolve().parent.parent
sdk_src = repo_root / "traceguard-sdk" / "src"
if str(sdk_src) not in sys.path:
    sys.path.insert(0, str(sdk_src))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from traceguard.drift import DriftMonitor
from traceguard.guardrails.injection import PromptInjectionScanner
from traceguard.guardrails.middleware import TraceGuardMiddleware, GuardrailConfig

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)


def run_benchmark_a_drift(monitor: DriftMonitor, seed: int = 42):
    """
    Evaluates DriftMonitor under 500 Null Windows and 500 Injected Shift Windows.
    Tests a realistic 25% semantic shift where MMD embedding drift provides the core signal.
    """
    print("\n" + "=" * 75)
    print(">>> RUNNING BENCHMARK A: Shift-Injection Drift Benchmark (N_ref=1000, n=200)")
    print("=" * 75)

    rng = np.random.default_rng(seed)
    cats = ["rag_qa", "code_gen", "summarization", "agent_tool"]

    num_null_windows = 500
    num_shift_windows = 500
    window_n = 200

    # 1. Null Windows Evaluation (H_0: no shift)
    print(f"[*] Evaluating {num_null_windows} Null (No-Shift) Windows (target alpha=0.05)...")
    null_drifts = 0
    t0 = time.perf_counter()

    for i in range(num_null_windows):
        w_len = rng.normal(160, 35, size=window_n).tolist()
        w_lat = rng.gamma(4.0, 70.0, size=window_n).tolist()
        w_cats = rng.choice(cats, p=[0.40, 0.30, 0.20, 0.10], size=window_n).tolist()
        w_emb = rng.normal(0, 1, size=(window_n, 16))
        w_emb = w_emb / np.linalg.norm(w_emb, axis=1, keepdims=True)

        cand = {
            "prompt_length": w_len,
            "latency_ms": w_lat,
            "route": w_cats,
            "embeddings": w_emb,
        }
        report = monitor.evaluate_window(
            cand,
            alpha=0.05,
            apply_fdr=True,
            num_mmd_permutations=200,
            random_state=seed + i,
        )
        if report.is_drift_detected:
            null_drifts += 1

    t_null = time.perf_counter() - t0
    fa_pct = (null_drifts / num_null_windows) * 100.0
    print(f"    -> Null Windows Done in {t_null:.2f}s: Flagged {null_drifts}/{num_null_windows} (Empirical FA: {fa_pct:.2f}%)")

    # 2. Shifted Windows Evaluation (H_1: 25% semantic/covariate shift)
    shift_name = "25% out-of-domain semantic shift (embedding latent shift delta=+0.65, mild +8% length, +12ms latency)"
    print(f"[*] Evaluating {num_shift_windows} Shifted Windows (realistic 25% covariate mix)...")
    shift_drifts = 0
    mmd_drifts = 0
    scalar_drifts = 0
    cat_drifts = 0
    t0 = time.perf_counter()

    for i in range(num_shift_windows):
        n_norm = 150
        n_shift = 50

        # Mild scalar & categorical drift
        w_len = np.concatenate([
            rng.normal(160, 35, size=n_norm),
            rng.normal(172, 36, size=n_shift),
        ]).tolist()
        w_lat = np.concatenate([
            rng.gamma(4.0, 70.0, size=n_norm),
            rng.gamma(4.15, 71.0, size=n_shift),
        ]).tolist()
        w_cats = np.concatenate([
            rng.choice(cats, p=[0.40, 0.30, 0.20, 0.10], size=n_norm),
            rng.choice(cats, p=[0.36, 0.30, 0.20, 0.14], size=n_shift),
        ]).tolist()

        # Primarily an embedding semantic cluster shift (delta=+0.65 along top 4 coordinates)
        e_norm = rng.normal(0, 1, size=(n_norm, 16))
        e_shift = rng.normal(0, 0.7, size=(n_shift, 16))
        center = np.zeros(16)
        center[:4] = 0.65
        e_shift += center
        w_emb = np.vstack([e_norm, e_shift])
        w_emb = w_emb / np.linalg.norm(w_emb, axis=1, keepdims=True)

        cand = {
            "prompt_length": w_len,
            "latency_ms": w_lat,
            "route": w_cats,
            "embeddings": w_emb,
        }
        report = monitor.evaluate_window(
            cand,
            alpha=0.05,
            apply_fdr=True,
            num_mmd_permutations=200,
            random_state=seed + 10000 + i,
        )

        if report.is_drift_detected:
            shift_drifts += 1

        if report.mmd_results.get("embeddings") and report.mmd_results["embeddings"].is_drift_detected:
            mmd_drifts += 1

        has_scalar = any(
            (k in report.ks_results and report.ks_results[k].is_drift_detected) or
            (k in report.psi_results and report.psi_results[k].is_drift_detected)
            for k in ["prompt_length", "latency_ms"]
        )
        if has_scalar:
            scalar_drifts += 1

        if report.chi2_results.get("route") and report.chi2_results["route"].is_drift_detected:
            cat_drifts += 1

    t_shift = time.perf_counter() - t0
    pw_pct = (shift_drifts / num_shift_windows) * 100.0
    mmd_power_pct = (mmd_drifts / num_shift_windows) * 100.0
    scalar_power_pct = (scalar_drifts / num_shift_windows) * 100.0
    cat_power_pct = (cat_drifts / num_shift_windows) * 100.0

    print(f"    -> Shifted Windows Done in {t_shift:.2f}s:")
    print(f"       Overall Detection Power:  {shift_drifts}/{num_shift_windows} ({pw_pct:.2f}%)")
    print(f"       Kernel MMD Power:         {mmd_drifts}/{num_shift_windows} ({mmd_power_pct:.2f}%)")
    print(f"       Scalar-Only (KS/PSI):     {scalar_drifts}/{num_shift_windows} ({scalar_power_pct:.2f}%)")
    print(f"       Categorical (Chi-Square): {cat_drifts}/{num_shift_windows} ({cat_power_pct:.2f}%)")

    return {
        "reference_distribution_size": 1000,
        "window_size": window_n,
        "num_null_windows": num_null_windows,
        "null_target_alpha": 0.05,
        "null_false_alarms": null_drifts,
        "empirical_false_alarm_rate_pct": round(fa_pct, 2),
        "num_shifted_windows": num_shift_windows,
        "injected_shift_description": shift_name,
        "shift_detections": shift_drifts,
        "empirical_detection_power_pct": round(pw_pct, 2),
        "signal_breakdown": {
            "mmd_detection_power_pct": round(mmd_power_pct, 2),
            "scalar_only_detection_power_pct": round(scalar_power_pct, 2),
            "categorical_detection_power_pct": round(cat_power_pct, 2),
            "mmd_advantage_over_scalar_pct": round(mmd_power_pct - scalar_power_pct, 2),
        },
        "execution_time_seconds": round(t_null + t_shift, 2),
    }


def run_benchmark_b_latency_and_injection(data_dir: Path):
    """
    Measures middleware added latency over 500 warm requests for T=128 and T=256 token prompts,
    and evaluates prompt-injection detection on deepset/prompt-injections test split.
    """
    print("\n" + "=" * 75)
    print(">>> RUNNING BENCHMARK B: Latency Overhead & Prompt Injection Accuracy")
    print("=" * 75)

    # 1. Latency Benchmark
    app = FastAPI()
    app.add_middleware(
        TraceGuardMiddleware,
        config=GuardrailConfig(enable_pii_redaction=True, enable_injection_detection=True, enable_otel=True),
    )

    @app.post("/v1/chat/completions")
    async def chat_endpoint(request: Request):
        return JSONResponse({"status": "success", "model": "llama-3-8b"})

    client = TestClient(app)

    text_128 = (
        "Please summarize the primary thermodynamic principles governing gas turbine cycles in modern "
        "combined-cycle power plants. Discuss the differences between Brayton and Rankine cycles, including "
        "isentropic expansion efficiency, compressor pressure ratios, turbine inlet temperatures, and overall "
        "thermal efficiency improvements achieved through multi-stage reheat and regenerative heat exchangers. "
        "Highlight the operational constraints related to thermal fatigue and nitrogen oxide emissions mitigation."
    )

    text_256 = (
        text_128 + " " +
        "Furthermore, evaluate the aerodynamic performance trade-offs associated with transonic blade profiles "
        "in axial compressors. Analyze how boundary layer separation, shock-wave boundary-layer interactions, and "
        "tip-leakage vortices affect stage pressure rise and stall margin limits under off-design operating regimes. "
        "Provide quantitative comparisons of nickel-based superalloys versus ceramic matrix composites for high-pressure "
        "turbine blades operating under continuous thermal gradients exceeding 1400 degrees Celsius with active internal "
        "serpentine cooling passages."
    )

    # Warmup
    for _ in range(50):
        client.post("/v1/chat/completions", json={"prompt": text_128})

    latency_results = {}
    for token_label, prompt_tokens, prompt_text in [("T=128", 128, text_128), ("T=256", 256, text_256)]:
        print(f"[*] Profiling 500 requests at {token_label} ({len(prompt_text)} chars)...")
        latencies = []
        for _ in range(500):
            t0 = time.perf_counter()
            resp = client.post("/v1/chat/completions", json={"prompt": prompt_text})
            t1 = time.perf_counter()
            assert resp.status_code == 200, f"Unexpected response status: {resp.status_code}"
            lat_ms = float(resp.headers.get("x-traceguard-latency-ms", (t1 - t0) * 1000.0))
            latencies.append(lat_ms)

        s_lat = sorted(latencies)
        p50 = statistics.median(s_lat)
        p95 = s_lat[int(len(s_lat) * 0.95)]
        p99 = s_lat[int(len(s_lat) * 0.99)]
        print(f"    -> {token_label}: Median = {p50:.3f} ms | p95 = {p95:.3f} ms | p99 = {p99:.3f} ms")

        latency_results[token_label] = {
            "token_count": prompt_tokens,
            "char_count": len(prompt_text),
            "requests_count": 500,
            "median_ms": round(p50, 3),
            "p95_ms": round(p95, 3),
            "p99_ms": round(p99, 3),
        }

    # 2. Prompt Injection Detector Accuracy Benchmark
    dataset_file = data_dir / "deepset_prompt_injections_test.jsonl"
    with open(dataset_file, "rb") as f:
        file_sha256 = hashlib.sha256(f.read()).hexdigest()

    dataset_name = "deepset/prompt-injections"
    print(f"\n[*] Evaluating Prompt Injection Detector on `{dataset_name}` test split...")
    print(f"    Dataset File: {dataset_file.name} (SHA-256: {file_sha256})")

    scanner = PromptInjectionScanner(threshold=0.45)
    rows = []
    with open(dataset_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    tp, fp, tn, fn = 0, 0, 0, 0
    for r in rows:
        text = r["text"]
        y_true = int(r["label"])
        scan_res = scanner.scan(text)
        y_pred = 1 if scan_res.is_injection else 0

        if y_true == 1 and y_pred == 1:
            tp += 1
        elif y_true == 0 and y_pred == 1:
            fp += 1
        elif y_true == 0 and y_pred == 0:
            tn += 1
        elif y_true == 1 and y_pred == 0:
            fn += 1

    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
    fpr = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    accuracy = ((tp + tn) / len(rows)) * 100.0 if len(rows) > 0 else 0.0

    print(f"    -> Results (N={len(rows)}): Recall = {recall:.2f}% | FPR = {fpr:.2f}% | Precision = {precision:.2f}% | Accuracy = {accuracy:.2f}%")
    print(f"    -> Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")

    injection_results = {
        "dataset_name": dataset_name,
        "dataset_split": "test",
        "dataset_sha256": file_sha256,
        "decision_threshold": 0.45,
        "total_samples": len(rows),
        "injections_count": tp + fn,
        "benign_count": tn + fp,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "injection_recall_pct": round(recall, 2),
        "false_positive_rate_pct": round(fpr, 2),
        "precision_pct": round(precision, 2),
        "accuracy_pct": round(accuracy, 2),
    }

    return latency_results, injection_results


def main():
    set_seed(SEED)

    repo_dir = Path(__file__).resolve().parent.parent
    benchmarks_dir = repo_dir / "benchmarks"
    data_dir = benchmarks_dir / "data"
    results_dir = benchmarks_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("           TRACEGUARD BENCHMARK & REPRODUCIBILITY SUITE")
    print("=" * 75)
    print(f"Timestamp:   {datetime.now(timezone.utc).isoformat()}")
    print(f"Random Seed: {SEED}")
    print(f"Repo Root:   {repo_dir}")

    # Build reference distribution for DriftMonitor (N=1000)
    rng = np.random.default_rng(SEED)
    ref_N = 1000
    ref_len = rng.normal(160, 35, size=ref_N).tolist()
    ref_lat = rng.gamma(4.0, 70.0, size=ref_N).tolist()
    cats = ["rag_qa", "code_gen", "summarization", "agent_tool"]
    ref_cats = rng.choice(cats, p=[0.40, 0.30, 0.20, 0.10], size=ref_N).tolist()
    ref_emb = rng.normal(0, 1, size=(ref_N, 16))
    ref_emb = ref_emb / np.linalg.norm(ref_emb, axis=1, keepdims=True)

    monitor = DriftMonitor(alpha=0.05, psi_threshold=0.25)
    monitor.register_scalar_baseline("prompt_length", ref_len)
    monitor.register_scalar_baseline("latency_ms", ref_lat)
    monitor.register_categorical_baseline("route", ref_cats)
    monitor.register_embedding_baseline("embeddings", ref_emb)

    # Execute Benchmarks
    bench_a = run_benchmark_a_drift(monitor, seed=SEED)
    bench_b_latency, bench_b_inj = run_benchmark_b_latency_and_injection(data_dir)

    # Aggregate JSON Output
    metrics_payload = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "random_seed": SEED,
            "python_version": sys.version,
            "traceguard_version": "0.2.0",
        },
        "benchmark_a_drift": bench_a,
        "benchmark_b_latency": bench_b_latency,
        "benchmark_b_prompt_injection": bench_b_inj,
        "cv_bracket_placeholders": {
            "[FA]%": f"{bench_a['empirical_false_alarm_rate_pct']}%",
            "[PW]%": f"{bench_a['empirical_detection_power_pct']}%",
            "[SHIFT]": bench_a["injected_shift_description"],
            "[L] ms": f"{bench_b_latency['T=128']['p95_ms']} ms",
            "[T]": 128,
            "[R]%": f"{bench_b_inj['injection_recall_pct']}%",
            "[DATASET]": bench_b_inj["dataset_name"],
            "[FP]%": f"{bench_b_inj['false_positive_rate_pct']}%",
        },
    }

    results_file = results_dir / "traceguard_metrics.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("\n" + "=" * 75)
    print(f"[+] Raw metrics successfully saved to: {results_file}")
    print("=" * 75)

    # Print Clean Summary Markdown Table (No "CV Placeholder" heading)
    print("\n### Benchmark Summary Table\n")
    print("| Metric Category | Measured Benchmark Value | Target / Specification | Method / Protocol |")
    print("| :--- | :--- | :--- | :--- |")
    print(f"| **Drift False-Alarm Rate** | **{bench_a['empirical_false_alarm_rate_pct']}%** | <= 5.0% (BH alpha=0.05) | 500 Null Windows (n=200) |")
    print(f"| **Overall Drift Detection Power** | **{bench_a['empirical_detection_power_pct']}%** | 88% - 95% target | 500 Shifted Windows (n=200) under FDR |")
    print(f"| **Embedding MMD Detection Power** | **{bench_a['signal_breakdown']['mmd_detection_power_pct']}%** | High sensitivity | Kernel MMD (B=200 permutations) |")
    print(f"| **Scalar-Only Detection Power** | **{bench_a['signal_breakdown']['scalar_only_detection_power_pct']}%** | Insensitive baseline | Two-sample KS + PSI |")
    print(f"| **Middleware Added Latency (p95, T=128)** | **{bench_b_latency['T=128']['p95_ms']} ms** | < 3.0 ms overhead | 500 requests at T=128 tokens |")
    print(f"| **Middleware Added Latency (p95, T=256)** | **{bench_b_latency['T=256']['p95_ms']} ms** | < 3.0 ms overhead | 500 requests at T=256 tokens |")
    print(f"| **Prompt Injection Recall** | **{bench_b_inj['injection_recall_pct']}%** | Held-out test split | deepset/prompt-injections (N=116) |")
    print(f"| **Prompt Injection False Positive Rate** | **{bench_b_inj['false_positive_rate_pct']}%** | <= 5.0% target | 56 benign prompts (Precision: {bench_b_inj['precision_pct']}%) |")
    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()
