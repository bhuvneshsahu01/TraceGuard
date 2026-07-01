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

  const { total, anomalies, passRate, latencyData, statusData } = useMemo(() => {
    if (traces.length === 0) return { total: 0, anomalies: 0, passRate: 0, latencyData: [], statusData: [] };
    
    const total = traces.length;
    const anomalies = traces.filter(t => t.status === 'ERROR').length;
    const passRate = Math.round(((total - anomalies) / total) * 100);
    
    const latencyData = traces.map((t, idx) => ({
      name: `Run ${idx + 1}`,
      latency: t.latencyMs,
      id: t.id.substring(0, 8),
    }));

    const statusData = [
      { name: 'Passed', value: total - anomalies },
      { name: 'Failed', value: anomalies }
    ];

    return { total, anomalies, passRate, latencyData, statusData };
  }, [traces]);

  const COLORS = ['#22c55e', '#ef4444'];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: 'var(--background)', border: '1px solid var(--surface-border)', padding: '12px', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontWeight: 'bold' }}>{label} ({payload[0].payload.id})</p>
          <p style={{ margin: 0, color: 'var(--primary)' }}>Latency: {payload[0].value}ms</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <header>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Evaluation Overview</h1>
        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.1rem' }}>Monitor statistical drift and AI agent performance.</p>
      </header>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Passed PRs</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--success)', marginTop: '8px' }}>{passRate}%</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Anomalous Traces</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--error)', marginTop: '8px' }}>{anomalies}</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Total Traces</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, marginTop: '8px' }}>{total}</div>
        </div>
      </div>

      {loading && <p style={{ color: 'rgba(255,255,255,0.6)' }}>Loading trace data...</p>}
      {error && <p style={{ color: 'var(--error)' }}>{error}</p>}

      {!loading && !error && traces.length > 0 && (
        <>
          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            <section className="glass" style={{ padding: '32px' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Latency Distribution (Last 50 Runs)</h2>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={latencyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <YAxis stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
                    <RechartsTooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="latency" stroke="var(--primary)" strokeWidth={3} dot={{ r: 4, fill: 'var(--primary)' }} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="glass" style={{ padding: '32px' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Status Breakdown</h2>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      contentStyle={{ background: 'var(--background)', border: '1px solid var(--surface-border)', borderRadius: '8px' }} 
                      itemStyle={{ color: 'var(--foreground)' }} 
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          {/* Table */}
          <section className="glass" style={{ padding: '32px' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Recent Production Traces</h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--surface-border)' }}>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Trace ID</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Status</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Latency</th>
                    <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Spans</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Show newest first in the table */}
                  {[...traces].reverse().slice(0, 10).map((trace) => (
                    <tr key={trace.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
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
                      <td style={{ padding: '16px' }}>{trace.latencyMs}ms</td>
                      <td style={{ padding: '16px' }}>{trace.spans}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ padding: '16px', textAlign: 'center', color: 'rgba(255,255,255,0.5)', fontSize: '0.9rem' }}>
                Showing 10 most recent traces. See charts for aggregated history.
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
