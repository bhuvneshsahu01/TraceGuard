"use client";
import React from 'react';
import useSWR from 'swr';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function DriftChart() {
  const { data, error, isLoading } = useSWR('/api/drift', fetcher, { refreshInterval: 5000 });

  if (error) return <div style={{ color: 'red' }}>Failed to load drift data.</div>;
  if (isLoading) return <div>Loading Statistical Drift...</div>;

  const driftData = data?.driftData || [];

  return (
    <div style={{ padding: '20px', background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3 style={{ marginTop: 0 }}>Model Distribution Drift (PSI) vs. Pass Rate</h3>
      <p style={{ color: '#555', fontSize: '14px' }}>
        Tracks the Population Stability Index (PSI) to detect mathematical shifts in model outputs. 
        A PSI &gt; 0.2 indicates significant drift and correlates with degraded agent evaluation pass rates.
      </p>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <ComposedChart
            data={driftData}
            margin={{
              top: 20,
              right: 20,
              bottom: 20,
              left: 20,
            }}
          >
            <CartesianGrid stroke="#f5f5f5" />
            <XAxis dataKey="name" scale="band" tick={{fontSize: 12}} />
            <YAxis 
              yAxisId="left" 
              label={{ value: 'Evaluation Pass Rate %', angle: -90, position: 'insideLeft' }} 
              domain={[0, 100]} 
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              label={{ value: 'PSI (Drift)', angle: 90, position: 'insideRight' }} 
              domain={[0, 0.5]} 
            />
            <Tooltip />
            <Legend />
            
            {/* PSI Threshold Alert Line */}
            <ReferenceLine yAxisId="right" y={0.2} stroke="red" strokeDasharray="3 3" label={{ position: 'top', value: 'Critical Drift Threshold (>0.2)', fill: 'red', fontSize: 12 }} />

            <Bar yAxisId="left" dataKey="passRate" name="Pass Rate (%)" barSize={20} fill="#413ea0" />
            <Line yAxisId="right" type="monotone" dataKey="psi" name="PSI Score" stroke="#ff7300" strokeWidth={3} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
