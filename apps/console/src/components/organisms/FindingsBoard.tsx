import { useState } from 'react';
import type { RiskFinding, FindingState, FeedbackVerdict } from '@/types';
import { FindingCard } from '@/components/organisms/FindingCard';
import { SnoozeDialog } from '@/components/molecules/SnoozeDialog';
import { AssignDialog } from '@/components/molecules/AssignDialog';
import { FeedbackModal } from '@/components/molecules/FeedbackModal';
import { FindingDetailModal } from '@/components/organisms/FindingDetailModal';
import clsx from 'clsx';

const COLUMNS: { state: FindingState; label: string; headerColor: string }[] = [
  { state: 'new', label: 'NEW ALERT', headerColor: 'border-t-[3px] border-t-imminent' },
  { state: 'acknowledged', label: 'ACKNOWLEDGED', headerColor: 'border-t-[3px] border-t-near' },
  { state: 'assigned', label: 'ASSIGNED', headerColor: 'border-t-[3px] border-t-watch' },
  { state: 'in-progress', label: 'IN PROGRESS', headerColor: 'border-t-[3px] border-t-accent' },
  { state: 'escalated', label: 'ESCALATED', headerColor: 'border-t-[3px] border-t-imminent' },
  { state: 'resolved', label: 'RESOLVED', headerColor: 'border-t-[3px] border-t-ok' },
];

interface FindingsBoardProps {
  findings: RiskFinding[];
  onChange: () => void;
}

export function FindingsBoard({ findings, onChange }: FindingsBoardProps) {
  const [snoozeFinding, setSnoozeFinding] = useState<RiskFinding | null>(null);
  const [assignFinding, setAssignFinding] = useState<RiskFinding | null>(null);
  const [feedbackFinding, setFeedbackFinding] = useState<RiskFinding | null>(null);
  const [feedbackVerdict, setFeedbackVerdict] = useState<FeedbackVerdict | null>(null);
  const [detailFinding, setDetailFinding] = useState<RiskFinding | null>(null);

  const handleOpenFeedback = (finding: RiskFinding, verdict: FeedbackVerdict) => {
    setFeedbackFinding(finding);
    setFeedbackVerdict(verdict);
  };

  return (
    <div className="h-full w-full overflow-x-auto overflow-y-hidden pb-2 scrollbar">
      <div className="flex gap-3 h-full min-w-[1200px] px-1 select-none">
        {COLUMNS.map(({ state, label, headerColor }) => {
          const items = findings.filter((f) => f.state === state);

          return (
            <section
              key={state}
              className={clsx(
                'flex-1 flex flex-col h-full bg-panel/30 border border-line rounded-md overflow-hidden',
                headerColor
              )}
            >
              {/* Column Header */}
              <div className="h-10 px-3 border-b border-line bg-panel-2/50 flex items-center justify-between shrink-0 select-none">
                <span className="text-micro font-mono font-bold text-ink uppercase tracking-wider">
                  {label}
                </span>
                <span className="px-1.5 py-0.5 rounded bg-line text-micro font-mono text-ink-dim font-bold tabular-nums">
                  {items.length}
                </span>
              </div>

              {/* Column Cards Container */}
              <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-2 scrollbar select-text">
                {items.length === 0 ? (
                  <div className="flex-1 flex items-center justify-center border border-dashed border-line/50 rounded-sm p-4 text-center">
                    <span className="text-micro font-mono text-ink-dim/40 uppercase">
                      NO ACTIVE FINDINGS
                    </span>
                  </div>
                ) : (
                  items.map((f) => (
                    <FindingCard
                      key={f.findingId}
                      finding={f}
                      onChange={onChange}
                      onOpenSnooze={setSnoozeFinding}
                      onOpenAssign={setAssignFinding}
                      onOpenFeedback={handleOpenFeedback}
                      onOpenDetail={setDetailFinding}
                    />
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>

      {/* Snooze dialog popup */}
      <SnoozeDialog
        finding={snoozeFinding}
        isOpen={snoozeFinding !== null}
        onClose={() => setSnoozeFinding(null)}
        onSuccess={onChange}
      />

      {/* Assign dialog popup */}
      <AssignDialog
        finding={assignFinding}
        isOpen={assignFinding !== null}
        onClose={() => setAssignFinding(null)}
        onSuccess={onChange}
      />

      {/* Feedback dialog popup */}
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

      {/* Details dialog popup */}
      <FindingDetailModal
        finding={detailFinding}
        isOpen={detailFinding !== null}
        onClose={() => setDetailFinding(null)}
        onSuccess={onChange}
      />
    </div>
  );
}
