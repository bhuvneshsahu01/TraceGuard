'use client';

import { useEffect, useState, useMemo } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

export default function Home() {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/traces')
      .then(res => res.json())
      .then(data => {
        if (data.error) throw new Error(data.error);
        // Reverse to show oldest to newest on the chart
        setTraces((data.traces || []).reverse());
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const { total, anomalies, passRate, latencyData, statusData, totalCost, avgFaithfulness, costData } = useMemo(() => {
    if (traces.length === 0) return { total: 0, anomalies: 0, passRate: 0, latencyData: [], statusData: [], totalCost: 0, avgFaithfulness: 0, costData: [] };
    
    const total = traces.length;
    const anomalies = traces.filter(t => t.status === 'ERROR').length;
    const passRate = Math.round(((total - anomalies) / total) * 100);
    
    let totalCost = 0;
    let sumFaithfulness = 0;
    let evalCount = 0;
    
    const costData = [];
    let cumulativeCost = 0;

    const latencyData = traces.map((t, idx) => {
      if (t.costUsd) {
        totalCost += t.costUsd;
        cumulativeCost += t.costUsd;
      }
      costData.push({
        name: `Run ${idx + 1}`,
        cost: cumulativeCost,
        runCost: t.costUsd || 0
      });
      
      if (t.faithfulness !== null && t.faithfulness !== undefined) {
        sumFaithfulness += t.faithfulness;
        evalCount++;
      }
      
      return {
        name: `Run ${idx + 1}`,
        latency: t.latencyMs,
        id: t.id.substring(0, 8),
      };
    });

    const statusData = [
      { name: 'Passed', value: total - anomalies },
      { name: 'Failed', value: anomalies }
    ];
    
    const avgFaithfulness = evalCount > 0 ? (sumFaithfulness / evalCount) * 100 : 0;

    return { total, anomalies, passRate, latencyData, statusData, totalCost, avgFaithfulness: Math.round(avgFaithfulness), costData };
  }, [traces]);

  const COLORS = ['#22c55e', '#ef4444'];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: 'var(--background)', border: '1px solid var(--surface-border)', padding: '12px', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: 0, color: payload[0].color }}>{payload[0].name}: {payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [traceTree, setTraceTree] = useState<any[]>([]);

  const fetchTraceTree = async (id: string) => {
    setSelectedTraceId(id);
    const res = await fetch(`/api/traces/${id}`);
    const data = await res.json();
    setTraceTree(data.spans || []);
  };

  const promoteToDataset = async () => {
    if (!selectedTraceId || traceTree.length === 0) return;
    const res = await fetch('/api/datasets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trace_id: selectedTraceId,
        name: `Curated Dataset ${new Date().toISOString().split('T')[0]}`,
        spans: traceTree
      })
    });
    if (res.ok) {
      alert('Trace successfully promoted to Golden Dataset!');
      setSelectedTraceId(null);
    } else {
      alert('Failed to promote trace.');
    }
  };

  const renderTree = (nodes: any[], depth = 0) => {
    return nodes.map(node => (
      <div key={node.span_id} style={{ marginLeft: depth * 24 + 'px', marginTop: '8px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', borderLeft: '4px solid ' + (node.status_code === 'ERROR' ? 'var(--error)' : 'var(--primary)') }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <strong style={{ fontFamily: 'monospace' }}>{node.name}</strong>
          <span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)' }}>{(node.end_time - node.start_time) / 1000000}ms</span>
        </div>
        {node.attributes && node.attributes['guardrail.direction'] && (
          <div style={{ marginTop: '8px', fontSize: '0.8rem', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)', padding: '4px 8px', borderRadius: '4px', display: 'inline-block' }}>
            🛡️ TraceGuard Firewall ({node.attributes['guardrail.direction']})
          </div>
        )}
        {node.attributes && node.attributes['llm.model'] && (
          <div style={{ marginTop: '8px', fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)' }}>
            Tokens: {node.attributes['financial.input_tokens']} In / {node.attributes['financial.output_tokens']} Out (${node.attributes['financial.cost_usd']?.toFixed(6)})
          </div>
        )}
        {node.children && node.children.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            {renderTree(node.children, depth + 1)}
          </div>
        )}
      </div>
    ));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <header>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Enterprise Observability</h1>
        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.1rem' }}>Monitor semantic quality, unit economics, and system performance.</p>
      </header>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Passed PRs</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--success)', marginTop: '8px' }}>{passRate}%</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Avg Faithfulness</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--primary)', marginTop: '8px' }}>{avgFaithfulness > 0 ? `${avgFaithfulness}%` : 'N/A'}</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Total Burn (USD)</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: '#f59e0b', marginTop: '8px' }}>${totalCost.toFixed(4)}</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Anomalous Traces</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--error)', marginTop: '8px' }}>{anomalies}</div>
        </div>
      </div>

      {loading && <p style={{ color: 'rgba(255,255,255,0.6)' }}>Loading trace data...</p>}
      {error && <p style={{ color: 'var(--error)' }}>{error}</p>}

      {!loading && !error && traces.length > 0 && (
        <>
          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <section className="glass" style={{ padding: '32px' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Latency Distribution</h2>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={latencyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <RechartsTooltip content={<CustomTooltip />} />
                    <Line type="monotone" name="Latency (ms)" dataKey="latency" stroke="var(--primary)" strokeWidth={3} dot={{ r: 4, fill: 'var(--primary)' }} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="glass" style={{ padding: '32px' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Cumulative Cost (USD)</h2>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={costData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <RechartsTooltip content={<CustomTooltip />} />
                    <Line type="stepAfter" name="Cumulative Cost ($)" dataKey="cost" stroke="#f59e0b" strokeWidth={3} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          {/* HITL Table */}
          <section className="glass" style={{ padding: '32px' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>Human-in-the-Loop (HITL) Queue</h2>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '24px' }}>Review anomalous traces and hallucinations.</p>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--surface-border)' }}>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Trace ID</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Status</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Cost</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Faithfulness</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Latency</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {[...traces].reverse().slice(0, 10).map((trace) => {
                    const isHallucination = trace.faithfulness !== null && trace.faithfulness < 0.8;
                    const isBlocked = trace.status === 'ERROR' && trace.reason?.includes('TraceGuard Firewall');
                    const rowBg = isHallucination ? 'rgba(239, 68, 68, 0.1)' : (isBlocked ? 'rgba(245, 158, 11, 0.1)' : 'transparent');
                    return (
                    <tr key={trace.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: rowBg }}>
                      <td style={{ padding: '16px' }}>
                        <code style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>
                          {trace.id.substring(0, 8)}...
                        </code>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ color: trace.status === 'OK' ? 'var(--success)' : 'var(--error)' }}>
                          {trace.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px' }}>${trace.costUsd?.toFixed(4)}</td>
                      <td style={{ padding: '16px' }}>
                        {trace.faithfulness !== null 
                          ? <span style={{ color: isHallucination ? 'var(--error)' : 'var(--success)' }}>{(trace.faithfulness * 100).toFixed(0)}%</span> 
                          : 'N/A'}
                      </td>
                      <td style={{ padding: '16px' }}>{trace.latencyMs}ms</td>
                      <td style={{ padding: '16px' }}>
                        <button 
                          onClick={() => fetchTraceTree(trace.id)}
                          style={{ background: isHallucination || isBlocked ? 'var(--error)' : 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>
                          Review
                        </button>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {/* Trace Tree Modal */}
      {selectedTraceId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="glass" style={{ width: '80%', height: '80%', padding: '32px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ margin: 0 }}>Trace Tree: <code style={{ fontSize: '1rem' }}>{selectedTraceId}</code></h2>
              <div>
                <button onClick={promoteToDataset} style={{ background: 'var(--primary)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', marginRight: '16px' }}>Promote to Dataset</button>
                <button onClick={() => setSelectedTraceId(null)} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}>Close</button>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              {renderTree(traceTree)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
