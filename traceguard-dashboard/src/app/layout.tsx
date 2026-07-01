import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TraceGuard Enterprise',
  description: 'AI Agent Evaluation and Observability',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <nav style={{ padding: '20px 40px', borderBottom: '1px solid var(--surface-border)', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem', background: 'linear-gradient(to right, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            TraceGuard
          </h1>
          <div style={{ flex: 1 }} />
          <a href="/" style={{ color: 'var(--foreground)', textDecoration: 'none' }}>Traces</a>
          <a href="/" style={{ color: 'var(--foreground)', textDecoration: 'none' }}>Evaluations</a>
        </nav>
        <main style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
          {children}
        </main>
      </body>
    </html>
  )
}
