import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from .exporter import SQLiteSpanExporter

def configure_traceguard(db_path: str = ".traceguard.db") -> None:
    """
    Configures OpenTelemetry TracerProvider and BatchSpanProcessor 
    to export to the local SQLite database.
    """
    provider = TracerProvider()
    
    # Initialize the custom SQLite exporter
    exporter = SQLiteSpanExporter(db_path=db_path)
    
    # Use BatchSpanProcessor for non-blocking asynchronous exports
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    # Set the global TracerProvider
    trace.set_tracer_provider(provider)
    
    logging.info(f"TraceGuard configured to export traces to {db_path}")
