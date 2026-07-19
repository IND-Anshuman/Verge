/**
 * Live Ops stage — persistent Board presence (design_plan §6.1).
 * Vision still + radio transcript rail. Never returns null; empty is labeled.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Radio, Camera, BookMarked } from 'lucide-react';
import { useAuthStore } from '@/stores/auth';
import { useFindingsStore } from '@/stores/findings';
import { BAND_SEVERITY } from '@/types';
import {
  displayableFrameSrc,
  fetchProactiveLessons,
  fetchVisionEvents,
  fetchVoiceEvents,
  type LessonCardRow,
  type VisionDetectionRow,
  type VoiceEventRow,
} from '@/api/liveOps';
import clsx from 'clsx';

const RADIO_ROLES = new Set(['Safety_Engineer', 'administrator']);

export function LiveOpsStage({ className }: { className?: string }) {
  const user = useAuthStore((s) => s.user);
  const roles = user?.roles ?? [];
  const radioAllowed = !user || roles.some((r) => RADIO_ROLES.has(r));

  const findings = useFindingsStore((s) => s.findings);
  const focusFinding = useMemo(
    () =>
      [...findings]
        .filter((f) => f.state !== 'closed' && f.state !== 'resolved')
        .sort((a, b) => BAND_SEVERITY[a.leadTimeBand] - BAND_SEVERITY[b.leadTimeBand])[0],
    [findings],
  );
  const focusZone = focusFinding?.zoneId;

  const [radio, setRadio] = useState<VoiceEventRow[]>([]);
  const [vision, setVision] = useState<VisionDetectionRow[]>([]);
  const [lesson, setLesson] = useState<LessonCardRow | null>(null);
  const [voiceErr, setVoiceErr] = useState<string | null>(null);
  const [visionErr, setVisionErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (radioAllowed) {
        try {
          const events = await fetchVoiceEvents(10);
          if (!cancelled) {
            setRadio(events);
            setVoiceErr(null);
          }
        } catch {
          if (!cancelled) {
            setRadio([]);
            setVoiceErr('radio feed offline');
          }
        }
      } else {
        setRadio([]);
        setVoiceErr(null);
      }

      try {
        const dets = await fetchVisionEvents(10);
        if (!cancelled) {
          setVision(dets);
          setVisionErr(null);
        }
      } catch {
        if (!cancelled) {
          setVision([]);
          setVisionErr('vision feed offline');
        }
      }

      if (focusZone) {
        try {
          const cards = await fetchProactiveLessons(focusZone);
          if (!cancelled) setLesson(cards[0] ?? null);
        } catch {
          if (!cancelled) setLesson(null);
        }
      } else if (!cancelled) {
        setLesson(null);
      }
    };
    void load();
    const id = setInterval(() => void load(), 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [radioAllowed, focusZone]);

  const latestWithFrame = vision.find((v) => displayableFrameSrc(v.frameUri));
  const latestVision = latestWithFrame ?? vision[0] ?? null;
  const frameSrc = displayableFrameSrc(latestVision?.frameUri);

  return (
    <section
      className={clsx(
        'border border-line rounded-md bg-panel overflow-hidden shrink-0 flex flex-col',
        className,
      )}
      aria-label="Live Ops — radio and vision"
    >
      <div className="h-8 px-3 border-b border-line flex items-center justify-between gap-3">
        <span className="text-micro font-mono uppercase tracking-[0.12em] text-ink-dim">
          Live Ops
        </span>
        <div className="flex items-center gap-3 text-micro font-mono text-ink-dim tabular-nums">
          <span>Radio · {radioAllowed ? radio.length : '—'}</span>
          <span>Vision · {vision.length}</span>
          {lesson && (
            <span className="text-watch truncate max-w-[160px]" title={lesson.title}>
              Lesson · {lesson.lessonId}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] min-h-[168px] max-h-[220px]">
        {/* Vision pane */}
        <div className="border-b md:border-b-0 md:border-r border-line flex flex-col min-h-0 bg-bg/40">
          <div className="px-3 py-1.5 flex items-center gap-1.5 text-micro font-mono uppercase tracking-[0.08em] text-ink-dim shrink-0">
            <Camera className="h-3 w-3" />
            Vision
            {latestVision && (
              <span className="normal-case tracking-normal text-ink-dim/80 ml-1 truncate">
                {latestVision.cameraId} · {latestVision.zoneId || '—'} · {latestVision.label}
              </span>
            )}
          </div>
          <div className="flex-1 min-h-0 flex items-center justify-center p-2 relative">
            {visionErr ? (
              <span className="text-xs text-ink-dim font-mono px-3 text-center">{visionErr}</span>
            ) : frameSrc ? (
              <img
                src={frameSrc}
                alt={`Detection ${latestVision?.label ?? ''} on ${latestVision?.cameraId ?? ''}`}
                className="max-h-full max-w-full object-contain border border-line bg-ink/5"
              />
            ) : latestVision ? (
              <div className="flex flex-col items-center gap-1 px-4 text-center">
                <span className="text-xs text-ink font-medium">
                  {latestVision.label}
                  <span className="font-mono text-ink-dim ml-1.5">
                    {(latestVision.confidence * 100).toFixed(0)}%
                  </span>
                </span>
                <span className="text-micro font-mono text-ink-dim">
                  {latestVision.frameUri?.startsWith('s3://')
                    ? 'Frame in object store — no browser preview path'
                    : 'No frame still for this detection'}
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-1 px-4 text-center">
                <span className="text-xs text-ink-dim">No recent vision events</span>
                <span className="text-micro font-mono text-ink-dim/70">
                  Frames appear after detect-frame ingest
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Radio rail */}
        <div className="flex flex-col min-h-0 min-w-0">
          <div className="px-3 py-1.5 flex items-center gap-1.5 text-micro font-mono uppercase tracking-[0.08em] text-ink-dim shrink-0">
            <Radio className="h-3 w-3" />
            Radio
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto scrollbar px-3 pb-2">
            {!radioAllowed ? (
              <span className="text-xs text-ink-dim">Radio restricted to Safety Engineer</span>
            ) : voiceErr ? (
              <span className="text-xs text-ink-dim font-mono">{voiceErr}</span>
            ) : radio.length === 0 ? (
              <div className="flex flex-col gap-1 py-2">
                <span className="text-xs text-ink-dim">No recent radio events</span>
                <span className="text-micro font-mono text-ink-dim/70">
                  Transcripts stream here when voice events arrive
                </span>
              </div>
            ) : (
              <ul className="flex flex-col gap-2 py-1">
                {radio.slice(0, 6).map((ev) => (
                  <li key={ev.eventId} className="text-xs leading-snug border-b border-line/50 pb-1.5 last:border-0">
                    <span className="font-mono text-ink-dim mr-1.5">
                      {ev.zoneId || '—'}
                    </span>
                    <span className="text-ink">{ev.transcript || '(empty transcript)'}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Footer chips — deep-link when a focus finding exists */}
      <div className="h-7 px-3 border-t border-line flex items-center gap-3 text-micro font-mono text-ink-dim bg-panel-2/40">
        {focusFinding ? (
          <Link
            to={`/findings/${focusFinding.findingId}`}
            className="hover:text-ink transition-colors truncate"
          >
            Focus · {focusFinding.findingId} · {focusFinding.leadTimeBand} · {focusFinding.zoneId}
          </Link>
        ) : (
          <span>No open finding to focus</span>
        )}
        {lesson && (
          <span className="flex items-center gap-1 truncate ml-auto text-watch">
            <BookMarked className="h-3 w-3 shrink-0" />
            {lesson.title}
          </span>
        )}
      </div>
    </section>
  );
}
