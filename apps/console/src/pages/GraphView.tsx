import { Network } from 'lucide-react';
import { KnowledgeGraphViz } from '@/components/organisms/KnowledgeGraphViz';
import { ErrorBoundary } from '@/components/atoms/ErrorBoundary';

/* ── Graph — exploration room (design_plan §6.4) ─────────────────────
   One job: explore live plant relationships. Live data only — the viz
   renders honest empty/offline states and never invents nodes. No triage
   board, no Copilot thread (D1, D6). */

export default function GraphView() {
  return (
    <div className="flex flex-col gap-4 p-4 h-full overflow-hidden text-ink">
      <div className="flex items-end justify-between gap-4 border-b border-line pb-3 shrink-0">
        <div className="flex flex-col gap-1 min-w-0">
          <h1 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <Network className="h-5 w-5 text-ink-dim" />
            Relationship graph
          </h1>
          <p className="text-xs text-ink-dim">
            Live plant topology — equipment, permits, zones, and findings as the engine sees them.
          </p>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto scrollbar surface-1 p-3">
        <ErrorBoundary>
          <KnowledgeGraphViz />
        </ErrorBoundary>
      </div>
    </div>
  );
}
