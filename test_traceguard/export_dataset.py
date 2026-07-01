import sys
import json
from traceguard_curate.extractor import TraceExtractor

if len(sys.argv) < 3:
    print("Usage: python export_dataset.py <db_path> <output_jsonl>")
    sys.exit(1)

db_path = sys.argv[1]
output = sys.argv[2]

extractor = TraceExtractor(db_path)
traces = extractor.extract_all_traces()

count = 0
with open(output, "w") as f:
    for t in traces:
        reason = ""
        total_cost = 0.0
        faithfulness_scores = []
        relevance_scores = []
        
        for s in t.spans:
            if s.status_code == "ERROR":
                reason += f"Span '{s.name}' threw an error."
            if s.attributes and s.attributes.get("exception.message") == "Limit Cycle":
                reason += " Limit Cycle"
                
            if s.attributes and "financial.cost_usd" in s.attributes:
                total_cost += float(s.attributes["financial.cost_usd"])
                
            if getattr(s, 'eval_faithfulness', None) is not None:
                faithfulness_scores.append(float(s.eval_faithfulness))
            if getattr(s, 'eval_relevance', None) is not None:
                relevance_scores.append(float(s.eval_relevance))
                
        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else None
                
        f.write(json.dumps({
            "trace_id": t.trace_id,
            "spans_count": len(t.spans),
            "reason": reason.strip(),
            "cost_usd": total_cost,
            "eval_faithfulness": avg_faithfulness,
            "eval_relevance": avg_relevance
        }) + "\n")
        count += 1
        
print(f"Exported {count} traces to {output}")
