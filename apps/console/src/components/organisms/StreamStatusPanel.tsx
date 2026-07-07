import { useEffect, useState } from 'react';
import { Card, Button } from '@/components/atoms';
import { Radio, AlertCircle } from 'lucide-react';
import { getStreamStatus } from '@/api/platform';

export function StreamStatusPanel() {
  const [subscribers, setSubscribers] = useState<number | null>(null);
  const [fanout, setFanout] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    getStreamStatus()
      .then((s) => {
        setSubscribers(s.subscribers);
        setFanout(s.redpandaFanout);
        setError(null);
      })
      .catch(() => {
        setSubscribers(null);
        setFanout(false);
        setError('Stream status API unavailable.');
      });
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <Card className="p-3 border-line bg-panel-2/30 flex flex-col gap-2">
      <span className="text-micro font-mono font-bold text-ink-dim uppercase flex items-center gap-1.5">
        <Radio className="h-3.5 w-3.5" />
        Live Stream (SSE / Redpanda)
      </span>
      {error && (
        <div className="text-xs text-imminent flex items-center gap-2 font-mono">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}
      {subscribers !== null && (
        <div className="text-xs font-mono text-ink-dim space-y-1">
          <div>
            SSE subscribers: <span className="text-ink">{subscribers}</span>
          </div>
          <div>
            Redpanda fan-out:{' '}
            <span className={fanout ? 'text-ok' : 'text-near'}>{fanout ? 'active' : 'off'}</span>
          </div>
          <Button variant="secondary" size="sm" onClick={refresh} className="mt-1 text-micro">
            Refresh
          </Button>
        </div>
      )}
    </Card>
  );
}
