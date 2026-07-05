"use client";
import React from 'react';

interface Span {
  span_id: string;
  parent_span_id?: string | null;
  name: string;
  start_time: string; // ns
  end_time: string;   // ns
  status_code: string;
  attributes: Record<string, string | number | boolean>;
}

interface Trace {
  trace_id: string;
  start_time: string;
  spans: Span[];
}

interface TraceWaterfallProps {
  trace: Trace | null;
}

export default function TraceWaterfall({ trace }: TraceWaterfallProps) {
  if (!trace || !trace.spans || trace.spans.length === 0) {
    return <div style={{ padding: '20px' }}>Select a trace to view its waterfall.</div>;
  }

  // 1. Find global min and max time in nanoseconds
  let minTime = BigInt(trace.spans[0].start_time);
  let maxTime = BigInt(trace.spans[0].end_time);

  trace.spans.forEach(s => {
    const st = BigInt(s.start_time);
    const et = BigInt(s.end_time);
    if (st < minTime) minTime = st;
    if (et > maxTime) maxTime = et;
  });

  const totalDurationNs = Number(maxTime - minTime);
  const totalDurationMs = totalDurationNs / 1000000;

  // 2. Build Hierarchy to calculate depth (Y-axis indent)
  const spanDepthMap: Record<string, number> = {};
  
  // A simple topological sort / depth calculation
  const getDepth = (spanId: string): number => {
    if (spanDepthMap[spanId] !== undefined) return spanDepthMap[spanId];
    
    const span = trace.spans.find(s => s.span_id === spanId);
    if (!span || !span.parent_span_id) {
      spanDepthMap[spanId] = 0;
      return 0;
    }
    
    const depth = getDepth(span.parent_span_id) + 1;
    spanDepthMap[spanId] = depth;
    return depth;
  };

  // Sort spans by start time for the waterfall
  const sortedSpans = [...trace.spans].sort((a, b) => {
    if (BigInt(a.start_time) < BigInt(b.start_time)) return -1;
    if (BigInt(a.start_time) > BigInt(b.start_time)) return 1;
    return 0;
  });

  return (
    <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
      <h3 style={{ marginTop: 0 }}>Trace Waterfall (Datadog/Jaeger View)</h3>
      <div style={{ marginBottom: '16px', fontSize: '14px', color: '#666' }}>
        Total Duration: {totalDurationMs.toFixed(2)} ms | Spans: {trace.spans.length}
      </div>

      <div style={{ position: 'relative', borderTop: '1px solid #eee', paddingTop: '10px' }}>
        {/* Render timeline grid lines (0%, 25%, 50%, 75%, 100%) */}
        {[0, 25, 50, 75, 100].map(pct => (
          <div key={pct} style={{ 
            position: 'absolute', 
            left: `calc(200px + (calc(100% - 200px) * ${pct / 100}))`, 
            top: 0, 
            bottom: 0, 
            borderLeft: '1px dashed #eee',
            zIndex: 0
          }}>
            <span style={{ position: 'absolute', top: '-20px', left: '-10px', fontSize: '10px', color: '#999' }}>
              {pct}%
            </span>
          </div>
        ))}

        {sortedSpans.map(span => {
          const startOffsetNs = Number(BigInt(span.start_time) - minTime);
          const durationNs = Number(BigInt(span.end_time) - BigInt(span.start_time));
          
          // Calculate percentages for CSS
          const leftPct = totalDurationNs > 0 ? (startOffsetNs / totalDurationNs) * 100 : 0;
          const widthPct = totalDurationNs > 0 ? Math.max((durationNs / totalDurationNs) * 100, 0.5) : 100; // minimum 0.5% width
          
          const depth = getDepth(span.span_id);
          const isError = span.status_code === 'ERROR';

          return (
            <div key={span.span_id} style={{ display: 'flex', alignItems: 'center', margin: '4px 0', position: 'relative', zIndex: 1 }}>
              {/* Left Column: Name and Indentation */}
              <div style={{ 
                width: '200px', 
                flexShrink: 0, 
                paddingLeft: `${depth * 15}px`, 
                fontSize: '12px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                borderRight: '1px solid #eee',
                paddingRight: '10px',
                boxSizing: 'border-box'
              }}>
                <span title={span.name} style={{ color: isError ? 'red' : '#333', fontWeight: depth === 0 ? 'bold' : 'normal' }}>
                  {isError ? '⚠️ ' : ''}{span.name}
                </span>
              </div>
              
              {/* Right Column: Waterfall Bar */}
              <div style={{ flexGrow: 1, position: 'relative', height: '24px' }}>
                <div 
                  title={`${span.name}\nLatency: ${(durationNs / 1000000).toFixed(2)} ms`}
                  style={{
                    position: 'absolute',
                    left: `${leftPct}%`,
                    width: `${widthPct}%`,
                    height: '16px',
                    top: '4px',
                    backgroundColor: isError ? '#ff4d4f' : '#1890ff',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    minWidth: '2px'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
