import pytest
import sqlite3
import os
from traceguard_curate.extractor import TraceExtractor

@pytest.fixture
def mock_db():
    db_path = ".test_curate.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE traces (trace_id TEXT PRIMARY KEY, start_time INTEGER)")
    cursor.execute('''CREATE TABLE spans (
        span_id TEXT PRIMARY KEY, trace_id TEXT, parent_span_id TEXT,
        name TEXT, start_time INTEGER, end_time INTEGER,
        status_code TEXT, attributes TEXT, events TEXT)
    ''')
    
    cursor.execute("INSERT INTO traces VALUES ('trace1', 1000)")
    cursor.execute("INSERT INTO spans VALUES ('span1', 'trace1', NULL, 'test_func', 1000, 2000, 'OK', '{}', '[]')")
    cursor.execute("INSERT INTO spans VALUES ('span2', 'trace1', 'span1', 'child_func', 1500, 1900, 'ERROR', '{\"arg\": 1}', '[]')")
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    if os.path.exists(db_path):
        os.remove(db_path)

def test_extract_all_traces(mock_db):
    extractor = TraceExtractor(mock_db)
    traces = extractor.extract_all_traces()
    
    assert len(traces) == 1
    assert traces[0].trace_id == 'trace1'
    assert len(traces[0].spans) == 2
    
    span2 = next(s for s in traces[0].spans if s.span_id == 'span2')
    assert span2.status_code == 'ERROR'
    assert span2.attributes == {"arg": 1}
