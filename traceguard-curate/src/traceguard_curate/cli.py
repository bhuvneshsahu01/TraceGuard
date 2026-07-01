import typer
from rich.console import Console
import json
import os
from .extractor import TraceExtractor
from .rules import AnomalyEngine, ErrorRule, LatencyRule

app = typer.Typer(help="TraceGuard Curation Pipeline")
console = Console()

@app.command()
def extract(
    db_path: str = typer.Option(".traceguard.db", help="Path to the SQLite database"),
    output: str = typer.Option("test_cases.jsonl", help="Output JSON Lines file for curated datasets"),
    max_latency: int = typer.Option(5000000000, help="Max latency threshold in nanoseconds (default 5s)")
):
    """
    Scans the trace database, runs anomaly detection, and saves flagged traces as test cases.
    """
    console.rule("[bold blue]TraceGuard Dataset Curation[/bold blue]")
    
    if not os.path.exists(db_path):
        console.print(f"[bold red]Database {db_path} not found![/bold red]")
        raise typer.Exit(code=1)
        
    extractor = TraceExtractor(db_path)
    engine = AnomalyEngine(rules=[ErrorRule(), LatencyRule(max_latency_ns=max_latency)])
    
    with console.status(f"[bold green]Scanning {db_path}...[/bold green]"):
        traces = extractor.extract_all_traces()
        
    curated_count = 0
    with open(output, "w") as f:
        for trace in traces:
            anomaly_result = engine.check_trace(trace)
            if anomaly_result.is_anomalous:
                # We save this trace as a test case for future evaluation
                test_case = {
                    "trace_id": trace.trace_id,
                    "reason": anomaly_result.reason,
                    # For a real dataset, we'd extract the specific inputs/outputs that caused the anomaly
                    "spans_count": len(trace.spans)
                }
                f.write(json.dumps(test_case) + "\n")
                curated_count += 1
                
    console.print(f"[green][OK] Scanned {len(traces)} traces.[/green]")
    console.print(f"[bold magenta]Curated {curated_count} anomalous traces into {output}[/bold magenta]")
    console.rule()

if __name__ == "__main__":
    app()
