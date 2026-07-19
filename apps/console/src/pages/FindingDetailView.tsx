import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import type { RiskFinding, FindingState } from '@/types';
import { getFinding, transitionFinding, getFindingExposure } from '@/api';
import type { FindingExposure } from '@/api/workers';
import { Button, Badge, EmptyState, Skeleton } from '@/components/atoms';
import { LeadTimeGauge } from '@/components/molecules/LeadTimeGauge';
import { InvestigationPanel } from '@/components/molecules/InvestigationPanel';
import { ExportEvidenceButton } from '@/components/molecules/ExportEvidenceButton';
import { ExportIncidentReportButton } from '@/components/molecules/ExportIncidentReportButton';
import { FindingAuditTab } from '@/components/molecules/FindingAuditTab';
import { lineageIcon } from '@/components/molecules/LineageChip';
import { TemporalConvergenceChart } from '@/components/organisms/TemporalConvergenceChart';
import { FindingLivePanel } from '@/components/organisms/FindingLivePanel';
import {
  ArrowLeft,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';

/* ── Finding page (/findings/:id) ────────────────────────────────────
   The full-page successor to the detail modal (design_plan §6.2): one
   finding, read top-to-bottom — Summary · Live · Signals · Investigate · Ask · Respond.
   The lead-time band gets the §13.1 "display moment" treatment up top: a
   mission clock, not a KPI tile. Everything below stays flat Instrument
   Paper; the rail is the instrument, the column is the brief. */

const BAND_VAR: Record<RiskFinding['leadTimeBand'], string> = {
  IMMINENT: 'var(--imminent)',
  NEAR: 'var(--near)',
  WATCH: 'var(--watch)',
  UNKNOWN: 'var(--unknown)',
};

const BAND_WINDOW: Record<RiskFinding['leadTimeBand'], string> = {
  IMMINENT: 'under 15 min to breach',
  NEAR: '15–45 min to breach',
  WATCH: 'over 45 min to breach',
  UNKNOWN: 'insufficient signal for an estimate',
};

/* One disposition fact — hairline definition row, title-block grammar. */
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

/* Ruled page section — the sequential blocks of §6.2. */
function Section({ label, children }: { label: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="ruled-label">{label}</h2>
      {children}
    </section>
  );
}

export default function FindingDetailView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [finding, setFinding] = useState<RiskFinding | null>(null);
  const [exposure, setExposure] = useState<FindingExposure | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<FindingState | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      if (!id) return;
      try {
        const f = await getFinding(id, signal);
        if (signal?.aborted) return;
        setFinding(f);
        setError(null);
        // Exposure is best-effort — a missing worker never blocks the brief.
        getFindingExposure(id)
          .then((e) => !signal?.aborted && setExposure(e))
          .catch(() => !signal?.aborted && setExposure(null));
      } catch {
        if (signal?.aborted) return;
        setFinding(null);
        setError('Finding not found, or the API gateway is offline.');
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [id],
  );

  useEffect(() => {
    setLoading(true);
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  const transition = useCallback(
    async (to: FindingState, reasonText: string, reasonCode: string) => {
      if (!finding) return;
      setActing(to);
      try {
        await transitionFinding(finding.findingId, to, reasonText, reasonCode);
        await load();
      } catch (err) {
        console.error('[FindingDetail] transition failed:', err);
      } finally {
        setActing(null);
      }
    },
    [finding, load],
  );

  // ── Loading — shaped like the page, not a spinner island ──────────
  if (loading) {
    return (
      <div className="h-full w-full overflow-y-auto scrollbar bg-bg">
        <div className="mx-auto max-w-5xl p-6 flex flex-col gap-6" aria-busy="true" aria-label="Loading finding">
          <Skeleton className="h-4 w-24" />
          <div className="flex items-start justify-between gap-6 border-b border-line pb-6">
            <div className="flex flex-col gap-3">
              <Skeleton className="h-8 w-96" />
              <Skeleton className="h-3 w-64" />
            </div>
            <Skeleton className="h-16 w-56" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_300px] gap-8">
            <div className="flex flex-col gap-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
            <Skeleton className="h-64 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // ── Not found / offline ───────────────────────────────────────────
  if (error || !finding) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-bg p-6">
        <EmptyState
          icon={<FileWarning />}
          title="This finding could not be opened"
          hint={error ?? 'It may have been closed, or the id is unknown.'}
          action={
            <Button variant="secondary" size="sm" onClick={() => navigate('/')}>
              Back to board
            </Button>
          }
          className="w-[440px] max-w-full"
        />
      </div>
    );
  }

  const band = finding.leadTimeBand;
  const bandColor = BAND_VAR[band];
  const isActionable =
    finding.state !== 'resolved' && finding.state !== 'closed' && finding.state !== 'suppressed-as-duplicate';

  return (
    <div className="h-full w-full overflow-y-auto scrollbar bg-bg text-ink">
      <div className="mx-auto max-w-5xl p-6 flex flex-col gap-6">
        {/* Back to triage — short path home (D5) */}
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-micro font-mono uppercase tracking-[0.1em] text-ink-dim hover:text-ink transition-colors duration-fast w-fit"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Board
        </Link>

        {/* ── Hero header — title carries weight (§13.1); band is the mission clock ── */}
        <header className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 border-b border-line pb-6">
          <div className="flex flex-col gap-2 min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="text-micro font-mono uppercase tracking-[0.12em] text-ink-dim">
                {finding.findingId} · {finding.zoneId}
              </span>
              {finding.shadow && (
                <Badge variant="generic" color="near" className="text-micro font-bold border-dashed">
                  SHADOW
                </Badge>
              )}
            </div>
            {/* h1 bigger than a board title — this is the one screen about this finding */}
            <h1 className="text-2xl md:text-3xl font-semibold leading-tight tracking-tight text-ink">
              {finding.title}
            </h1>
            <span className="text-micro font-mono text-ink-dim">
              Opened {new Date(finding.createdAt).toLocaleString()}
            </span>
          </div>

          {/* Hero numeral: the band as a standing mission clock, right-aligned */}
          <div className="flex flex-col items-start md:items-end gap-1 shrink-0">
            <span
              className="text-3xl md:text-4xl font-semibold tracking-tight tabular-nums leading-none"
              style={{ color: bandColor }}
            >
              {band}
            </span>
            <span className="text-micro font-mono uppercase tracking-[0.08em] text-ink-dim">
              {BAND_WINDOW[band]}
            </span>
          </div>
        </header>

        {/* ── Body: brief column + instrument rail ───────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_300px] gap-8 items-start">
          {/* Main column — sequential ruled sections */}
          <div className="flex flex-col gap-8 min-w-0">
            {/* 1 · Summary */}
            <Section label="Summary">
              <p className="text-sm text-ink-dim/90 leading-relaxed">
                Independent signals converged into a compound risk. The engine places the breach
                window in the{' '}
                <span className="font-mono font-semibold" style={{ color: bandColor }}>
                  {band}
                </span>{' '}
                band.
              </p>

              {finding.counterfactual && (
                <div className="border-l-2 border-line-2 pl-4 py-1 flex flex-col gap-1">
                  <span className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim">
                    Counterfactual — if unmitigated
                  </span>
                  <p className="text-lg font-medium text-ink leading-snug">{finding.counterfactual}</p>
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
            </Section>

            {/* 2 · Live — telemetry, permits, zone camera, radio */}
            <Section label="Live">
              <FindingLivePanel finding={finding} />
            </Section>

            {/* 3 · Signals — lineage + convergence chart */}
            <Section label="Signals">
              {finding.lineage && finding.lineage.length > 0 ? (
                <div className="flex flex-col gap-2 font-mono text-xs">
                  {finding.lineage.map((item, idx) => {
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
                          <span className="text-micro text-ink-dim leading-normal">{signal.summary}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="border border-dashed border-line rounded-md py-6 text-center">
                  <span className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim/60">
                    No evidence signals attached
                  </span>
                </div>
              )}

              <div className="border border-line rounded-md bg-panel p-3">
                <TemporalConvergenceChart finding={finding} />
              </div>
            </Section>

            {/* 4 · Investigate */}
            <Section label="Investigate">
              <InvestigationPanel findingId={finding.findingId} />
            </Section>

            {/* 5 · Ask — deep-link to Copilot scoped to this finding (§6.2) */}
            <Section label="Ask">
              <Link
                to={`/knowledge?finding=${encodeURIComponent(finding.findingId)}`}
                className="group flex items-center justify-between gap-3 border border-line rounded-md bg-panel p-3 hover-elevate"
              >
                <span className="flex items-start gap-2.5 min-w-0">
                  <MessageSquare className="h-4 w-4 text-ink-dim shrink-0 mt-0.5" />
                  <span className="flex flex-col min-w-0">
                    <span className="text-xs font-medium text-ink">Ask Plant Copilot about this finding</span>
                    <span className="text-micro text-ink-dim leading-normal">
                      Opens a grounded, cited thread scoped to {finding.findingId} in Living Knowledge.
                    </span>
                  </span>
                </span>
                <ChevronRight className="h-4 w-4 text-ink-dim group-hover:text-ink transition-colors shrink-0" />
              </Link>
            </Section>

            {/* Audit trail — integrity is part of the record, not a hidden tab */}
            <Section label="Audit">
              <FindingAuditTab findingId={finding.findingId} />
            </Section>
          </div>

          {/* Instrument rail — sticky on desktop */}
          <aside className="flex flex-col gap-5 lg:sticky lg:top-4 select-none">
            <div className="flex flex-col gap-2">
              <span className="ruled-label">Lead time to breach</span>
              {/* The console's one tactile instrument (§13.4) */}
              <div className="instrument-bezel p-3">
                <LeadTimeGauge band={finding.leadTimeBand} basis={finding.leadTimeBasis} size="md" />
              </div>
            </div>

            <div className="flex flex-col">
              <span className="ruled-label mb-1">Disposition</span>
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
            </div>

            {exposure && (
              <div className="flex flex-col gap-1">
                <span className="ruled-label mb-1">Personnel exposure</span>
                <div
                  className={clsx(
                    'border rounded px-2.5 py-2 flex flex-col gap-0.5 font-mono',
                    exposure.headcountAtRisk > 0 ? 'border-near/40 bg-near/5' : 'border-line bg-panel-2/50',
                  )}
                >
                  <span
                    className={clsx(
                      'text-sm font-bold tabular-nums',
                      exposure.headcountAtRisk > 0 ? 'text-near' : 'text-ink-dim',
                    )}
                  >
                    {exposure.headcountAtRisk} at risk
                  </span>
                  <span className="text-micro text-ink-dim">
                    {exposure.inZone.length} in zone · {exposure.inAdjacent.length} adjacent
                    {exposure.staleFixes > 0 && ` · ${exposure.staleFixes} stale fix`}
                  </span>
                </div>
              </div>
            )}

            {/* Respond — grouped, explicit; every control hits a real API (D4) */}
            <div className="flex flex-col gap-2">
              <span className="ruled-label">Respond</span>

              {finding.shadow && (
                <Button
                  variant="primary"
                  size="sm"
                  loading={acting === 'acknowledged'}
                  onClick={() =>
                    transition('acknowledged', 'Promoted shadow finding to live alert', 'shadow-promote')
                  }
                  className="w-full text-micro font-mono font-bold uppercase bg-near/20 border-near/40 text-near hover:bg-near/30"
                >
                  Promote to live
                </Button>
              )}

              {!finding.shadow && isActionable && (
                <>
                  {finding.state === 'new' && (
                    <Button
                      variant="primary"
                      size="sm"
                      loading={acting === 'acknowledged'}
                      onClick={() => transition('acknowledged', 'Acknowledged from finding page', 'ack')}
                      className="w-full"
                    >
                      Acknowledge
                    </Button>
                  )}
                  {finding.state !== 'escalated' && (
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={acting === 'escalated'}
                      onClick={() => transition('escalated', 'Escalated from finding page', 'escalate')}
                      className="w-full"
                    >
                      Escalate
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    loading={acting === 'resolved'}
                    onClick={() => transition('resolved', 'Resolved from finding page', 'resolve')}
                    className="w-full"
                  >
                    Resolve
                  </Button>
                </>
              )}

              <ExportEvidenceButton finding={finding} />
              <ExportIncidentReportButton finding={finding} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
