"use client";
import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

interface Span {
  span_id: string;
  name: string;
  start_time: string; // BigInt serialized as string
  end_time: string;
  status_code: string;
  agent_id?: string | null;
  parent_agent_id?: string | null;
  agent_role?: string | null;
}

interface Trace {
  trace_id: string;
  start_time: string;
  spans: Span[];
}

interface SwimlaneGraphProps {
  trace: Trace;
}

export default function SwimlaneGraph({ trace }: SwimlaneGraphProps) {
  const { nodes, edges } = useMemo(() => {
    const defaultAgentId = "Main-Thread";
    
    // 1. Identify all unique agents to assign them lanes
    const agentSet = new Set<string>();
    trace.spans.forEach(span => {
      agentSet.add(span.agent_id || defaultAgentId);
    });
    const agents = Array.from(agentSet);
    
    // 2. Map agents to Y-coordinates (Lanes)
    const laneHeight = 150;
    const agentLanes: Record<string, number> = {};
    agents.forEach((agentId, index) => {
      agentLanes[agentId] = index * laneHeight;
    });

    // 3. Find global min time to set X=0
    let minTime = Number.MAX_SAFE_INTEGER;
    trace.spans.forEach(span => {
      const t = Number(span.start_time);
      if (t < minTime) minTime = t;
    });

    // Time scaling factor (adjust based on typical trace duration)
    // ns to ms, then scale
    const timeScale = 0.0001; 
    
    const outNodes: Node[] = [];
    const outEdges: Edge[] = [];

    // Create Lane Background Nodes
    agents.forEach(agentId => {
      outNodes.push({
        id: `lane-${agentId}`,
        type: 'default',
        position: { x: -100, y: agentLanes[agentId] - 20 },
        data: { label: agentId === defaultAgentId ? 'System' : `Agent: ${agentId}` },
        style: { 
          width: 2000, 
          height: 140, 
          backgroundColor: 'rgba(255, 255, 255, 0.05)', 
          border: '1px dashed #444',
          zIndex: -1,
          textAlign: 'left',
          padding: '10px'
        },
        draggable: false,
        selectable: false
      });
    });

    // Create Span Nodes
    trace.spans.forEach(span => {
      const agentId = span.agent_id || defaultAgentId;
      const startMs = (Number(span.start_time) - minTime) * timeScale;
      const durationMs = (Number(span.end_time) - Number(span.start_time)) * timeScale;
      
      const width = Math.max(durationMs, 120); // min width for text

      outNodes.push({
        id: span.span_id,
        position: { x: startMs + 150, y: agentLanes[agentId] + 20 }, // +150 offset for lane labels
        data: { 
          label: (
            <div style={{ padding: '4px', fontSize: '10px', wordWrap: 'break-word' }}>
              <strong>{span.name}</strong><br/>
              {span.agent_role && <span style={{color: '#888'}}>Role: {span.agent_role}</span>}
            </div>
          ) 
        },
        style: {
          width: width,
          height: 60,
          background: span.status_code === 'ERROR' ? '#ffeeee' : '#ffffff',
          border: span.status_code === 'ERROR' ? '2px solid red' : '1px solid #777',
          borderRadius: '4px',
          zIndex: 10
        }
      });
    });

    // Create Inter-Agent Communication Edges (Delegation)
    trace.spans.forEach(span => {
      // If this span explicitly says it was triggered by a parent agent
      if (span.parent_agent_id && span.agent_id && span.parent_agent_id !== span.agent_id) {
        // Find the span from the parent agent that occurred right before this one
        const parentSpans = trace.spans.filter(s => s.agent_id === span.parent_agent_id && Number(s.start_time) <= Number(span.start_time));
        if (parentSpans.length > 0) {
          const closestParent = parentSpans.reduce((prev, curr) => 
            (Number(span.start_time) - Number(curr.start_time)) < (Number(span.start_time) - Number(prev.start_time)) ? curr : prev
          );
          
          outEdges.push({
            id: `edge-${closestParent.span_id}-${span.span_id}`,
            source: closestParent.span_id,
            target: span.span_id,
            animated: true,
            style: { stroke: '#0070f3', strokeWidth: 2 },
            label: 'delegates',
            labelStyle: { fill: '#0070f3', fontSize: 10, fontWeight: 700 }
          });
        }
      }
    });

    return { nodes: outNodes, edges: outEdges };
  }, [trace]);

  return (
    <div style={{ height: '600px', width: '100%', border: '1px solid #eaeaea', borderRadius: '8px' }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges}
        fitView
      >
        <Background gap={12} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
