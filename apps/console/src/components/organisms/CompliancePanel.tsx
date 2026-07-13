import { useEffect, useMemo, useState } from 'react';
import { Card } from '@/components/atoms';
import { AlertCircle, Scale, ChevronRight, CircleCheck, CircleAlert } from 'lucide-react';
import { getComplianceReport, type ComplianceClause } from '@/api/platform';
import clsx from 'clsx';

/* Regulatory compliance drill-down (OISD / Factory Act / DGMS).
   Renders the deterministic gap report from services/compliance — every
   clause shows its actual requirement text and the machine-checkable
   reason it is satisfied or open. Honest gaps stay visible: a coke-oven
   plant genuinely lacking tank-farm controls should say so. */

type StatusFilter = 'all' | 'gap' | 'satisfied';

export function CompliancePanel() {
  const [report, setReport] = useState<{
    plant: string;
    coverageRatio: number;
    satisfied: number;
    gaps: number;
    total: number;
    clauses: ComplianceClause[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [openClause, setOpenClause] = useState<string | null>(null);

  useEffect(() => {
    getComplianceReport()
      .then((r) => {
        setReport(r);
        setError(null);
      })
      .catch(() => {
        setReport(null);
        setError('Compliance API unavailable.');
      });
  }, []);

  const clauses = useMemo(() => {
    if (!report) return [];
    const list = filter === 'all' ? report.clauses : report.clauses.filter((c) => c.status === filter);
    // Open gaps first — they are what a safety officer must act on.
    return [...list].sort((a, b) => (a.status === b.status ? 0 : a.status === 'gap' ? -1 : 1));
  }, [report, filter]);

  const coveragePct = report ? Math.round(report.coverageRatio * 100) : 0;

  return (
    <Card className="p-3 border-line bg-panel-2/30 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-micro font-mono font-bold text-ink-dim uppercase flex items-center gap-1.5">
          <Scale className="h-3.5 w-3.5" />
          Regulatory Compliance (OISD / Factory Act)
        </span>
        {report && (
          <div className="flex bg-bg border border-line p-0.5 rounded select-none">
            {(['all', 'gap', 'satisfied'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  'px-2 py-0.5 text-micro font-mono font-bold uppercase rounded-sm cursor-pointer transition-colors',
                  filter === f ? 'bg-panel text-ink border border-line' : 'text-ink-dim hover:text-ink'
                )}
              >
                {f === 'all' ? `ALL ${report.total}` : f === 'gap' ? `GAPS ${report.gaps}` : `OK ${report.satisfied}`}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="text-xs text-imminent flex items-center gap-2 font-mono">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}

      {report && (
        <>
          {/* Coverage bar */}
          <div className="flex items-center gap-2 font-mono text-xs select-none">
            <div className="flex-1 h-1.5 bg-bg border border-line rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full', coveragePct >= 90 ? 'bg-ok' : coveragePct >= 70 ? 'bg-near' : 'bg-imminent')}
                style={{ width: `${coveragePct}%` }}
              />
            </div>
            <span className="text-ink font-bold tabular-nums">{coveragePct}%</span>
            <span className="text-ink-dim text-micro uppercase">{report.plant}</span>
          </div>

          {/* Clause drill-down */}
          <div className="flex flex-col max-h-64 overflow-y-auto scrollbar -mx-1 px-1">
            {clauses.map((c) => {
              const open = openClause === c.clauseId;
              const gap = c.status === 'gap';
              return (
                <div key={c.clauseId} className="border-b border-line/60 last:border-b-0">
                  <button
                    onClick={() => setOpenClause(open ? null : c.clauseId)}
                    className="w-full flex items-center gap-2 py-1.5 text-left cursor-pointer group"
                    aria-expanded={open}
                  >
                    {gap ? (
                      <CircleAlert className="h-3.5 w-3.5 shrink-0 text-near" />
                    ) : (
                      <CircleCheck className="h-3.5 w-3.5 shrink-0 text-ok/70" />
                    )}
                    <span className="text-micro font-mono text-ink-dim shrink-0">{c.standard}</span>
                    <span className={clsx('text-xs truncate flex-1', gap ? 'text-ink font-semibold' : 'text-ink-dim group-hover:text-ink')}>
                      {c.title}
                    </span>
                    <ChevronRight
                      className={clsx('h-3.5 w-3.5 shrink-0 text-ink-dim/50 transition-transform', open && 'rotate-90')}
                    />
                  </button>
                  {open && (
                    <div className="pb-2 pl-5 flex flex-col gap-1.5 select-text">
                      <p className="text-xs text-ink leading-normal">{c.requirement}</p>
                      <div className="flex flex-wrap items-center gap-1.5 font-mono text-micro">
                        <span
                          className={clsx(
                            'px-1.5 py-0.5 rounded-sm border font-bold uppercase',
                            gap ? 'text-near border-near/30 bg-near/10' : 'text-ok border-ok/30 bg-ok/10'
                          )}
                        >
                          {c.status}
                        </span>
                        <span className="px-1.5 py-0.5 rounded-sm border border-line bg-panel text-ink-dim">
                          {c.oisdRef}
                        </span>
                        <span className="px-1.5 py-0.5 rounded-sm border border-line bg-panel text-ink-dim">
                          capability: {c.capability}
                        </span>
                        {c.isPlatform && (
                          <span className="px-1.5 py-0.5 rounded-sm border border-watch/30 bg-watch/10 text-watch">
                            platform-provided
                          </span>
                        )}
                      </div>
                      <p className="text-micro font-mono text-ink-dim leading-normal">↳ {c.reason}</p>
                    </div>
                  )}
                </div>
              );
            })}
            {clauses.length === 0 && (
              <span className="text-micro font-mono text-ink-dim py-2">No clauses match this filter.</span>
            )}
          </div>
        </>
      )}
    </Card>
  );
}
