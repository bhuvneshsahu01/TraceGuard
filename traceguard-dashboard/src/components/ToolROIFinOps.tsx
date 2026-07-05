"use client";
import React from 'react';
import useSWR from 'swr';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const fetcher = (url: string) => fetch(url).then(res => res.json());

interface ROIData {
  toolName: string;
  count: number;
  totalCost: number;
  successRate: number;
  roi: number;
}

export default function ToolROIFinOps() {
  const { data, error, isLoading } = useSWR('/api/finops', fetcher, { refreshInterval: 5000 });

  if (error) return <div style={{ color: 'red' }}>Failed to load FinOps data.</div>;
  if (isLoading) return <div>Loading FinOps ROI...</div>;

  const roiData: ROIData[] = data?.roiData || [];

  return (
    <div style={{ padding: '20px', background: '#fff', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3 style={{ marginTop: 0 }}>Tool Return on Investment (ROI)</h3>
      <p style={{ margin: 0, color: '#555', fontSize: '14px' }}>
        This chart aggregates the historical success rate of agent tools against their API invocation cost. High-cost, low-success tools indicate prime targets for model distillation or fallback cascading. ROI is calculated based on the tool&apos;s contribution to a successful end-to-end trace completion.
      </p>

      {roiData.length === 0 ? (
        <p>No tools invoked yet.</p>
      ) : (
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={roiData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="toolName" tick={{fontSize: 12}} />
              <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
              <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="roi" name="ROI Score" fill="#8884d8">
                {roiData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.roi < 100 ? '#ff4d4f' : '#8884d8'} />
                ))}
              </Bar>
              <Bar yAxisId="right" dataKey="successRate" name="Success Rate" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      
      <table style={{ width: '100%', marginTop: '20px', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #eee' }}>
            <th>Tool Name</th>
            <th>Invocations</th>
            <th>Total Cost ($)</th>
            <th>Success Rate</th>
            <th>ROI Score</th>
          </tr>
        </thead>
        <tbody>
          {roiData.map(d => (
            <tr key={d.toolName} style={{ borderBottom: '1px solid #eee' }}>
              <td>{d.toolName}</td>
              <td>{d.count}</td>
              <td>${d.totalCost.toFixed(4)}</td>
              <td>{(d.successRate * 100).toFixed(1)}%</td>
              <td style={{ color: d.roi < 100 ? 'red' : 'green', fontWeight: 'bold' }}>
                {d.roi.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
