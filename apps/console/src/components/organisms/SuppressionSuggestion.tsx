import { useState } from 'react';
import type { RiskFinding } from '@/types';
import { Card, Button } from '@/components/atoms';
import { Merge, Check, X } from 'lucide-react';
import { transitionFinding } from '@/api';

interface SuppressionSuggestionProps {
  activeFindings: RiskFinding[];
  onChange: () => void;
}

export function SuppressionSuggestion({ activeFindings, onChange }: SuppressionSuggestionProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Find candidate duplicate findings.
  // In a real system, Verge risk engine flags findings with `suppressedAsPrimaryId` or similar recommendation metadata.
  // Let's filter findings in the 'new' or 'acknowledged' states that share zones and titles to simulate suggestions.
  const suggestions = activeFindings.filter((f) => f.state === 'new' && f.title.includes('Methane') && f.findingId !== 'rf-0491');

  if (suggestions.length === 0) return null;

  const handleConfirm = async (duplicateId: string) => {
    setIsSubmitting(true);
    try {
      // Transition state to 'suppressed-as-duplicate'
      await transitionFinding(
        duplicateId,
        'suppressed-as-duplicate',
        'Operator approved duplicate suppression suggestion. Merged into rf-0491.'
      );
      onChange();
    } catch (err) {
      console.error('[SuppressionSuggestion] Merge failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async (duplicateId: string) => {
    setIsSubmitting(true);
    try {
      // Discard suggestion (simulated by marking it as acknowledged so it doesn't trigger the recommendation block)
      await transitionFinding(
        duplicateId,
        'acknowledged',
        'Operator rejected suppression suggestion. Kept as independent alert.'
      );
      onChange();
    } catch (err) {
      console.error('[SuppressionSuggestion] Rejection failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 shrink-0 select-none">
      {suggestions.map((item) => (
        <Card
          key={item.findingId}
          className="border-accent/30 bg-accent/5 p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-ink"
        >
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 bg-accent/15 border border-accent/25 rounded text-accent shrink-0 mt-0.5">
              <Merge className="h-4 w-4" />
            </div>
            <div className="flex flex-col gap-0.5">
              <div className="text-xs font-bold flex items-center gap-1.5">
                <span>COLLAPSE SUGGESTION: duplicate risk finding detected</span>
                <span className="text-micro font-mono bg-accent/20 px-1 border border-accent/30 rounded text-accent">
                  CO-CONVERGENCE
                </span>
              </div>
              <p className="text-xs text-ink-dim leading-relaxed">
                Verge recommends merging finding <code className="text-accent">{item.findingId}</code> ({item.title}) into primary alert <code className="text-accent">rf-0491</code> in {item.zoneId}. Both share identical sensor lineages.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleReject(item.findingId)}
              disabled={isSubmitting}
              className="text-ink-dim hover:text-imminent hover:bg-imminent/10 hover:border-imminent/20"
              icon={<X className="h-3.5 w-3.5" />}
            >
              Reject
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleConfirm(item.findingId)}
              disabled={isSubmitting}
              className="bg-accent/20 border-accent/40 text-accent hover:bg-accent/30"
              icon={<Check className="h-3.5 w-3.5" />}
            >
              Approve Merge
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
