import { useState } from 'react';
import type { RiskFinding, FeedbackVerdict } from '@/types';
import { transitionFinding } from '@/api';
import { Badge, Button, Card } from '@/components/atoms';
import { LeadTimeGauge } from '@/components/molecules/LeadTimeGauge';
import { LineageChip } from '@/components/molecules/LineageChip';
import { toast } from '@/stores/toasts';
import { AlertTriangle, User, Clock, ThumbsUp, ThumbsDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

/* Board card — scan path is fixed: band tape → title → lineage → actions.
   The 3px band edge and the tape carry severity; everything else is ink. */

const MAX_LINEAGE_CHIPS = 4;

interface FindingCardProps {
  finding: RiskFinding;
  onChange: () => void;
  onOpenSnooze?: (finding: RiskFinding) => void;
  onOpenAssign?: (finding: RiskFinding) => void;
  onOpenFeedback?: (finding: RiskFinding, verdict: FeedbackVerdict) => void;
  onOpenDetail?: (finding: RiskFinding) => void;
}

export function FindingCard({
  finding,
  onChange,
  onOpenSnooze,
  onOpenAssign,
  onOpenFeedback,
  onOpenDetail,
}: FindingCardProps) {
  const [isTransitioning, setIsTransitioning] = useState(false);

  const ack = async () => {
    setIsTransitioning(true);
    try {
      await transitionFinding(finding.findingId, 'acknowledged', 'Acknowledged by operator');
      toast.ok(`${finding.findingId} acknowledged`);
      onChange();
    } catch (err) {
      console.error('[FindingCard] Ack failure:', err);
      toast.error(`Failed to acknowledge ${finding.findingId}`);
    } finally {
      setIsTransitioning(false);
    }
  };

  const visibleLineage = finding.lineage?.slice(0, MAX_LINEAGE_CHIPS) ?? [];
  const hiddenLineage = (finding.lineage?.length ?? 0) - visibleLineage.length;

  return (
    <Card
      role="article"
      aria-labelledby={`finding-${finding.findingId}-title`}
      className={clsx(
        'group flex flex-col gap-2.5 relative overflow-hidden transition-colors duration-fast select-text',
        finding.leadTimeBand === 'IMMINENT' &&
          finding.state !== 'closed' &&
          'border-imminent/40 hover:border-imminent/70'
      )}
    >
      {/* 3px band edge — severity readable before anything else */}
      <div
        className={clsx(
          'absolute left-0 top-0 bottom-0 w-[3px]',
          finding.leadTimeBand === 'IMMINENT' ? 'bg-imminent' :
          finding.leadTimeBand === 'NEAR' ? 'bg-near' :
          finding.leadTimeBand === 'WATCH' ? 'bg-watch' : 'bg-unknown'
        )}
      />

      {/* 1 · Band: the signature lead-time tape leads the card */}
      <LeadTimeGauge band={finding.leadTimeBand} basis={finding.leadTimeBasis} size="sm" />

      {/* 2 · Title — loudest thing on the card after the tape: 14px 600 ink.
          Hover affordance is the chevron darkening + underline, never orange. */}
      <button
        type="button"
        onClick={() => onOpenDetail?.(finding)}
        className="text-left cursor-pointer group/title"
        aria-label={`Open finding ${finding.findingId}`}
      >
        <h3
          id={`finding-${finding.findingId}-title`}
          className="text-base font-semibold text-ink leading-snug flex items-start gap-1"
        >
          <span className="flex-1 truncate-2 group-hover/title:underline decoration-line-2 underline-offset-2">
            {finding.title}
          </span>
          <ChevronRight className="h-4 w-4 shrink-0 text-ink-dim/40 self-center group-hover/title:text-ink transition-colors duration-fast" />
        </h3>
      </button>

      {/* Metadata line — zone, id, confidence: data, therefore mono; 12px,
          clearly secondary to the 14px title above it */}
      <div className="flex items-center justify-between gap-2 text-xs font-mono text-ink-dim select-none">
        <span className="flex items-center gap-1.5 min-w-0">
          <span className="font-medium tracking-[0.06em] truncate">{finding.zoneId}</span>
          <span className="text-ink-dim/40 shrink-0">·</span>
          <span className="text-ink-dim/70 truncate">{finding.findingId}</span>
          {finding.shadow && (
            <Badge variant="generic" color="near" className="text-micro font-bold border-dashed shrink-0">
              SHADOW
            </Badge>
          )}
        </span>
        <span className="tabular-nums text-ink-dim/70 shrink-0" title="Detection confidence">
          {(finding.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Degradation banner — tinted well, ink prose, colored signal only */}
      {finding.confidenceDegraded && (
        <div className="flex items-baseline gap-1.5 bg-imminent/5 border border-imminent/10 p-1.5 rounded text-micro leading-normal">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 self-center text-imminent" />
          <div className="min-w-0">
            <span className="font-mono uppercase tracking-[0.08em] text-imminent font-semibold">Estimate degraded</span>
            <span className="text-ink-dim font-mono ml-1">— {finding.confidenceDegradedBy.join(', ')}</span>
          </div>
        </div>
      )}

      {/* Counterfactual — set apart by an ink rule; orange is not decoration */}
      {finding.counterfactual && (
        <p className="text-xs text-ink-dim leading-normal border-l-2 border-line-2 pl-2">
          <span className="text-micro font-mono uppercase tracking-[0.08em] text-ink-dim mr-1.5">If unmitigated</span>
          {finding.counterfactual}
        </p>
      )}

      {/* 3 · Lineage — capped; overflow stays honest with a +N chip */}
      {visibleLineage.length > 0 && (
        <div className="flex flex-wrap gap-1.5 select-none" aria-label="Contributing evidence signals">
          {visibleLineage.map((item) => (
            <LineageChip key={item} label={item} onClick={() => onOpenDetail?.(finding)} />
          ))}
          {hiddenLineage > 0 && (
            <button
              type="button"
              onClick={() => onOpenDetail?.(finding)}
              className="inline-flex items-center px-1.5 py-0.5 rounded-sm border border-dashed border-line text-micro font-mono text-ink-dim hover:text-ink hover:border-line-2 transition-colors duration-fast cursor-pointer tabular-nums"
              aria-label={`${hiddenLineage} more evidence signals`}
            >
              +{hiddenLineage}
            </button>
          )}
        </div>
      )}

      <div className="h-[1px] bg-line w-full select-none" />

      {/* 4 · Actions — Acknowledge stays present; secondary controls recede
          until the card is hovered or focused */}
      <footer className="flex items-center justify-between select-none">
        <div className="flex items-center gap-1.5">
          {finding.state === 'new' ? (
            <Button
              variant="primary"
              size="sm"
              loading={isTransitioning}
              onClick={ack}
              aria-label="Acknowledge finding"
            >
              Acknowledge
            </Button>
          ) : (
            <div className="text-micro font-mono text-ink-dim flex items-center gap-1 bg-panel-2 px-2 py-0.5 border border-line rounded">
              <span className="h-1.5 w-1.5 rounded-full bg-ink-dim" />
              <span className="uppercase">{finding.state}</span>
            </div>
          )}

          {finding.state !== 'closed' && finding.state !== 'resolved' && (
            <div className="flex items-center gap-0.5 opacity-60 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-fast">
              {onOpenAssign && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenAssign(finding)}
                  className="p-1 h-6 hover:bg-panel-2 text-ink-dim"
                  aria-label="Assign finding"
                  title="Assign to owner"
                >
                  <User className="h-3.5 w-3.5" />
                </Button>
              )}
              {onOpenSnooze && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenSnooze(finding)}
                  className="p-1 h-6 hover:bg-panel-2 text-ink-dim"
                  aria-label="Snooze finding"
                  title="Snooze alert"
                >
                  <Clock className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-fast">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onOpenFeedback?.(finding, 'useful')}
            className="p-1 h-6 hover:text-ok text-ink-dim hover:bg-panel-2"
            aria-label="Mark finding as useful"
            title="Mark useful"
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onOpenFeedback?.(finding, 'false-alarm')}
            className="p-1 h-6 hover:text-imminent text-ink-dim hover:bg-panel-2"
            aria-label="Mark finding as false alarm"
            title="Mark false alarm"
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </Button>
        </div>
      </footer>
    </Card>
  );
}
