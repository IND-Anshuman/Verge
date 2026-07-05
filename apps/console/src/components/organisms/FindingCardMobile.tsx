import { useState } from 'react';
import type { RiskFinding } from '@/types';
import { Badge } from '@/components/atoms';
import { ChevronRight, Check } from 'lucide-react';
import { transitionFinding } from '@/api';

interface FindingCardMobileProps {
  finding: RiskFinding;
  onChange: () => void;
  onOpenDetail?: (finding: RiskFinding) => void;
}

export function FindingCardMobile({ finding, onChange, onOpenDetail }: FindingCardMobileProps) {
  const [startX, setStartX] = useState<number | null>(null);
  const [translateX, setTranslateX] = useState(0);
  const [isAcknowledge, setIsAcknowledge] = useState(finding.state === 'acknowledged');

  const handleTouchStart = (e: React.TouchEvent) => {
    if (isAcknowledge) return;
    setStartX(e.touches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (startX === null || isAcknowledge) return;
    const diff = e.touches[0].clientX - startX;
    // Allow right swipe only (positive translation)
    if (diff > 0) {
      setTranslateX(Math.min(diff, 150));
    }
  };

  const handleTouchEnd = async () => {
    if (isAcknowledge) return;
    setStartX(null);
    if (translateX >= 120) {
      setTranslateX(150);
      try {
        await transitionFinding(finding.findingId, 'acknowledged', 'Swiped right to acknowledge on mobile device');
        setIsAcknowledge(true);
        onChange();
      } catch (err) {
        console.error('[SwipeAcknowledge] Failed:', err);
        setTranslateX(0);
      }
    } else {
      setTranslateX(0);
    }
  };

  return (
    <div className="relative overflow-hidden w-full h-24 select-none rounded border border-line">
      {/* Swipe action reveal background */}
      <div className="absolute inset-0 bg-ok/20 flex items-center pl-6 text-ok font-mono font-bold text-xs select-none">
        <Check className="h-4 w-4 mr-2 animate-bounce" />
        ACKNOWLEDGE ALARM...
      </div>

      {/* Main card body that swipes */}
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClick={() => onOpenDetail?.(finding)}
        className="absolute inset-0 bg-panel-2/95 flex items-center justify-between px-3 cursor-pointer select-text transition-transform duration-75"
        style={{ transform: `translateX(${translateX}px)` }}
      >
        <div className="flex flex-col gap-1 pr-4 truncate">
          <div className="flex items-center gap-1.5 shrink-0 select-none">
            <Badge variant="band" band={finding.leadTimeBand} className="text-[9px] font-bold py-0">
              {finding.leadTimeBand}
            </Badge>
            <span className="text-micro font-mono text-ink-dim truncate">ID: {finding.findingId}</span>
          </div>
          <h4 className="text-xs font-bold text-ink leading-relaxed truncate">{finding.title}</h4>
          <span className="text-[9px] font-mono text-ink-dim uppercase truncate">ZONE: {finding.zoneId}</span>
        </div>

        <div className="flex items-center gap-2 select-none shrink-0">
          {isAcknowledge ? (
            <Badge variant="generic" color="ok" className="font-mono text-micro font-bold py-0.5 uppercase">
              ACKED
            </Badge>
          ) : (
            <div className="flex items-center text-micro font-mono text-ink-dim/40 animate-pulse">
              <span>SWIPE</span>
              <ChevronRight className="h-3 w-3" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
