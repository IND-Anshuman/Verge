import type { LeadTimeBand } from '@/types';
import clsx from 'clsx';

/* ── LeadTimeGauge — Verge's signature instrument ────────────────────
   A minutes-to-breach tape: WATCH >45 · NEAR 15–45 · IMMINENT <15, with
   a hard breach end-stop at zero. The marker sits at the *midpoint of
   the forecast band* and the band's extent is underlined — the backend
   deliberately never emits a point ETA (P4: bands, not fake precision),
   so the gauge doesn't render one. UNKNOWN parks a hollow marker and
   dims the tape: honest uncertainty, not a guess. The annunciator ring
   on IMMINENT is the only motion on the board. */

interface LeadTimeGaugeProps {
  band: LeadTimeBand;
  basis?: string | null;
  size?: 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

// Tape geometry: 90 minutes mapped linearly onto TAPE_W px, breach stop after.
const TAPE_W = 228;
const STOP_W = 8;
const VIEW_W = TAPE_W + STOP_W + 4;
const minToX = (min: number) => ((90 - Math.min(min, 90)) / 90) * TAPE_W;

const ZONES: { band: Exclude<LeadTimeBand, 'UNKNOWN'>; from: number; to: number; color: string }[] = [
  { band: 'WATCH', from: 90, to: 45, color: 'var(--watch)' },
  { band: 'NEAR', from: 45, to: 15, color: 'var(--near)' },
  { band: 'IMMINENT', from: 15, to: 0, color: 'var(--imminent)' },
];

const BAND_META: Record<LeadTimeBand, { label: string; mid: number | null; color: string }> = {
  WATCH: { label: 'WATCH · T−45+ MIN', mid: 67.5, color: 'var(--watch)' },
  NEAR: { label: 'NEAR · T−15–45 MIN', mid: 30, color: 'var(--near)' },
  IMMINENT: { label: 'IMMINENT · T−<15 MIN', mid: 7.5, color: 'var(--imminent)' },
  UNKNOWN: { label: 'UNKNOWN · INSUFFICIENT SIGNAL', mid: null, color: 'var(--unknown)' },
};

export function LeadTimeGauge({
  band,
  basis,
  size = 'sm',
  showLabel = true,
  className,
}: LeadTimeGaugeProps) {
  const meta = BAND_META[band];
  const unknown = band === 'UNKNOWN';
  const tapeY = size === 'md' ? 4 : 2;
  const tapeH = size === 'md' ? 8 : 6;
  const viewH = size === 'md' ? 30 : 16;
  const markerX = meta.mid === null ? 10 : minToX(meta.mid);
  const markerY = tapeY + tapeH / 2;

  return (
    <div className={clsx('flex flex-col gap-1 min-w-0', className)}>
      {showLabel && (
        <div className="flex items-baseline justify-between gap-2 font-mono">
          <span
            className="text-micro font-semibold tracking-[0.08em] whitespace-nowrap"
            style={{ color: meta.color }}
          >
            {meta.label}
          </span>
          {size === 'md' && basis && (
            <span className="text-micro text-ink-dim truncate" title={basis}>
              {basis}
            </span>
          )}
        </div>
      )}
      <svg
        viewBox={`0 0 ${VIEW_W} ${viewH}`}
        className="w-full"
        style={{ height: viewH }}
        role="img"
        aria-label={`Lead time ${meta.label}${basis ? `, basis: ${basis}` : ''}`}
      >
        {ZONES.map((z) => (
          <rect
            key={z.band}
            x={minToX(z.from)}
            y={tapeY}
            width={minToX(z.to) - minToX(z.from) - 1.5}
            height={tapeH}
            rx="1.5"
            fill={unknown ? 'var(--unknown)' : z.color}
            opacity={unknown ? 0.1 : z.band === band ? 0.42 : 0.14}
          />
        ))}
        {/* breach end-stop */}
        <rect
          x={TAPE_W + 2}
          y={tapeY - 2}
          width={STOP_W}
          height={tapeH + 4}
          rx="1"
          fill="var(--imminent)"
          opacity={unknown ? 0.25 : 0.9}
        />
        {/* band-extent underline (the forecast is the whole band) */}
        {!unknown && (
          <rect
            x={minToX(ZONES.find((z) => z.band === band)!.from)}
            y={tapeY + tapeH + 1.5}
            width={
              minToX(ZONES.find((z) => z.band === band)!.to) -
              minToX(ZONES.find((z) => z.band === band)!.from) -
              1.5
            }
            height="2"
            fill={meta.color}
            opacity="0.6"
          />
        )}
        {/* graduation ticks at 90/45/15/0 */}
        {size === 'md' &&
          [90, 45, 15, 0].map((m) => (
            <g key={m}>
              <line
                x1={minToX(m)}
                y1={tapeY + tapeH + 2}
                x2={minToX(m)}
                y2={tapeY + tapeH + 7}
                stroke="var(--line)"
                strokeWidth="1"
              />
              <text
                x={minToX(m)}
                y={viewH - 1}
                textAnchor={m === 90 ? 'start' : m === 0 ? 'end' : 'middle'}
                fill="var(--ink-dim)"
                fontSize="7"
                fontFamily="IBM Plex Mono, monospace"
              >
                {m}
              </text>
            </g>
          ))}
        {/* marker */}
        {unknown ? (
          <circle
            cx={markerX}
            cy={markerY}
            r={tapeH / 2 + 1}
            fill="none"
            stroke="var(--ink-dim)"
            strokeWidth="1.6"
          />
        ) : (
          <g>
            {band === 'IMMINENT' && (
              <circle
                cx={markerX}
                cy={markerY}
                r={tapeH / 2 + 4}
                fill="none"
                stroke="var(--imminent)"
                strokeWidth="1.4"
                className="animate-annunciator"
              />
            )}
            <circle cx={markerX} cy={markerY} r={tapeH / 2 + 1} fill={meta.color} />
          </g>
        )}
      </svg>
    </div>
  );
}
