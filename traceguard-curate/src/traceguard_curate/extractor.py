import sqlite3
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SpanData(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: int
    end_time: int
    status_code: str
    attributes: Dict[str, Any]
    events: List[Dict[str, Any]]

class TraceData(BaseModel):
    trace_id: str
    start_time: int
    spans: List[SpanData]

class TraceExtractor:
    """Extracts and groups spans from the SQLite trace database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def extract_all_traces(self) -> List[TraceData]:
        """Loads all traces from the database, grouped with their spans."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all traces
            cursor.execute("SELECT trace_id, start_time FROM traces ORDER BY start_time ASC")
            trace_rows = cursor.fetchall()
            
            # Get all spans
            cursor.execute("SELECT * FROM spans ORDER BY start_time ASC")
            span_rows = cursor.fetchall()
            conn.close()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

        # Group spans by trace_id
        spans_by_trace: Dict[str, List[SpanData]] = {}
        for row in span_rows:
            trace_id = row['trace_id']
            
            attributes = {}
            if row['attributes']:
                try:
                    attributes = json.loads(row['attributes'])
                except json.JSONDecodeError:
                    pass
                    
            events = []
            if row['events']:
                try:
                    events = json.loads(row['events'])
                except json.JSONDecodeError:
                    pass

            span = SpanData(
                span_id=row['span_id'],
                trace_id=trace_id,
                parent_span_id=row['parent_span_id'],
                name=row['name'],
                start_time=row['start_time'],
                end_time=row['end_time'],
                status_code=row['status_code'],
                attributes=attributes,
                events=events
            )
            
            if trace_id not in spans_by_trace:
                spans_by_trace[trace_id] = []
            spans_by_trace[trace_id].append(span)

        # Assemble traces
        traces = []
        for tr in trace_rows:
            t_id = tr['trace_id']
            traces.append(TraceData(
                trace_id=t_id,
                start_time=tr['start_time'],
                spans=spans_by_trace.get(t_id, [])
            ))
            
        return traces
