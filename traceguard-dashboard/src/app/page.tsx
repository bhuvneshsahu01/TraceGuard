import styles from './page.module.css'

export default function Home() {
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
          <div style={{ fontSize: '2.5rem', fontWeight: 600, color: 'var(--error)', marginTop: '8px' }}>12</div>
        </div>
        <div className="glass glass-card">
          <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Avg Latency</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 600, marginTop: '8px' }}>1.2s</div>
        </div>
      </div>

      <section className="glass" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>Recent Production Traces</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--surface-border)' }}>
                <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Trace ID</th>
                <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Status</th>
                <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Latency</th>
                <th style={{ padding: '12px 16px', color: 'rgba(255,255,255,0.6)' }}>Tokens</th>
              </tr>
            </thead>
            <tbody>
              {/* Dummy data for visual design */}
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '16px' }}><code style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>tr_8f92a1</code></td>
                <td style={{ padding: '16px' }}><span style={{ color: 'var(--success)' }}>OK</span></td>
                <td style={{ padding: '16px' }}>842ms</td>
                <td style={{ padding: '16px' }}>4,102</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '16px' }}><code style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>tr_3b19c4</code></td>
                <td style={{ padding: '16px' }}><span style={{ color: 'var(--error)' }}>ERROR</span></td>
                <td style={{ padding: '16px' }}>5,210ms</td>
                <td style={{ padding: '16px' }}>12,890</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
