import { useEffect, useState } from 'react';
import { Card } from '@/components/atoms';
import { AlertCircle, Database } from 'lucide-react';
import { getMemoryStatus, type MemoryStatus } from '@/api/intelligence';

export function MemoryStatusPanel() {
  const [status, setStatus] = useState<MemoryStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMemoryStatus()
      .then((body) => {
        setStatus(body);
        setError(null);
      })
      .catch(() => {
        setStatus(null);
        setError('Memory status unavailable — start API with `make dev`.');
      });
  }, []);

  return (
    <Card className="p-3 border-line bg-panel-2/30 flex flex-col gap-2">
      <span className="text-micro font-mono font-bold text-ink-dim uppercase flex items-center gap-1.5">
        <Database className="h-3.5 w-3.5" />
        Cognee Memory Status
      </span>
      {error && (
        <div className="text-xs text-imminent flex items-center gap-2 font-mono">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}
      {status && (
        <div className="text-xs font-mono text-ink-dim space-y-1">
          <div>
            Dataset: <span className="text-ink">{status.dataset}</span>
          </div>
          <div>
            Configured:{' '}
            <span className={status.configured ? 'text-ok' : 'text-near'}>
              {status.configured ? 'yes' : 'no'}
            </span>
          </div>
          <div>
            Status:{' '}
            <span className={status.degraded ? 'text-near' : 'text-ok'}>
              {status.degraded ? 'degraded' : 'healthy'}
            </span>
          </div>
          {status.reason && <p className="text-micro leading-relaxed">{status.reason}</p>}
        </div>
      )}
    </Card>
  );
}
