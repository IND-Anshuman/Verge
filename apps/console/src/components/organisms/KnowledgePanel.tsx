import { useEffect, useState } from 'react';
import { Badge } from '@/components/atoms';
import { AlertTriangle, FileText, History, Shield } from 'lucide-react';
import { getFindingContext, type FindingContext } from '@/api/memory';

interface KnowledgePanelProps {
  /** Active finding to load memory context for; panel stays empty without one. */
  findingId?: string | null;
}

function ContextSection({
  title,
  icon,
  empty,
  items,
  renderItem,
}: {
  title: string;
  icon: React.ReactNode;
  empty: string;
  items: unknown[];
  renderItem: (item: unknown, idx: number) => React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-1.5 text-micro font-mono font-bold text-ink-dim uppercase select-none">
        {icon}
        {title}
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-ink-dim italic font-mono">{empty}</p>
      ) : (
        <div className="flex flex-col gap-2">{items.map(renderItem)}</div>
      )}
    </div>
  );
}

export function KnowledgePanel({ findingId }: KnowledgePanelProps) {
  const [context, setContext] = useState<FindingContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!findingId) {
      setContext(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getFindingContext(findingId)
      .then((data) => {
        if (!cancelled) setContext(data);
      })
      .catch(() => {
        if (!cancelled) {
          setContext(null);
          setError('Memory context unavailable — check API connection.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [findingId]);

  if (!findingId) {
    return (
      <div className="flex items-center justify-center h-full text-xs font-mono text-ink-dim uppercase p-4 text-center">
        Select or focus a finding to load incident memory context
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-ink h-full select-none">
      <div className="flex items-center justify-between border-b border-line pb-2 shrink-0">
        <span className="text-micro font-mono font-bold text-ink-dim uppercase">
          Context · {findingId}
        </span>
        {context?.degraded && (
          <Badge variant="generic" color="near" className="text-micro font-bold flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            DEGRADED
          </Badge>
        )}
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-4 pr-1 scrollbar select-text">
        {loading && (
          <p className="text-xs font-mono text-ink-dim animate-pulse uppercase">Loading Cognee context...</p>
        )}

        {error && (
          <div className="bg-imminent/10 border border-imminent/20 text-imminent text-xs p-2.5 rounded flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {context?.degraded && context.reason && (
          <p className="text-xs text-ink-dim font-mono leading-relaxed">{context.reason}</p>
        )}

        {context && !loading && (
          <>
            <ContextSection
              title="Similar incidents"
              icon={<Shield className="h-3.5 w-3.5" />}
              empty="No similar incidents in memory."
              items={context.similarIncidents}
              renderItem={(item, idx) => {
                const incident = item as FindingContext['similarIncidents'][number];
                return (
                  <div key={idx} className="p-2.5 border border-line rounded bg-panel-2/30 text-xs">
                    <div className="font-bold text-ink">{incident.title}</div>
                    <p className="text-ink-dim mt-1 leading-relaxed">{incident.excerpt}</p>
                    <span className="text-micro font-mono text-ink-dim mt-1 block">{incident.source}</span>
                  </div>
                );
              }}
            />

            <ContextSection
              title="Regulatory clauses"
              icon={<FileText className="h-3.5 w-3.5" />}
              empty="No regulatory clauses retrieved."
              items={context.regulatoryClauses}
              renderItem={(clause) => {
                const c = clause as FindingContext['regulatoryClauses'][number];
                return (
                  <div key={c.id} className="p-2.5 border border-line rounded bg-panel-2/30 text-xs">
                    <div className="font-mono font-bold text-accent">{c.id}</div>
                    <div className="font-semibold text-ink mt-0.5">{c.title}</div>
                    <p className="text-ink-dim mt-1 leading-relaxed">{c.excerpt}</p>
                  </div>
                );
              }}
            />

            <ContextSection
              title="Plant history"
              icon={<History className="h-3.5 w-3.5" />}
              empty="No closed findings in memory."
              items={context.plantHistory}
              renderItem={(entry, idx) => {
                const h = entry as FindingContext['plantHistory'][number];
                return (
                  <div key={idx} className="p-2.5 border border-line rounded bg-panel-2/30 text-xs">
                    <div className="font-mono font-bold text-ink">{h.findingId}</div>
                    <p className="text-ink-dim mt-1 leading-relaxed">{h.summary}</p>
                  </div>
                );
              }}
            />
          </>
        )}
      </div>
    </div>
  );
}
