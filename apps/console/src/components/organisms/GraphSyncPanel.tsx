import { useState } from 'react';
import { Card, Button } from '@/components/atoms';
import { GitBranch, AlertCircle, CheckCircle2 } from 'lucide-react';
import { syncPlantGraph } from '@/api/platform';

export function GraphSyncPanel() {
  const [status, setStatus] = useState<string | null>(null);
  const [degraded, setDegraded] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSync = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const body = await syncPlantGraph();
      setDegraded(Boolean(body.degraded));
      if (body.degraded) {
        setStatus(String(body.reason ?? 'Neo4j not configured'));
      } else {
        setStatus(`Synced ${body.zones ?? 0} zones, ${body.sensors ?? 0} sensors`);
      }
    } catch {
      setDegraded(true);
      setStatus('Graph sync API unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-3 border-line bg-panel-2/30 flex flex-col gap-2">
      <span className="text-micro font-mono font-bold text-ink-dim uppercase flex items-center gap-1.5">
        <GitBranch className="h-3.5 w-3.5" />
        Neo4j Graph Sync (§5)
      </span>
      <p className="text-micro font-mono text-ink-dim">
        Push equipment-zone relationships for compound-risk queries. Degrades when Neo4j is unset.
      </p>
      <Button
        variant="secondary"
        size="sm"
        loading={loading}
        onClick={handleSync}
        className="self-start text-micro font-mono uppercase"
      >
        Sync Demo Plant
      </Button>
      {status && (
        <span
          className={`text-micro font-mono flex items-start gap-1 ${
            degraded ? 'text-near' : 'text-ok'
          }`}
        >
          {degraded ? (
            <AlertCircle className="h-3 w-3 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle2 className="h-3 w-3 shrink-0 mt-0.5" />
          )}
          {status}
        </span>
      )}
    </Card>
  );
}
