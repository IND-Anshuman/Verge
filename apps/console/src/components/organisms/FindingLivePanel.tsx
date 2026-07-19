/**
 * Finding Live block — telemetry, permits, zone vision still, recent radio (§6.2).
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Camera, Radio, Network } from 'lucide-react';
import type { RiskFinding } from '@/types';
import { getFindingTelemetry, type FindingTelemetry } from '@/api/telemetry';
import { getPermits, type PermitWire } from '@/api/permits';
import {
  displayableFrameSrc,
  fetchVisionEvents,
  fetchVoiceEvents,
  type VisionDetectionRow,
  type VoiceEventRow,
} from '@/api/liveOps';

export function FindingLivePanel({ finding }: { finding: RiskFinding }) {
  const [telemetry, setTelemetry] = useState<FindingTelemetry | null>(null);
  const [telemetryErr, setTelemetryErr] = useState<string | null>(null);
  const [permits, setPermits] = useState<PermitWire[]>([]);
  const [vision, setVision] = useState<VisionDetectionRow | null>(null);
  const [radio, setRadio] = useState<VoiceEventRow[]>([]);

  useEffect(() => {
    let cancelled = false;
    getFindingTelemetry(finding.findingId)
      .then((t) => {
        if (!cancelled) {
          setTelemetry(t);
          setTelemetryErr(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTelemetry(null);
          setTelemetryErr('Telemetry unavailable');
        }
      });

    getPermits()
      .then((all) => {
        if (cancelled) return;
        setPermits(all.filter((p) => p.zoneId === finding.zoneId));
      })
      .catch(() => {
        if (!cancelled) setPermits([]);
      });

    Promise.allSettled([fetchVisionEvents(20), fetchVoiceEvents(12)]).then(
      ([vRes, rRes]) => {
        if (cancelled) return;
        if (vRes.status === 'fulfilled') {
          const zoneHits = vRes.value.filter((d) => d.zoneId === finding.zoneId);
          const withFrame = zoneHits.find((d) => displayableFrameSrc(d.frameUri));
          setVision(withFrame ?? zoneHits[0] ?? null);
        }
        if (rRes.status === 'fulfilled') {
          setRadio(
            rRes.value.filter((e) => !e.zoneId || e.zoneId === finding.zoneId).slice(0, 5),
          );
        }
      },
    );

    return () => {
      cancelled = true;
    };
  }, [finding.findingId, finding.zoneId]);

  const frameSrc = displayableFrameSrc(vision?.frameUri);
  const activePermits = permits.filter((p) => {
    const s = (p.status || '').toLowerCase();
    return s === 'active' || s === 'open' || s === 'issued' || !s;
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Vision still */}
        <div className="border border-line rounded-md bg-panel overflow-hidden flex flex-col min-h-[140px]">
          <div className="px-2.5 py-1.5 border-b border-line text-micro font-mono uppercase tracking-[0.08em] text-ink-dim flex items-center gap-1.5">
            <Camera className="h-3 w-3" />
            Zone camera
          </div>
          <div className="flex-1 flex items-center justify-center p-2 bg-bg/40 min-h-[100px]">
            {frameSrc ? (
              <img
                src={frameSrc}
                alt={vision?.label ?? 'zone frame'}
                className="max-h-36 max-w-full object-contain border border-line"
              />
            ) : vision ? (
              <span className="text-xs text-ink-dim text-center px-3 font-mono">
                {vision.cameraId} · {vision.label}
                <span className="block mt-1 text-micro">No browser-displayable frame</span>
              </span>
            ) : (
              <span className="text-xs text-ink-dim text-center px-3">
                No recent vision in {finding.zoneId}
              </span>
            )}
          </div>
        </div>

        {/* Radio */}
        <div className="border border-line rounded-md bg-panel overflow-hidden flex flex-col min-h-[140px]">
          <div className="px-2.5 py-1.5 border-b border-line text-micro font-mono uppercase tracking-[0.08em] text-ink-dim flex items-center gap-1.5">
            <Radio className="h-3 w-3" />
            Zone radio
          </div>
          <div className="flex-1 overflow-y-auto scrollbar px-2.5 py-2">
            {radio.length === 0 ? (
              <span className="text-xs text-ink-dim">No recent radio for this zone</span>
            ) : (
              <ul className="flex flex-col gap-2">
                {radio.map((ev) => (
                  <li key={ev.eventId} className="text-xs text-ink leading-snug">
                    <span className="font-mono text-ink-dim mr-1">{ev.zoneId || '—'}</span>
                    {ev.transcript}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Telemetry summary */}
      <div className="border border-line rounded-md bg-panel p-3 flex flex-col gap-2">
        <span className="text-micro font-mono uppercase tracking-[0.08em] text-ink-dim">
          Telemetry window
        </span>
        {telemetryErr ? (
          <span className="text-xs text-ink-dim font-mono">{telemetryErr}</span>
        ) : !telemetry?.series?.length ? (
          <span className="text-xs text-ink-dim">No sensor series for this finding</span>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {telemetry.series.slice(0, 6).map((s) => {
              const last = s.points[s.points.length - 1];
              return (
                <li
                  key={s.sensorId}
                  className="px-2 py-1 border border-line rounded-sm bg-bg font-mono text-micro text-ink"
                >
                  {s.sensorId}
                  {last != null && (
                    <span className="text-ink-dim ml-1.5 tabular-nums">
                      {typeof last.value === 'number' ? last.value.toFixed(2) : last.value}
                      {s.unit ? ` ${s.unit}` : ''}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Permits */}
      <div className="border border-line rounded-md bg-panel p-3 flex flex-col gap-2">
        <span className="text-micro font-mono uppercase tracking-[0.08em] text-ink-dim">
          Active permits · {finding.zoneId}
        </span>
        {activePermits.length === 0 ? (
          <span className="text-xs text-ink-dim">No active permits in this zone</span>
        ) : (
          <ul className="flex flex-col gap-1">
            {activePermits.slice(0, 6).map((p) => (
              <li key={p.permitId} className="text-xs font-mono text-ink flex gap-2">
                <span className="text-ink-dim">{p.permitId}</span>
                <span>{p.kind}</span>
                <span className="text-ink-dim">{p.status}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <Link
        to="/graph"
        className="inline-flex items-center gap-1.5 text-micro font-mono uppercase tracking-[0.08em] text-ink-dim hover:text-ink transition-colors w-fit"
      >
        <Network className="h-3 w-3" />
        Open plant graph
      </Link>
    </div>
  );
}
