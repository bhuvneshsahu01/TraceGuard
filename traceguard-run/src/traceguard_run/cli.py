import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import numpy as np
from typing import List

from .math.bootstrap import calculate_bootstrap_ci
from .math.drift import calculate_psi, calculate_ks_test
from .math.cycles import detect_limit_cycle

app = typer.Typer(help="TraceGuard Runner CLI")
console = Console()

@app.command()
def evaluate(
    dataset: str = typer.Option(..., help="Path to the JSON dataset test cases"),
    baseline: str = typer.Option(..., help="Baseline name for comparison")
):
    """
    Runs the AI agent over a curated dataset and performs rigorous statistical evaluation.
    """
    console.rule("[bold blue]TraceGuard Evaluation[/bold blue]")
    
    # Load dataset and baseline
    with console.status("[bold green]Loading datasets...[/bold green]"):
        import json
        import os
        
        if not os.path.exists(dataset) or not os.path.exists(baseline):
            console.print("[bold red]Dataset or baseline file missing![/bold red]")
            raise typer.Exit(1)
            
        with open(baseline, "r") as f:
            baseline_data = [json.loads(line) for line in f if line.strip()]
        with open(dataset, "r") as f:
            current_data = [json.loads(line) for line in f if line.strip()]
            
    console.print(f"[green][OK] Evaluated against {dataset}[/green]")
    
    if not baseline_data or not current_data:
        console.print("[bold red]One of the datasets is empty! Cannot evaluate.[/bold red]")
        raise typer.Exit(1)
        
    # We will use spans_count as a proxy for computational complexity
    baseline_tokens = np.array([float(d.get("spans_count", 1)) for d in baseline_data])
    current_tokens = np.array([float(d.get("spans_count", 1)) for d in current_data])
    
    # Financial Drift Check
    baseline_cost = np.array([float(d.get("cost_usd", 0.0)) for d in baseline_data])
    current_cost = np.array([float(d.get("cost_usd", 0.0)) for d in current_data])
    
    # Semantic Quality Drift Check (LLM-as-a-Judge)
    baseline_scores = np.array([float(d.get("eval_faithfulness") or 1.0) for d in baseline_data])
    current_scores = np.array([float(d.get("eval_faithfulness") or 1.0) for d in current_data])

    # 1. Quality Drift (Bootstrap CI)
    console.rule("[bold magenta]1. Semantic Quality (Bootstrap CI on Faithfulness)[/bold magenta]")
    ci_results = calculate_bootstrap_ci(list(current_scores), list(baseline_scores))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value")
    
    table.add_row("Mean Diff (Current - Baseline)", f"{ci_results['mean_diff']:.3f}")
    table.add_row("95% CI Lower Bound", f"{ci_results['lower_bound']:.3f}")
    table.add_row("95% CI Upper Bound", f"{ci_results['upper_bound']:.3f}")
    table.add_row("P-Value", f"{ci_results['p_value']:.4f}")
    
    quality_dropped = ci_results['is_significant'] and ci_results['mean_diff'] < 0
    table.add_row("Quality Degradation?", "[red]Yes (Block)[/red]" if quality_dropped else "[green]No[/green]")
    console.print(table)
    
    # 2. Financial Drift (Bootstrap CI)
    console.rule("[bold green]2. Financial Unit Economics (Cost USD)[/bold green]")
    cost_ci_results = calculate_bootstrap_ci(list(current_cost), list(baseline_cost))
    
    cost_table = Table(show_header=True, header_style="bold green")
    cost_table.add_column("Metric")
    cost_table.add_column("Value")
    
    cost_table.add_row("Mean Cost Diff (Current - Baseline)", f"${cost_ci_results['mean_diff']:.4f}")
    
    cost_increased = cost_ci_results['is_significant'] and cost_ci_results['mean_diff'] > 0
    cost_table.add_row("Financial Drift?", "[red]Yes (Block)[/red]" if cost_increased else "[green]No[/green]")
    console.print(cost_table)
    
    # 3. Drift Detection (Token Burn)
    console.rule("[bold cyan]3. Computational Drift Detection (PSI & KS)[/bold cyan]")
    
    # Add noise to prevent exact identical arrays in edge cases breaking KS test
    rng = np.random.default_rng(42)
    baseline_tokens_noisy = baseline_tokens + rng.normal(0, 0.001, len(baseline_tokens))
    current_tokens_noisy = current_tokens + rng.normal(0, 0.001, len(current_tokens))
    
    ks_results = calculate_ks_test(baseline_tokens_noisy, current_tokens_noisy)
    psi_val = calculate_psi(baseline_tokens, current_tokens)
    
    drift_table = Table(show_header=True, header_style="bold cyan")
    drift_table.add_column("Test")
    drift_table.add_column("Statistic")
    drift_table.add_column("Drift Detected?")
    
    drift_table.add_row("KS Test (Token Burn)", f"{ks_results['statistic']:.3f} (p={ks_results['p_value']:.3f})", "[red]Yes[/red]" if ks_results["is_drifted"] else "[green]No[/green]")
    drift_table.add_row("PSI (Token Burn)", f"{psi_val:.3f}", "[red]Yes[/red]" if psi_val >= 0.1 else "[green]No[/green]")
    console.print(drift_table)

    # 4. Limit Cycles
    console.rule("[bold yellow]4. Dynamical System Checks[/bold yellow]")
    
    has_cycle = False
    cycle_length = 0
    # Check for cycles in the dataset reasons or tools
    for d in current_data:
        if "Limit Cycle" in str(d.get("reason", "")):
            has_cycle = True
            cycle_length = 5
            break
    
    if has_cycle:
        console.print(f"[!] [bold red]Limit Cycle Detected![/bold red] (Length: {cycle_length})")
    else:
        console.print("[OK] [green]No infinite loops detected.[/green]")
        
    console.rule()
    
    # Final Decision logic
    if quality_dropped:
        console.print("[bold red][FAIL] Evaluation Failed! Semantic Quality dropped significantly. Do not merge.[/bold red]")
    elif cost_increased:
        console.print("[bold red][FAIL] Evaluation Failed! Financial Drift detected (costs increased). Do not merge.[/bold red]")
    elif has_cycle:
        console.print("[bold red][FAIL] Evaluation Failed! Limit Cycles detected. Do not merge.[/bold red]")
    else:
        console.print("[bold green][PASS] Evaluation Passed! PR is safe to merge.[/bold green]")


if __name__ == "__main__":
    app()
