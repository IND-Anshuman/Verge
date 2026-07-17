import { useEffect, useState } from 'react';
import { AlertTriangle, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import { getDegradationStatus, type DegradationBanner } from '@/api/platform';

/* Degradation strip — chrome recedes, state advances. ONE collapsed hairline
   strip: the signal word carries severity color, the reason stays ink, and
   the full list only exists when the operator asks for it. Never a stack of
   tinted bars above the content. */

const SEVERITY_RANK: Record<DegradationBanner['severity'], number> = {
  critical: 2,
  warn: 1,
  info: 0,
};

const SEVERITY_META: Record<DegradationBanner['severity'], { word: string; signal: string }> = {
  critical: { word: 'Critical', signal: 'text-imminent' },
  warn: { word: 'Degraded', signal: 'text-near' },
  info: { word: 'Notice', signal: 'text-watch' },
};

export function DegradationBannerStrip() {
  const [banners, setBanners] = useState<DegradationBanner[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      getDegradationStatus()
        .then((body) => {
          if (!cancelled) setBanners(body.banners);
        })
        .catch(() => {
          if (!cancelled) setBanners([]);
        });
    };
    load();
    const id = window.setInterval(load, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  if (banners.length === 0) return null;

  const worst = banners.reduce((a, b) =>
    SEVERITY_RANK[b.severity] > SEVERITY_RANK[a.severity] ? b : a,
  );
  const meta = SEVERITY_META[worst.severity];

  return (
    <div className="border-b border-line bg-panel shrink-0 select-none">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full h-7 px-4 flex items-center gap-2 text-left cursor-pointer hover:bg-panel-2/50 transition-colors duration-fast"
      >
        <AlertTriangle className={clsx('h-3 w-3 shrink-0', meta.signal)} />
        <span
          className={clsx(
            'text-micro font-mono uppercase tracking-[0.1em] font-semibold shrink-0',
            meta.signal,
          )}
        >
          {meta.word} · <span className="tabular-nums">{banners.length}</span>
        </span>
        <span className="text-xs text-ink-dim truncate min-w-0">{worst.message}</span>
        <ChevronDown
          className={clsx(
            'h-3 w-3 text-ink-dim shrink-0 ml-auto transition-transform duration-fast',
            expanded && 'rotate-180',
          )}
        />
      </button>

      {expanded && (
        <div className="border-t border-line/60">
          {banners.map((b) => {
            const rowMeta = SEVERITY_META[b.severity];
            return (
              <div
                key={b.code}
                className="py-1.5 px-4 pl-9 flex items-baseline gap-2 border-b border-line/40 last:border-b-0 select-text"
              >
                <span
                  className={clsx(
                    'text-micro font-mono uppercase tracking-[0.1em] font-semibold shrink-0',
                    rowMeta.signal,
                  )}
                >
                  {rowMeta.word}
                </span>
                <span className="text-xs text-ink min-w-0">{b.message}</span>
                <span className="ml-auto text-micro font-mono text-ink-dim/70 shrink-0 hidden sm:inline">
                  {b.code}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
