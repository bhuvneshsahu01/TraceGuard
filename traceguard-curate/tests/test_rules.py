from traceguard_curate.rules import ErrorRule, LatencyRule, AnomalyEngine
from traceguard_curate.extractor import TraceData, SpanData

def create_mock_trace(spans_data) -> TraceData:
    spans = [
        SpanData(
            span_id=f"span_{i}",
            trace_id="trace1",
            parent_span_id=None,
            name=s.get("name", "func"),
            start_time=s.get("start", 0),
            end_time=s.get("end", 100),
            status_code=s.get("status", "OK"),
            attributes={},
            events=[]
        ) for i, s in enumerate(spans_data)
    ]
    return TraceData(trace_id="trace1", start_time=0, spans=spans)

def test_error_rule():
    rule = ErrorRule()
    trace_ok = create_mock_trace([{"status": "OK"}])
    assert not rule.evaluate(trace_ok).is_anomalous
    
    trace_err = create_mock_trace([{"status": "OK"}, {"status": "ERROR"}])
    assert rule.evaluate(trace_err).is_anomalous

def test_latency_rule():
    rule = LatencyRule(max_latency_ns=500)
    trace_fast = create_mock_trace([{"start": 0, "end": 400}])
    assert not rule.evaluate(trace_fast).is_anomalous
    
    trace_slow = create_mock_trace([{"start": 0, "end": 600}])
    assert rule.evaluate(trace_slow).is_anomalous

def test_anomaly_engine():
    engine = AnomalyEngine(rules=[ErrorRule(), LatencyRule(max_latency_ns=500)])
    trace = create_mock_trace([{"status": "ERROR", "start": 0, "end": 100}])
    
    result = engine.check_trace(trace)
    assert result.is_anomalous
    assert result.reason is not None
    assert "error" in result.reason
