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
                    const rowBg = isHallucination ? 'rgba(239, 68, 68, 0.1)' : 'transparent';
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
                        {isHallucination ? (
                          <button style={{ background: 'var(--error)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Review</button>
                        ) : (
                          <span style={{ color: 'rgba(255,255,255,0.4)' }}>-</span>
                        )}
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
