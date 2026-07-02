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


    def _get_connection(self):
        if self.is_postgres:
            import psycopg2
            return psycopg2.connect(self.db_url)
        else:
            import sqlite3
            return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                # Postgres schema creation is handled by Prisma via Next.js
                # We just verify connection here
                pass
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS traces (
                        trace_id TEXT PRIMARY KEY,
                        start_time INTEGER
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS spans (
                        span_id TEXT PRIMARY KEY,
                        trace_id TEXT,
                        parent_span_id TEXT,
                        name TEXT,
                        start_time INTEGER,
                        end_time INTEGER,
                        status_code TEXT,
                        attributes TEXT,
                        events TEXT,
                        FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
                    )
                ''')
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
                    if self.is_postgres:
                        try:
                            # Postgres syntax
                            from psycopg2.extras import execute_values
                            execute_values(cursor, 'INSERT INTO traces (trace_id, start_time) VALUES %s ON CONFLICT DO NOTHING', traces_data)
                        except Exception:
                            pass
                    else:
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

                if self.is_postgres:
                    from psycopg2.extras import execute_values
                    execute_values(cursor, '''
                        INSERT INTO spans 
                        (span_id, trace_id, parent_span_id, name, start_time, end_time, status_code, attributes, events)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                    ''', spans_data)
                else:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO spans 
                        (span_id, trace_id, parent_span_id, name, start_time, end_time, status_code, attributes, events)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', spans_data)
                
                conn.commit()
            return SpanExportResult.SUCCESS
        except Exception as e:
            logger.error(f"Failed to export spans to DB: {e}")
            return SpanExportResult.FAILURE

    def reconstruct_swarm_dag(self, swarm_id: str) -> list[dict]:
        """
        Graph Aggregation Engine (Phase 21).
        Dynamically reconstructs a non-linear DAG out of standard OTel spans
        using the 'gen_ai.agent.swarm.id' attribute, enabling cross-vendor portability
        even if standard parent-child trace links are broken across distributed boundaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch all spans containing the swarm_id in attributes
            cursor.execute('''
                SELECT span_id, parent_span_id, name, attributes 
                FROM spans 
                WHERE attributes LIKE ?
            ''', (f'%"{swarm_id}"%',))
            
            rows = cursor.fetchall()
            
        # Reconstruct graph locally
        nodes = {}
        for row in rows:
            attrs = json.loads(row[3]) if row[3] else {}
            # Verify exact attribute match to avoid SQL LIKE false positives
            if attrs.get("gen_ai.agent.swarm.id") == swarm_id:
                nodes[row[0]] = {
                    "id": row[0],
                    "parent_id": row[1],
                    "name": row[2],
                    "attributes": attrs,
                    "children": []
                }
                
        # Build tree structure
        roots = []
        for span_id, node in nodes.items():
            parent = node["parent_id"]
            if parent and parent in nodes:
                nodes[parent]["children"].append(node)
            else:
                roots.append(node)
                
        return roots

    def shutdown(self) -> None:
        """Called when the TracerProvider shuts down."""
        pass

def get_enterprise_exporters() -> list[SpanExporter]:
    """
    Returns a list of all active exporters.
    Always includes SQLiteSpanExporter.
    If OTLP endpoint is set, adds OTLPSpanExporter (Phase 31).
    """
    import os
    exporters = [SQLiteSpanExporter()]
    
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        logger.info(f"TraceGuard Enterprise OTLP Export enabled: {otlp_endpoint}")
        exporters.append(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        
    return exporters
