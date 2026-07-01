import os
import sys
import json
import sqlite3
from typing import Dict, Any
from dotenv import load_dotenv
from groq import Groq

def setup_db(db_path: str):
    """Ensure the spans table has columns for semantic scores."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if we need to add columns to the spans table for unit economics and semantic scores
    cursor.execute("PRAGMA table_info(spans)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "eval_faithfulness" not in columns:
        cursor.execute("ALTER TABLE spans ADD COLUMN eval_faithfulness REAL")
    if "eval_relevance" not in columns:
        cursor.execute("ALTER TABLE spans ADD COLUMN eval_relevance REAL")
    if "eval_rationale" not in columns:
        cursor.execute("ALTER TABLE spans ADD COLUMN eval_rationale TEXT")
        
    conn.commit()
    return conn

def evaluate_span(client: Groq, context: str, response: str) -> Dict[str, Any]:
    """Uses LLM-as-a-Judge to evaluate Faithfulness and Relevance."""
    
    prompt = f"""You are an expert AI evaluator calculating the RAG Triad.
Evaluate the following response based on the provided context.

[CONTEXT]
{context}

[RESPONSE]
{response}

Score the following metrics on a scale of 0.0 to 1.0 (where 1.0 is perfect):
1. faithfulness: Is the response entirely supported by the context without any hallucinations?
2. relevance: Is the response helpful and on-topic?

Return ONLY a JSON object with this exact schema:
{{
    "faithfulness": 0.0,
    "relevance": 0.0,
    "rationale": "short explanation"
}}
"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        result_str = completion.choices[0].message.content
        return json.loads(result_str)
    except Exception as e:
        print(f"Error calling Judge LLM: {e}")
        return {"faithfulness": 0.0, "relevance": 0.0, "rationale": f"Eval failed: {str(e)}"}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="TraceGuard Judge: Enterprise LLM-as-a-Judge Evaluation")
    parser.add_argument("--db", type=str, default=".traceguard.db", help="Path to SQLite trace database")
    args = parser.parse_args()
    
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'test_traceguard', '.env'))
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not found.")
        sys.exit(1)
        
    client = Groq(api_key=api_key)
    conn = setup_db(args.db)
    cursor = conn.cursor()
    
    print(f"Evaluating traces in {args.db}...")
    
    # Find spans that have a RAG context and an LLM result, but haven't been evaluated yet
    cursor.execute("SELECT span_id, attributes FROM spans WHERE attributes LIKE '%rag.context%' AND eval_faithfulness IS NULL")
    rows = cursor.fetchall()
    
    evaluated = 0
    for span_id, attributes_json in rows:
        try:
            attrs = json.loads(attributes_json)
            context = attrs.get("rag.context")
            result = attrs.get("output.result")
            
            if context and result:
                print(f"Evaluating span {span_id}...")
                scores = evaluate_span(client, str(context), str(result))
                
                cursor.execute(
                    "UPDATE spans SET eval_faithfulness = ?, eval_relevance = ?, eval_rationale = ? WHERE span_id = ?",
                    (scores.get("faithfulness", 0.0), scores.get("relevance", 0.0), scores.get("rationale", ""), span_id)
                )
                conn.commit()
                evaluated += 1
                
        except Exception as e:
            print(f"Failed to evaluate span {span_id}: {e}")
            
    print(f"Successfully evaluated {evaluated} spans.")
    conn.close()

if __name__ == "__main__":
    main()
