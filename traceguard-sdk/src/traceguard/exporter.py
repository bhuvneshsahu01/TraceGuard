import sqlite3
import json
import logging
from typing import Sequence
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)

class SQLiteSpanExporter(SpanExporter):
    """
    Exports OpenTelemetry spans to a local SQLite database.
    Optimized for fast batch inserts.
    """
    def __init__(self, db_path: str = ".traceguard.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # Use isolation_level=None for autocommit, or handle transactions manually.
        # We handle transactions manually in export for batching.
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self) -> None:
        """Initializes the SQLite schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    start_time INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    name TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    status_code TEXT NOT NULL,
                    attributes TEXT,
                    events TEXT
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id)')
            conn.commit()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if not spans:
            return SpanExportResult.SUCCESS
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert traces (ignore if already exists)
                traces_data = [
                    (
                        format(span.context.trace_id, '032x'),
                        span.start_time
                    )
                    for span in spans if span.parent is None
                ]
                
                if traces_data:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO traces (trace_id, start_time)
                        VALUES (?, ?)
                    ''', traces_data)

                # Insert spans
                spans_data = []
                for span in spans:
                    trace_id_hex = format(span.context.trace_id, '032x')
                    span_id_hex = format(span.context.span_id, '016x')
                    parent_id_hex = format(span.parent.span_id, '016x') if span.parent else None
                    
                    attributes_json = json.dumps(dict(span.attributes)) if span.attributes else None
                    
                    events_list = []
                    for event in span.events:
                        events_list.append({
                            "name": event.name,
                            "timestamp": event.timestamp,
                            "attributes": dict(event.attributes) if event.attributes else {}
                        })
                    events_json = json.dumps(events_list) if events_list else None
                    
                    spans_data.append((
                        span_id_hex,
                        trace_id_hex,
                        parent_id_hex,
                        span.name,
                        span.start_time,
                        span.end_time,
                        span.status.status_code.name if span.status else "UNSET",
                        attributes_json,
                        events_json
                    ))

                cursor.executemany('''
                    INSERT OR REPLACE INTO spans 
                    (span_id, trace_id, parent_span_id, name, start_time, end_time, status_code, attributes, events)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', spans_data)
                
                conn.commit()
            return SpanExportResult.SUCCESS
        except Exception as e:
            logger.error(f"Failed to export spans to SQLite: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Called when the TracerProvider shuts down."""
        pass
