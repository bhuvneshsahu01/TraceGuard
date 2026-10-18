"use client";
import React from 'react';
import useSWR from 'swr';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
  Cell
} from 'recharts';

const fetcher = (url: string) => fetch(url).then(res => res.json());

export default function LatencyHeatmap() {
  const { data, error, isLoading } = useSWR('/api/traces', fetcher, { refreshInterval: 5000 });

  if (error) return <div style={{ color: 'red' }}>Failed to load latency data.</div>;
  if (isLoading) return <div>Loading Latency Scatter...</div>;

  const traces = data?.traces || [];

  // Format data for Scatter
  const scatterData = traces.map((t: { latencyMs: number, name: string, status: string, timestamp: number }, index: number) => {
    // Generate a pseudo-X if timestamps are too close, or just use index for demonstration
    // In production, X would be a formatted time string
    return {
      x: index + 1, // Timeline sequence
      y: t.latencyMs,
      z: 100, // Bubble size
      name: t.name,
      status: t.status,
      timestamp: new Date(t.timestamp).toLocaleTimeString()
    };
  }).reverse(); // chronological order

  return (
    <div style={{ padding: '20px', background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3 style={{ marginTop: 0 }}>Agent Latency Heatmap (Scatter)</h3>
      <p style={{ color: '#555', fontSize: '14px' }}>
        Visualizes execution latencies of agent calls over time. Outliers (high Y-axis values) indicate potential bottlenecks in LLM inference or tool execution.
      </p>
      
      {scatterData.length === 0 ? (
        <p>No traces found.</p>
      ) : (
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" type="number" name="Timeline Sequence" />
              <YAxis dataKey="y" type="number" name="Latency (ms)" unit="ms" />
              <ZAxis dataKey="z" type="number" range={[50, 400]} name="Weight" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} 
                content={(props: any) => {
                  const { active, payload } = props;
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc' }}>
                        <p style={{ margin: 0 }}><strong>{d.name}</strong></p>
                        <p style={{ margin: 0 }}>Time: {d.timestamp}</p>
                        <p style={{ margin: 0 }}>Latency: {d.y.toFixed(2)} ms</p>
                        <p style={{ margin: 0, color: d.status === 'ERROR' ? 'red' : 'green' }}>
                          Status: {d.status}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Scatter name="Agent Executions" data={scatterData} fill="#8884d8">
                {scatterData.map((entry: { status: string, y: number }, index: number) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.status === 'ERROR' ? '#ff4d4f' : (entry.y > 3000 ? '#ffa940' : '#8884d8')} 
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
