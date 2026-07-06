import { useState } from 'react';
import { Card } from '@/components/atoms';
import { Network, HardDrive, FileText, AlertTriangle } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: 'equipment' | 'permit' | 'risk';
  x: number;
  y: number;
  details: string;
}

interface GraphLink {
  source: string;
  target: string;
}

const NODES: GraphNode[] = [
  { id: 'eq-1', label: 'Primary Reformer Line-04', type: 'equipment', x: 150, y: 150, details: 'Line isolation valves, status: operating' },
  { id: 'ptw-1', label: 'PTW-4091 Welding', type: 'permit', x: 280, y: 100, details: 'Authorized hot-work, active shift supervisor approval' },
  { id: 'ptw-2', label: 'PTW-1102 Vessel Insp', type: 'permit', x: 280, y: 200, details: 'Confined space entry authorized adjacent' },
  { id: 'risk-1', label: 'RF-0491 Gas Accumulation', type: 'risk', x: 80, y: 80, details: 'Imminent lead-time warning risk convergence' },
  { id: 'risk-2', label: 'RF-1204 Bearing Thermal', type: 'risk', x: 80, y: 220, details: 'Near thermal breach limit risk' },
];

const LINKS: GraphLink[] = [
  { source: 'eq-1', target: 'ptw-1' },
  { source: 'eq-1', target: 'ptw-2' },
  { source: 'risk-1', target: 'eq-1' },
  { source: 'risk-2', target: 'eq-1' },
  { source: 'risk-1', target: 'ptw-1' },
];

export function KnowledgeGraphViz() {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(NODES[0]);

  return (
    <div className="flex flex-col gap-4 text-ink h-full select-none">
      <div className="flex-1 border border-line bg-panel/30 rounded-md relative overflow-hidden flex items-center justify-center">
        {/* Network Icon absolute watermark */}
        <div className="absolute top-2 left-2 text-ink-dim/40 font-mono text-micro flex items-center gap-1.5 pointer-events-none">
          <Network className="h-3.5 w-3.5" />
          ADJACENCY RELATIONSHIP GRAPH
        </div>

        {/* SVG Drawing workspace */}
        <svg className="w-full h-full max-h-[300px] pointer-events-auto">
          {/* Link edges lines */}
          {LINKS.map((link, idx) => {
            const sourceNode = NODES.find((n) => n.id === link.source);
            const targetNode = NODES.find((n) => n.id === link.target);
            if (!sourceNode || !targetNode) return null;
            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke="#2a323d"
                strokeWidth={1.5}
                className="transition-colors duration-fast"
              />
            );
          })}

          {/* Node circles */}
          {NODES.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const color =
              node.type === 'risk'
                ? '#f06363'
                : node.type === 'permit'
                ? '#4fa3c7'
                : '#e8a33d';

            return (
              <g
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
                transform={`translate(${node.x}, ${node.y})`}
              >
                {/* Ping ring for selected or risk nodes */}
                {isSelected && (
                  <circle
                    r={10}
                    fill="none"
                    stroke={color}
                    strokeWidth={1.5}
                    className="animate-ping opacity-60"
                  />
                )}
                <circle
                  r={7}
                  fill="#161b22"
                  stroke={color}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  className="group-hover:fill-panel-2 transition-all"
                />
                <text
                  x={10}
                  y={4}
                  fill="#8b949e"
                  fontSize={8}
                  fontFamily="monospace"
                  className="group-hover:fill-ink transition-colors"
                >
                  {node.id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Drawer */}
      {selectedNode && (
        <Card className="p-3 bg-panel-2/30 border-line select-text text-xs flex flex-col gap-1.5">
          <div className="flex justify-between items-center select-none border-b border-line pb-1.5 mb-1 shrink-0">
            <span className="font-bold text-ink uppercase flex items-center gap-1.5">
              {selectedNode.type === 'risk' ? (
                <AlertTriangle className="h-3.5 w-3.5 text-imminent shrink-0" />
              ) : selectedNode.type === 'permit' ? (
                <FileText className="h-3.5 w-3.5 text-watch shrink-0" />
              ) : (
                <HardDrive className="h-3.5 w-3.5 text-accent shrink-0" />
              )}
              {selectedNode.label}
            </span>
            <span className="text-micro font-mono text-ink-dim uppercase">[{selectedNode.type}]</span>
          </div>
          <p className="text-ink-dim leading-relaxed font-mono text-micro uppercase">{selectedNode.details}</p>
        </Card>
      )}
    </div>
  );
}
