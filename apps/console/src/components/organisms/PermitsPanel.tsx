import { useState, useMemo } from 'react';
import { Card, Badge, Button } from '@/components/atoms';
import { AlertTriangle, Check, X } from 'lucide-react';

export interface Permit {
  permitId: string;
  title: string;
  zoneId: string;
  workType: string;
  workers: string[];
  startTime: string;
  endTime: string;
  status: 'requested' | 'approved' | 'active' | 'suspended' | 'closed';
  hasConflict: boolean;
  conflictDescription?: string;
}

const MOCK_PERMITS: Permit[] = [
  {
    permitId: 'PTW-4091',
    title: 'Hot Work - Welding on Reformer line',
    zoneId: 'Zone 4 (Primary Reformer)',
    workType: 'Hot Work',
    workers: ['J. Doe', 'A. Singh'],
    startTime: '2026-07-05T08:00:00Z',
    endTime: '2026-07-05T16:00:00Z',
    status: 'active',
    hasConflict: true,
    conflictDescription: 'SIMOPS Conflict: Confined space entry work in adjacent Reformer feed line.',
  },
  {
    permitId: 'PTW-1102',
    title: 'Confined Space - Vessel Inspection',
    zoneId: 'Zone 12 (Confined Compressor)',
    workType: 'Confined Space',
    workers: ['R. Kumar'],
    startTime: '2026-07-05T10:00:00Z',
    endTime: '2026-07-05T12:00:00Z',
    status: 'active',
    hasConflict: false,
  },
  {
    permitId: 'PTW-9912',
    title: 'Cold Work - Valve replacement dikes',
    zoneId: 'Zone 2 (Storage Dikes)',
    workType: 'Cold Work',
    workers: ['P. Smith'],
    startTime: '2026-07-05T09:00:00Z',
    endTime: '2026-07-05T17:00:00Z',
    status: 'active',
    hasConflict: false,
  },
  {
    permitId: 'PTW-2810',
    title: 'Electrical - Substation Maintenance',
    zoneId: 'Zone 8 (Sulfur Recovery)',
    workType: 'Electrical Isolation',
    workers: ['T. Johnson', 'S. Ali'],
    startTime: '2026-07-05T14:00:00Z',
    endTime: '2026-07-05T18:00:00Z',
    status: 'requested',
    hasConflict: true,
    conflictDescription: 'SIMOPS Conflict: Live power isolation scheduled during active steam blowdown.',
  },
];

export function PermitsPanel() {
  const [permits, setPermits] = useState<Permit[]>(MOCK_PERMITS);
  const [filterConflict, setFilterConflict] = useState<boolean | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null);

  const filteredPermits = useMemo(() => {
    return permits.filter((p) => {
      if (filterConflict !== null && p.hasConflict !== filterConflict) return false;
      if (filterStatus !== 'all' && p.status !== filterStatus) return false;
      return true;
    });
  }, [permits, filterConflict, filterStatus]);

  const handleApprove = async (permitId: string) => {
    setIsSubmitting(permitId);
    try {
      // Simulate state update to active on supervisor approval
      setPermits((prev) =>
        prev.map((p) => (p.permitId === permitId ? { ...p, status: 'active' } : p))
      );
    } finally {
      setIsSubmitting(null);
    }
  };

  const handleReject = async (permitId: string) => {
    setIsSubmitting(permitId);
    try {
      setPermits((prev) =>
        prev.map((p) => (p.permitId === permitId ? { ...p, status: 'closed' } : p))
      );
    } finally {
      setIsSubmitting(null);
    }
  };

  return (
    <div className="flex flex-col gap-4 text-ink h-full select-none">
      {/* Header with Filters row */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3 select-none">
        <div className="flex items-center gap-1.5 bg-panel-2 p-0.5 rounded border border-line">
          <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold">
            CONFLICT:
          </span>
          <button
            onClick={() => setFilterConflict(null)}
            className={`h-6 px-2 text-micro font-mono font-bold rounded-sm cursor-pointer ${
              filterConflict === null
                ? 'bg-panel text-ink border border-line'
                : 'text-ink-dim hover:text-ink'
            }`}
          >
            ALL
          </button>
          <button
            onClick={() => setFilterConflict(true)}
            className={`h-6 px-2 text-micro font-mono font-bold rounded-sm cursor-pointer ${
              filterConflict === true
                ? 'bg-imminent/10 border-imminent/30 text-imminent'
                : 'text-ink-dim hover:text-imminent'
            }`}
          >
            CONFLICTS
          </button>
        </div>

        <div className="flex items-center gap-1.5 bg-panel-2 p-0.5 rounded border border-line">
          <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold">
            STATUS:
          </span>
          {['all', 'active', 'requested', 'closed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`h-6 px-2 text-micro font-mono font-bold rounded-sm cursor-pointer uppercase ${
                filterStatus === status
                  ? 'bg-panel text-ink border border-line'
                  : 'text-ink-dim hover:text-ink'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Permits Grid Scroll Container */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 scrollbar pr-1">
        {filteredPermits.map((permit) => (
          <Card
            key={permit.permitId}
            className={`flex flex-col gap-3 relative p-3 border ${
              permit.hasConflict && permit.status !== 'closed' ? 'border-imminent/30 bg-imminent/5' : 'border-line bg-panel-2/30'
            }`}
          >
            {/* Header row */}
            <div className="flex justify-between items-center text-xs select-none">
              <div className="flex items-center gap-2">
                <Badge variant="generic" color="ok" className="font-mono text-micro font-bold py-0.5">
                  {permit.permitId}
                </Badge>
                <span className="text-ink font-semibold">{permit.zoneId}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-micro font-mono text-ink-dim uppercase">[{permit.workType}]</span>
                <span
                  className={`text-micro font-mono uppercase font-bold ${
                    permit.status === 'active' ? 'text-ok' : permit.status === 'requested' ? 'text-near' : 'text-ink-dim'
                  }`}
                >
                  {permit.status}
                </span>
              </div>
            </div>

            {/* Title & Workers */}
            <div className="flex flex-col gap-1 select-text">
              <span className="text-xs font-bold text-ink leading-relaxed">{permit.title}</span>
              <span className="text-micro font-mono text-ink-dim uppercase">
                Workers assigned: {permit.workers.join(', ')}
              </span>
            </div>

            {/* SIMOPS conflict warnings */}
            {permit.hasConflict && permit.status !== 'closed' && (
              <div className="bg-imminent/5 border border-imminent/10 p-2 rounded flex items-start gap-2 text-xs text-imminent leading-normal select-text">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">SIMOPS CONFLICT DETECTED:</span> {permit.conflictDescription}
                </div>
              </div>
            )}

            {/* Action buttons (Pending Approval) */}
            {permit.status === 'requested' && (
              <div className="flex items-center justify-end gap-2 border-t border-line/50 pt-2 shrink-0 select-none">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleReject(permit.permitId)}
                  disabled={isSubmitting !== null}
                  icon={<X className="h-3.5 w-3.5" />}
                  className="text-ink-dim hover:text-imminent hover:bg-imminent/10"
                >
                  Reject
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleApprove(permit.permitId)}
                  disabled={isSubmitting !== null}
                  icon={<Check className="h-3.5 w-3.5" />}
                  className="bg-ok/20 border-ok/40 text-ok hover:bg-ok/30"
                >
                  Approve Permit
                </Button>
              </div>
            )}
          </Card>
        ))}

        {filteredPermits.length === 0 && (
          <div className="flex-1 flex items-center justify-center border border-dashed border-line rounded p-6">
            <span className="text-xs text-ink-dim font-mono uppercase">NO PERMITS MATCH FILTER</span>
          </div>
        )}
      </div>
    </div>
  );
}
