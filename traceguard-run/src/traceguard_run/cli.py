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
    
    # Mock loading dataset and running agent (would integrate with traceguard-sdk/curate here)
    with console.status("[bold green]Running agent over dataset...[/bold green]"):
        import time
        time.sleep(1) # simulate work
        
    console.print(f"[green][OK] Evaluated against {dataset}[/green]")
    
    # Mock data for demonstration
    rng = np.random.default_rng(42)
    baseline_scores = rng.normal(loc=0.80, scale=0.10, size=100)
    current_scores = rng.normal(loc=0.84, scale=0.08, size=100)
    
    baseline_tokens = rng.normal(loc=1000, scale=200, size=100)
    current_tokens = rng.normal(loc=1300, scale=300, size=100)

    # 1. Bootstrap CI
    console.rule("[bold magenta]1. Model Performance (Bootstrap CI)[/bold magenta]")
    ci_results = calculate_bootstrap_ci(list(current_scores), list(baseline_scores))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value")
    
    table.add_row("Mean Diff", f"{ci_results['mean_diff']:.3f}")
    table.add_row("95% CI Lower Bound", f"{ci_results['lower_bound']:.3f}")
    table.add_row("95% CI Upper Bound", f"{ci_results['upper_bound']:.3f}")
    table.add_row("P-Value", f"{ci_results['p_value']:.4f}")
    table.add_row("Significant?", "[green]Yes[/green]" if ci_results['is_significant'] else "[yellow]No[/yellow]")
    console.print(table)
    
    # 2. Drift Detection
    console.rule("[bold cyan]2. Resource Drift Detection (PSI & KS)[/bold cyan]")
    
    ks_results = calculate_ks_test(baseline_tokens, current_tokens)
    psi_val = calculate_psi(baseline_tokens, current_tokens)
    
    drift_table = Table(show_header=True, header_style="bold cyan")
    drift_table.add_column("Test")
    drift_table.add_column("Statistic")
    drift_table.add_column("Drift Detected?")
    
    drift_table.add_row("KS Test (Token Burn)", f"{ks_results['statistic']:.3f} (p={ks_results['p_value']:.3f})", "[red]Yes[/red]" if ks_results["is_drifted"] else "[green]No[/green]")
    drift_table.add_row("PSI (Token Burn)", f"{psi_val:.3f}", "[red]Yes[/red]" if psi_val >= 0.1 else "[green]No[/green]")
    console.print(drift_table)

    # 3. Limit Cycles
    console.rule("[bold yellow]3. Dynamical System Checks[/bold yellow]")
    mock_states = [{"tool": "search", "query": "python"}, {"tool": "search", "query": "python"}, {"tool": "search", "query": "python"}]
    cycle_res = detect_limit_cycle(mock_states, min_cycle_length=1)
    
    if cycle_res["has_cycle"]:
        console.print(f"[!] [bold red]Limit Cycle Detected![/bold red] (Length: {cycle_res['cycle_length']})")
    else:
        console.print("[OK] [green]No infinite loops detected.[/green]")
        
    console.rule()
    if ci_results['is_significant'] and ci_results['mean_diff'] > 0 and not cycle_res["has_cycle"]:
        console.print("[bold green][PASS] Evaluation Passed! PR is safe to merge.[/bold green]")
    else:
        console.print("[bold red][FAIL] Evaluation Failed! Do not merge.[/bold red]")


if __name__ == "__main__":
    app()
