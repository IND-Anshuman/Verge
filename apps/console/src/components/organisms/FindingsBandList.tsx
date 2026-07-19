/**
 * Band-first triage list — Board default (IMMINENT → NEAR → WATCH).
 * Column kanban remains available as a toggle.
 */
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { RiskFinding, FeedbackVerdict, LeadTimeBand } from '@/types';
import { BAND_SEVERITY } from '@/types';
import { FindingCard } from '@/components/organisms/FindingCard';
import { SnoozeDialog } from '@/components/molecules/SnoozeDialog';
import { AssignDialog } from '@/components/molecules/AssignDialog';
import { FeedbackModal } from '@/components/molecules/FeedbackModal';
import { EmptyState } from '@/components/atoms';
import { useFindingsStore } from '@/stores/findings';
import { Inbox } from 'lucide-react';
import clsx from 'clsx';

const BAND_ORDER: LeadTimeBand[] = ['IMMINENT', 'NEAR', 'WATCH', 'UNKNOWN'];

const BAND_EDGE: Record<LeadTimeBand, string> = {
  IMMINENT: 'border-l-imminent',
  NEAR: 'border-l-near',
  WATCH: 'border-l-watch',
  UNKNOWN: 'border-l-unknown',
};

interface Props {
  findings: RiskFinding[];
  onChange: () => void;
}

export function FindingsBandList({ findings, onChange }: Props) {
  const [snoozeFinding, setSnoozeFinding] = useState<RiskFinding | null>(null);
  const [assignFinding, setAssignFinding] = useState<RiskFinding | null>(null);
  const [feedbackFinding, setFeedbackFinding] = useState<RiskFinding | null>(null);
  const [feedbackVerdict, setFeedbackVerdict] = useState<FeedbackVerdict | null>(null);
  const navigate = useNavigate();
  const { selectedId, setSelectedId } = useFindingsStore();

  useEffect(() => {
    if (!selectedId) return;
    const hit = findings.find((f) => f.findingId === selectedId);
    setSelectedId(null);
    if (hit) navigate(`/findings/${hit.findingId}`);
  }, [selectedId, findings, setSelectedId, navigate]);

  const openDetail = (finding: RiskFinding) => navigate(`/findings/${finding.findingId}`);

  const grouped = useMemo(() => {
    const active = findings.filter(
      (f) => f.state !== 'closed' && f.state !== 'suppressed-as-duplicate',
    );
    const sorted = [...active].sort((a, b) => {
      const band = BAND_SEVERITY[a.leadTimeBand] - BAND_SEVERITY[b.leadTimeBand];
      if (band !== 0) return band;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
    return BAND_ORDER.map((band) => ({
      band,
      items: sorted.filter((f) => f.leadTimeBand === band),
    })).filter((g) => g.items.length > 0);
  }, [findings]);

  if (findings.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <EmptyState
          icon={<Inbox />}
          title="No findings on the board"
          hint="Signals are streaming; nothing has converged into a risk. When one does, it lands here by lead-time band."
          className="w-[420px] max-w-full py-12"
        />
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-y-auto scrollbar">
      <div className="flex flex-col gap-4 pb-2 max-w-3xl">
        {grouped.map(({ band, items }) => (
          <section key={band} className="flex flex-col gap-2">
            <div className="flex items-baseline gap-2 px-1">
              <span
                className={clsx(
                  'text-micro font-mono font-bold uppercase tracking-[0.1em]',
                  band === 'IMMINENT' && 'text-imminent',
                  band === 'NEAR' && 'text-near',
                  band === 'WATCH' && 'text-watch',
                  band === 'UNKNOWN' && 'text-ink-dim',
                )}
              >
                {band}
              </span>
              <span className="text-micro font-mono text-ink-dim tabular-nums">{items.length}</span>
            </div>
            <div className="flex flex-col gap-2">
              {items.map((f) => (
                <div key={f.findingId} className={clsx('border-l-[3px] pl-0', BAND_EDGE[band])}>
                  <FindingCard
                    finding={f}
                    onChange={onChange}
                    onOpenSnooze={setSnoozeFinding}
                    onOpenAssign={setAssignFinding}
                    onOpenFeedback={(finding, verdict) => {
                      setFeedbackFinding(finding);
                      setFeedbackVerdict(verdict);
                    }}
                    onOpenDetail={openDetail}
                  />
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      <SnoozeDialog
        finding={snoozeFinding}
        isOpen={snoozeFinding !== null}
        onClose={() => setSnoozeFinding(null)}
        onSuccess={onChange}
      />
      <AssignDialog
        finding={assignFinding}
        isOpen={assignFinding !== null}
        onClose={() => setAssignFinding(null)}
        onSuccess={onChange}
      />
      <FeedbackModal
        finding={feedbackFinding}
        verdict={feedbackVerdict}
        isOpen={feedbackFinding !== null && feedbackVerdict !== null}
        onClose={() => {
          setFeedbackFinding(null);
          setFeedbackVerdict(null);
        }}
        onSuccess={onChange}
      />
    </div>
  );
}
