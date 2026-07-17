import { useEffect, useState, type ReactNode } from 'react';
import type { RiskFinding } from '@/types';
import { Modal, Button, Badge } from '@/components/atoms';
import { transitionFinding, getFindingExposure } from '@/api';
import type { FindingExposure } from '@/api/workers';
import { TemporalConvergenceChart } from './TemporalConvergenceChart';
import { LeadTimeGauge } from '@/components/molecules/LeadTimeGauge';
import { InvestigationPanel } from '@/components/molecules/InvestigationPanel';
import { ExportEvidenceButton } from '@/components/molecules/ExportEvidenceButton';
import { ExportIncidentReportButton } from '@/components/molecules/ExportIncidentReportButton';
import { FindingAuditTab } from '@/components/molecules/FindingAuditTab';
import { lineageIcon } from '@/components/molecules/LineageChip';
import {
  FileText,
  ShieldCheck,
  TrendingUp,
  Sliders,
  AlertTriangle,
} from 'lucide-react';
import clsx from 'clsx';

/* Finding detail — an investigation cockpit, not a CRUD modal.
   Identity pinned in the header; disposition facts in a left rail that
   reads like a title block; evidence in stable tabs on the right. */

interface FindingDetailModalProps {
  finding: RiskFinding | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type TabType = 'overview' | 'chart' | 'lineage' | 'audit';

/* One disposition fact — hairline-separated definition row (title-block
   grammar), not a box inside a box. */
function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-2 py-1.5 border-b border-line/70">
      <span className="text-micro font-mono uppercase tracking-[0.08em] text-ink-dim shrink-0">
        {label}
      </span>
      <span className="text-xs font-mono text-ink text-right tabular-nums min-w-0">{children}</span>
    </div>
  );
}

export function FindingDetailModal({ finding, isOpen, onClose, onSuccess }: FindingDetailModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [exposure, setExposure] = useState<FindingExposure | null>(null);

  const findingId = finding?.findingId ?? null;
  useEffect(() => {
    if (!isOpen || !findingId) return;
    // Each finding opens on its brief with fresh exposure data
    setActiveTab('overview');
    let cancelled = false;
    getFindingExposure(findingId)
      .then((e) => {
        if (!cancelled) setExposure(e);
      })
      .catch(() => {
        if (!cancelled) setExposure(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isOpen, findingId]);

  if (!finding) return null;

  const tabs: { value: TabType; label: string; icon: React.ReactNode }[] = [
    { value: 'overview', label: 'BRIEF', icon: <Sliders className="h-3.5 w-3.5" /> },
    { value: 'chart', label: 'SIGNALS', icon: <TrendingUp className="h-3.5 w-3.5" /> },
    { value: 'lineage', label: 'LINEAGE', icon: <FileText className="h-3.5 w-3.5" /> },
    { value: 'audit', label: 'AUDIT', icon: <ShieldCheck className="h-3.5 w-3.5" /> },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <span className="flex items-center gap-2 min-w-0">
          <span className="truncate">{finding.title}</span>
          {finding.shadow && (
            <Badge variant="generic" color="near" className="text-micro font-bold border-dashed shrink-0">
              SHADOW
            </Badge>
          )}
        </span>
      }
      description={
        <span className="font-mono text-micro tracking-[0.06em]">
          {finding.findingId} · {finding.zoneId} · investigation
        </span>
      }
      size="2xl"
    >
      <div className="flex flex-col md:flex-row gap-4 h-[540px] overflow-hidden text-ink">
        {/* Left rail — disposition title block */}
        <div className="w-full md:w-64 flex flex-col border-r border-line pr-4 select-none overflow-y-auto scrollbar shrink-0">
          <span className="ruled-label mb-2">Lead time to breach</span>
          <LeadTimeGauge band={finding.leadTimeBand} basis={finding.leadTimeBasis} size="md" />

          <span className="ruled-label mt-4 mb-1">Disposition</span>
          <Fact label="State">
            <span className="inline-flex items-center gap-1.5 uppercase font-semibold">
              <span className="h-1.5 w-1.5 rounded-full bg-ink-dim" />
              {finding.state}
            </span>
          </Fact>
          <Fact label="Confidence">{(finding.confidence * 100).toFixed(0)}%</Fact>
          <Fact label="Estimate quality">
            <span className="uppercase">{finding.estimateQuality}</span>
          </Fact>
          {finding.owner && (
            <Fact label="Assignee">
              <span className="uppercase">{finding.owner}</span>
            </Fact>
          )}

          {exposure && (
            <>
              <span className="ruled-label mt-4 mb-1">Personnel exposure</span>
              <div
                className={clsx(
                  'border rounded px-2.5 py-2 flex flex-col gap-0.5 font-mono',
                  exposure.headcountAtRisk > 0
                    ? 'border-near/40 bg-near/5'
                    : 'border-line bg-panel-2/50'
                )}
              >
                <span
                  className={clsx(
                    'text-sm font-bold tabular-nums',
                    exposure.headcountAtRisk > 0 ? 'text-near' : 'text-ink-dim'
                  )}
                >
                  {exposure.headcountAtRisk} at risk
                </span>
                <span className="text-micro text-ink-dim">
                  {exposure.inZone.length} in zone · {exposure.inAdjacent.length} adjacent
                  {exposure.staleFixes > 0 && ` · ${exposure.staleFixes} stale fix`}
                </span>
              </div>
            </>
          )}

          {/* Respond — grouped, explicit; never hidden in a menu */}
          <div className="mt-auto flex flex-col gap-2 pt-4">
            <span className="ruled-label">Respond</span>
            {finding.shadow && (
              <Button
                variant="primary"
                size="sm"
                onClick={async () => {
                  try {
                    await transitionFinding(
                      finding.findingId,
                      'acknowledged',
                      'Promoted shadow finding to live alert',
                      'shadow-promote',
                    );
                    onSuccess();
                    onClose();
                  } catch (err) {
                    console.error('[DetailModal] Promotion failed:', err);
                  }
                }}
                className="w-full text-micro font-mono font-bold uppercase bg-near/20 border-near/40 text-near hover:bg-near/30"
              >
                Promote to Live
              </Button>
            )}
            <ExportEvidenceButton finding={finding} />
            <ExportIncidentReportButton finding={finding} />
          </div>
        </div>

        {/* Right column — evidence tabs */}
        <div className="flex-1 flex flex-col gap-3 overflow-hidden min-w-0">
          <div className="flex border-b border-line select-none shrink-0" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                role="tab"
                aria-selected={activeTab === tab.value}
                onClick={() => setActiveTab(tab.value)}
                className={clsx(
                  'flex items-center gap-1.5 h-8 px-3 text-micro font-semibold font-mono tracking-[0.08em] border-b-2 -mb-px transition-colors duration-fast cursor-pointer',
                  activeTab === tab.value
                    ? 'border-ink text-ink'
                    : 'border-transparent text-ink-dim hover:text-ink'
                )}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto pr-1 scrollbar">
            {activeTab === 'overview' && (
              <div className="flex flex-col gap-4">
                <p className="text-xs text-ink-dim/90 leading-relaxed">
                  Independent signals converged into a compound risk. The engine places the
                  breach window in the{' '}
                  <span
                    className="font-mono font-semibold"
                    style={{
                      color:
                        finding.leadTimeBand === 'IMMINENT' ? 'var(--imminent)' :
                        finding.leadTimeBand === 'NEAR' ? 'var(--near)' :
                        finding.leadTimeBand === 'WATCH' ? 'var(--watch)' : 'var(--unknown)',
                    }}
                  >
                    {finding.leadTimeBand}
                  </span>{' '}
                  band.
                </p>

                {/* Counterfactual — the differentiator gets display type;
                    the emphasis is size and ink, never orange decoration */}
                {finding.counterfactual && (
                  <div className="border-l-2 border-line-2 pl-3 py-1 flex flex-col gap-1">
                    <span className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim">
                      Counterfactual — if unmitigated
                    </span>
                    <p className="text-md font-medium text-ink leading-relaxed">
                      {finding.counterfactual}
                    </p>
                  </div>
                )}

                {finding.confidenceDegraded && (
                  <div className="bg-imminent/5 border border-imminent/10 p-3 rounded flex items-start gap-2 text-xs leading-normal">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-imminent" />
                    <div className="text-ink">
                      <span className="font-mono text-micro uppercase tracking-[0.08em] text-imminent font-semibold">
                        Estimate degraded
                      </span>{' '}
                      — confidence lowered by stale or unreliable signals:
                      <span className="font-semibold block mt-1 font-mono">
                        {finding.confidenceDegradedBy.join(', ')}
                      </span>
                    </div>
                  </div>
                )}

                <span className="ruled-label">Investigate</span>
                <InvestigationPanel findingId={finding.findingId} />
              </div>
            )}

            {activeTab === 'chart' && (
              <div className="h-full flex items-center justify-center">
                <TemporalConvergenceChart finding={finding} />
              </div>
            )}

            {activeTab === 'lineage' && (
              <div className="flex flex-col gap-2 font-mono text-xs">
                {finding.lineage && finding.lineage.length > 0 ? (
                  finding.lineage.map((item, idx) => {
                    const signal = finding.contributingSignals?.find(
                      (s) => `${s.kind}:${s.refId}` === item,
                    );
                    return (
                      <div
                        key={idx}
                        className="p-3 border border-line bg-panel-2/30 rounded flex flex-col gap-1 hover-elevate"
                      >
                        <div className="flex justify-between items-center gap-2">
                          <span className="font-semibold text-ink inline-flex items-center gap-1.5 min-w-0">
                            {lineageIcon(item)}
                            <span className="truncate">{item}</span>
                          </span>
                          {signal?.ts && (
                            <span className="text-micro text-ink-dim tabular-nums shrink-0">
                              {new Date(signal.ts).toLocaleTimeString()}
                            </span>
                          )}
                        </div>
                        {signal?.summary && (
                          <span className="text-micro text-ink-dim leading-normal">
                            {signal.summary}
                          </span>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div className="border border-dashed border-line rounded-md py-8 text-center">
                    <span className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim/60">
                      No evidence signals attached
                    </span>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'audit' && <FindingAuditTab findingId={finding.findingId} />}
          </div>
        </div>
      </div>
    </Modal>
  );
}
