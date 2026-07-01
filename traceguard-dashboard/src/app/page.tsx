'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/traces')
      .then(res => res.json())
      .then(data => {
        if (data.error) throw new Error(data.error);
        setTraces(data.traces || []);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <header>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Evaluation Overview</h1>
        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.1rem' }}>Monitor statistical drift and AI agent performance.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Passed PRs</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--success)', marginTop: '8px' }}>94%</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Anomalous Traces</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--error)', marginTop: '8px' }}>{traces.filter(t => t.status === 'ERROR').length}</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Total Traces</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, marginTop: '8px' }}>{traces.length}</div>
        </div>
      </div>

      <section className="glass" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Recent Production Traces</h2>
        
        {loading && <p style={{ color: 'rgba(255,255,255,0.6)' }}>Loading trace data...</p>}
        {error && <p style={{ color: 'var(--error)' }}>{error}</p>}
        
        {!loading && !error && (
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
                {traces.length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'rgba(255,255,255,0.5)' }}>
                      No traces recorded yet.
                    </td>
                  </tr>
                ) : traces.map((trace) => (
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
          </div>
        )}
      </section>
    </div>
  )
}
