import { useEffect, useState } from 'react';
import { Wrench, AlertCircle } from 'lucide-react';
import { EmptyState } from '@/components/atoms';
import clsx from 'clsx';

interface WorkOrder {
  orderId: string;
  equipmentId: string;
  zoneId: string;
  failureCode: string;
  state: string;
  title: string;
  openedAt?: string;
  closedAt?: string | null;
  description?: string;
}

interface RcaDigest {
  workOrderCount: number;
  similarFailureCount: number;
  citationCount: number;
  citations: Array<{ kind: string; refId: string; summary: string }>;
  scheduleSuggestion?: string | null;
  degraded?: boolean;
  reason?: string;
}

export default function MaintenanceView() {
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [rca, setRca] = useState<RcaDigest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const zoneId = 'B-04';

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [woRes, rcaRes] = await Promise.all([
          fetch(`/api/maintenance/work-orders?zoneId=${encodeURIComponent(zoneId)}`),
          fetch(`/api/maintenance/rca?zoneId=${encodeURIComponent(zoneId)}`),
        ]);
        if (!woRes.ok || !rcaRes.ok) throw new Error('unavailable');
        const woBody = (await woRes.json()) as { orders?: WorkOrder[] };
        const rcaBody = (await rcaRes.json()) as { rca?: RcaDigest };
        if (!cancelled) {
          setOrders(woBody.orders ?? []);
          setRca(rcaBody.rca ?? null);
          setError(null);
        }
      } catch {
        if (!cancelled) setError('Maintenance API unavailable — start API with `make dev`.');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="h-full w-full overflow-y-auto bg-bg p-4 flex flex-col gap-4">
      <div className="flex items-end justify-between border-b border-line pb-3">
        <div className="flex flex-col gap-1">
          <h1 className="text-lg font-semibold text-ink flex items-center gap-2">
            <Wrench className="h-4 w-4 text-ink-dim" />
            Maintenance · {zoneId}
          </h1>
          <p className="text-xs text-ink-dim">
            Work orders and RCA digest from real fixtures — never invented IDs.
          </p>
        </div>
      </div>

      {error && (
        <div className="text-xs text-imminent flex items-center gap-2 font-mono">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}

      {rca && (
        <section className="border border-line rounded-md bg-panel p-3 flex flex-col gap-2">
          <span className="text-micro font-mono font-bold text-ink-dim uppercase">
            RCA digest · {rca.citationCount} citations
            {rca.degraded ? ' · degraded' : ''}
          </span>
          {rca.scheduleSuggestion && (
            <p className="text-xs text-ink leading-normal">{rca.scheduleSuggestion}</p>
          )}
          <ul className="flex flex-col gap-1">
            {(rca.citations || []).map((c) => (
              <li key={`${c.kind}-${c.refId}`} className="text-xs font-mono text-ink-dim">
                <span className="text-ink">{c.refId}</span>
                <span className="mx-1.5 text-line-2">·</span>
                {c.kind}
                {c.summary ? ` — ${c.summary.slice(0, 100)}` : ''}
              </li>
            ))}
          </ul>
          {rca.degraded && rca.reason && (
            <p className="text-micro font-mono text-ink-dim">↳ {rca.reason}</p>
          )}
        </section>
      )}

      <section className="border border-line rounded-md bg-panel p-3 flex flex-col gap-2 flex-1 min-h-0">
        <span className="text-micro font-mono font-bold text-ink-dim uppercase">
          Work orders ({orders.length})
        </span>
        {orders.length === 0 && !error ? (
          <EmptyState
            title="No work orders for this zone"
            hint="Empty is honest — the CSV has no rows matching this filter."
            className="py-8"
          />
        ) : (
          <div className="flex flex-col gap-1.5 overflow-y-auto scrollbar">
            {orders.map((o) => (
              <div
                key={o.orderId}
                className="flex items-start gap-2 border-b border-line/60 last:border-0 py-2"
              >
                <span
                  className={clsx(
                    'px-1.5 py-0.5 rounded-sm border font-mono text-micro font-bold uppercase shrink-0',
                    o.state === 'in-progress' || o.state === 'open'
                      ? 'text-near border-near/30 bg-near/10'
                      : 'text-ink-dim border-line bg-bg',
                  )}
                >
                  {o.state}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-xs text-ink font-medium truncate">
                    <span className="font-mono text-ink-dim mr-1.5">{o.orderId}</span>
                    {o.title}
                  </div>
                  <div className="text-micro font-mono text-ink-dim mt-0.5">
                    {o.equipmentId} · {o.failureCode || '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
