import { useEffect, useState } from 'react';
import { Card, EmptyState } from '@/components/atoms';
import { Network, HardDrive, FileText, AlertTriangle } from 'lucide-react';
import { getPlantGraph, type GraphNode, type PlantGraph } from '@/api/plant';

export function KnowledgeGraphViz() {
  const [graph, setGraph] = useState<PlantGraph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const g = await getPlantGraph();
        if (cancelled) return;
        setGraph(g);
        setError(null);
        setSelectedNode((prev) => {
          if (!g.nodes.length) return null;
          if (prev && g.nodes.some((n) => n.id === prev.id)) {
            return g.nodes.find((n) => n.id === prev.id) ?? g.nodes[0];
          }
          return g.nodes[0];
        });
      } catch {
        if (!cancelled) {
          setGraph(null);
          setError('Plant graph unavailable — start API with `make dev`.');
        }
      }
    };
    void load();
    const id = window.setInterval(load, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  if (error) {
    return (
      <EmptyState icon={<Network className="h-5 w-5" />} title="Graph offline" hint={error} />
    );
  }

  if (!graph) {
    return (
      <div className="flex items-center justify-center h-40 text-xs font-mono text-ink-dim">
        Loading plant graph…
      </div>
    );
  }

  if (graph.nodes.length === 0) {
    return (
      <EmptyState
        icon={<Network className="h-5 w-5" />}
        title="No graph relationships yet"
        hint="Commission equipment and open permits, or ingest live findings — Verge will not invent nodes."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4 text-ink h-full select-none">
      <div className="flex-1 border border-line bg-panel/30 rounded-md relative overflow-hidden flex items-center justify-center min-h-[220px]">
        <div className="absolute top-2 left-2 text-ink-dim/40 font-mono text-micro flex items-center gap-1.5 pointer-events-none">
          <Network className="h-3.5 w-3.5" />
          LIVE · {graph.source.toUpperCase()} · {graph.plant}
        </div>

        <svg className="w-full h-full max-h-[300px] pointer-events-auto" viewBox="0 0 360 240">
          {graph.links.map((link, idx) => {
            const sourceNode = graph.nodes.find((n) => n.id === link.source);
            const targetNode = graph.nodes.find((n) => n.id === link.target);
            if (!sourceNode || !targetNode) return null;
            return (
              <line
                key={`${link.source}-${link.target}-${idx}`}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke="#DEDCD5"
                strokeWidth={1.5}
              />
            );
          })}

          {graph.nodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const color =
              node.type === 'risk' ? '#C92A2A' : node.type === 'permit' ? '#1864AB' : '#D9480F';

            return (
              <g
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
                transform={`translate(${node.x}, ${node.y})`}
              >
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
                  fill="#FFFFFF"
                  stroke={color}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  className="group-hover:fill-panel-2 transition-all"
                />
                <text
                  x={10}
                  y={4}
                  fill="#6E7178"
                  fontSize={8}
                  fontFamily="monospace"
                  className="group-hover:fill-ink transition-colors"
                >
                  {node.refId ?? node.id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {selectedNode && (
        <Card className="p-3 bg-panel-2/30 border-line select-text text-xs flex flex-col gap-1.5">
          <div className="flex justify-between items-center select-none border-b border-line pb-1.5 mb-1 shrink-0">
            <span className="font-bold text-ink flex items-center gap-1.5">
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
          <p className="text-ink-dim leading-relaxed font-mono text-micro">{selectedNode.details}</p>
        </Card>
      )}
    </div>
  );
}
