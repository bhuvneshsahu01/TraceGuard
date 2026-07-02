import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, Edge, Node } from 'reactflow';
import 'reactflow/dist/style.css';

export interface TopologyGraphProps {
  traces: any[];
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({ traces }) => {
  const { nodes, edges } = useMemo(() => {
    const initialNodes: Node[] = [];
    const initialEdges: Edge[] = [];
    
    let yOffset = 50;

    // We take traces that represent a Swarm cycle or just chain
    // For simplicity, we just lay them out linearly or based on parent/child.
    traces.forEach((trace, idx) => {
        initialNodes.push({
            id: trace.trace_id || `trace-${idx}`,
            position: { x: 250, y: yOffset },
            data: { label: `Trace: ${trace.trace_id?.slice(0,8) || 'Unknown'}` },
            style: { border: '1px solid #777', padding: 10, borderRadius: 5, background: '#1e1e1e', color: 'white' }
        });
        
        yOffset += 100;
        
        if (idx > 0) {
            initialEdges.push({
                id: `e-${idx-1}-${idx}`,
                source: traces[idx-1].trace_id || `trace-${idx-1}`,
                target: trace.trace_id || `trace-${idx}`,
                animated: true
            });
        }
    });

    return { nodes: initialNodes, edges: initialEdges };
  }, [traces]);

  return (
    <div style={{ height: '500px', width: '100%', border: '1px solid #333', borderRadius: '8px' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#444" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
