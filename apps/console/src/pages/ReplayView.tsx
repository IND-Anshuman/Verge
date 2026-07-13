import { useState, useEffect, useMemo } from 'react';
import { Card, Badge, Button } from '@/components/atoms';
import { listReplays, getReplay } from '@/api';
import type { ReplaySummary, ReplayTimeline } from '@/api';
import { Play, Pause, RotateCcw, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';

/* Historical incident replay over the REAL eval fixtures (spec §10).
   Events, telemetry, the Verge alert marker, and the breach marker all come
   from /api/replays — the same data the eval harness scores. Nothing is
   simulated in the frontend. */

const SERIES_COLORS = ['#F0A83E', '#4FA3C7', '#43C989', '#B48EDE', '#FF8FA3'];

function fmtClock(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

function bandColor(band: string | null): string {
  switch (band) {
    case 'IMMINENT':
      return 'var(--imminent)';
    case 'NEAR':
      return 'var(--near)';
    case 'WATCH':
      return 'var(--watch)';
    default:
      return 'var(--unknown)';
  }
}

/** Numeric series per sensor from real reading events, normalized to % of
    that sensor's peak so multi-unit signals share one axis (labeled as such). */
function buildSeries(timeline: ReplayTimeline) {
  const bySensor = new Map<string, { time: number; raw: number }[]>();
  for (const e of timeline.events) {
    if (e.type !== 'reading') continue;
    const raw = parseFloat(e.value);
    if (!Number.isFinite(raw)) continue;
    if (!bySensor.has(e.sensor)) bySensor.set(e.sensor, []);
    bySensor.get(e.sensor)!.push({ time: e.time, raw });
  }
  const sensors = [...bySensor.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 4)
    .map(([sensor]) => sensor);

  const points = new Map<number, Record<string, number>>();
  for (const sensor of sensors) {
    const samples = bySensor.get(sensor)!;
    const peak = Math.max(...samples.map((s) => Math.abs(s.raw))) || 1;
    for (const { time, raw } of samples) {
      if (!points.has(time)) points.set(time, { time });
      points.get(time)![sensor] = Math.round((raw / peak) * 1000) / 10;
    }
  }
  const data = [...points.values()].sort((a, b) => a.time - b.time);
  return { sensors, data };
}

export default function ReplayView() {
  const [replays, setReplays] = useState<ReplaySummary[]>([]);
  const [timeline, setTimeline] = useState<ReplayTimeline | null>(null);
  const [selectedId, setSelectedId] = useState<string>('');
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<0.5 | 1 | 2 | 4>(1);

  // Load the replay catalog once
  useEffect(() => {
    const ctrl = new AbortController();
    listReplays(ctrl.signal)
      .then((list) => {
        setReplays(list);
        if (list.length > 0) setSelectedId(list[0].incidentId);
        setLoadError(null);
      })
      .catch(() => setLoadError('Replay catalog unavailable — start the API with `make dev`.'));
    return () => ctrl.abort();
  }, []);

  // Load the selected incident's full timeline
  useEffect(() => {
    if (!selectedId) return;
    const ctrl = new AbortController();
    setLoading(true);
    setIsPlaying(false);
    setCurrentTime(0);
    getReplay(selectedId, ctrl.signal)
      .then((t) => {
        setTimeline(t);
        setLoadError(null);
      })
      .catch(() => setLoadError(`Failed to load replay ${selectedId}.`))
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [selectedId]);

  // Playback loop — a full pass takes ~60s at 1x regardless of incident length
  useEffect(() => {
    if (!isPlaying || !timeline) return;
    const step = (timeline.duration / 600) * speed;
    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        if (prev >= timeline.duration) {
          setIsPlaying(false);
          return timeline.duration;
        }
        return Math.min(prev + step, timeline.duration);
      });
    }, 100);
    return () => clearInterval(interval);
  }, [isPlaying, speed, timeline]);

  const chart = useMemo(() => (timeline ? buildSeries(timeline) : { sensors: [], data: [] }), [timeline]);
  const visibleChartData = useMemo(
    () => chart.data.filter((d) => (d.time as number) <= currentTime),
    [chart.data, currentTime]
  );

  const vergeAlertTime = useMemo(() => {
    const e = timeline?.events.find((ev) => ev.type === 'verge-alert');
    return e ? e.time : null;
  }, [timeline]);
  const breachTime = useMemo(() => {
    const e = timeline?.events.find((ev) => ev.type === 'breach');
    return e ? e.time : null;
  }, [timeline]);

  const activeEvents = useMemo(
    () => (timeline ? timeline.events.filter((e) => e.time <= currentTime) : []),
    [timeline, currentTime]
  );

  const duration = timeline?.duration ?? 0;

  return (
    <div className="flex flex-col gap-6 p-4 h-[calc(100vh-80px)] overflow-y-auto scrollbar select-text text-ink font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-line pb-3 select-none shrink-0">
        <div className="flex flex-col gap-1 min-w-0">
          <h1 className="text-lg font-bold uppercase font-mono tracking-wide">Incident Replay</h1>
          <p className="text-xs text-ink-dim font-mono">
            Real incident streams scored by the eval harness — the alert marker is Verge&apos;s actual output, not a script.
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-panel-2 p-0.5 rounded border border-line shrink-0 max-w-full">
          <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold shrink-0">Incident:</span>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="h-7 px-2 rounded border border-line text-xs bg-panel text-ink focus:outline-none min-w-0 flex-1"
            disabled={replays.length === 0}
          >
            {replays.map((r) => (
              <option key={r.incidentId} value={r.incidentId}>
                {r.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadError && (
        <div className="flex items-center gap-2 bg-imminent/10 border border-imminent/30 text-imminent text-xs font-mono p-3 rounded">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {loadError}
        </div>
      )}

      {timeline && (
        <>
          {/* Verdict strip — the eval-proven numbers for this incident */}
          <div className="flex flex-wrap items-center gap-3 select-none shrink-0">
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded border font-mono text-xs font-bold"
              style={{
                color: bandColor(timeline.band),
                borderColor: 'color-mix(in srgb, currentColor 35%, transparent)',
                backgroundColor: 'color-mix(in srgb, currentColor 10%, transparent)',
              }}
            >
              VERGE ALERT{' '}
              {timeline.leadMin !== null ? `T−${timeline.leadMin} MIN` : '—'} · {timeline.band ?? 'NONE'}
            </div>
            <div className="px-3 py-1.5 rounded border border-line bg-panel font-mono text-xs text-ink-dim">
              ZONE <span className="text-ink font-bold">{timeline.zoneId}</span>
            </div>
            <div className="px-3 py-1.5 rounded border border-line bg-panel font-mono text-xs text-ink-dim">
              STREAM <span className="text-ink font-bold tabular-nums">{fmtClock(duration)}</span>
            </div>
            <div className="px-3 py-1.5 rounded border border-line bg-panel font-mono text-xs text-ink-dim truncate max-w-[380px]" title={timeline.description}>
              {timeline.description || timeline.name}
            </div>
          </div>

          {/* Replay controller */}
          <Card className="p-4 border-line bg-panel-2/30 flex flex-col gap-4 select-none shrink-0">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-col gap-0.5 font-mono text-xs">
                <span className="text-micro text-ink-dim uppercase">Elapsed stream time</span>
                <div className="text-base font-bold text-ink tabular-nums">
                  {fmtClock(currentTime)} / {fmtClock(duration)}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCurrentTime((p) => Math.max(p - duration / 20, 0))}
                  icon={<ChevronLeft className="h-4 w-4 text-ink-dim" />}
                  aria-label="Step backward"
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                  icon={isPlaying ? <Pause className="h-4 w-4 text-bg" /> : <Play className="h-4 w-4 text-bg" />}
                  className="h-8 w-16"
                  aria-label={isPlaying ? 'Pause' : 'Play'}
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCurrentTime((p) => Math.min(p + duration / 20, duration))}
                  icon={<ChevronRight className="h-4 w-4 text-ink-dim" />}
                  aria-label="Step forward"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentTime(0);
                  }}
                  icon={<RotateCcw className="h-3.5 w-3.5 text-ink-dim" />}
                  aria-label="Reset"
                />
              </div>

              <div className="flex items-center gap-1.5 bg-panel p-0.5 rounded border border-line">
                <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold">Speed:</span>
                {([0.5, 1, 2, 4] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setSpeed(s)}
                    className={`h-6 px-2 text-micro font-mono font-bold rounded-sm cursor-pointer ${
                      speed === s ? 'bg-panel-2 text-ink border border-line' : 'text-ink-dim hover:text-ink'
                    }`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>

            {/* Scrubber with real alert/breach markers */}
            <div className="relative w-full pt-3">
              {vergeAlertTime !== null && duration > 0 && (
                <span
                  className="absolute top-0 h-2.5 w-2.5 rounded-full -translate-x-1/2"
                  style={{ left: `${(vergeAlertTime / duration) * 100}%`, backgroundColor: bandColor(timeline.band) }}
                  title={`Verge alert at ${fmtClock(vergeAlertTime)}`}
                />
              )}
              {breachTime !== null && duration > 0 && (
                <span
                  className="absolute top-0 h-2.5 w-2.5 -translate-x-1/2 rounded-sm bg-imminent"
                  title={`Threshold breach at ${fmtClock(breachTime)}`}
                  style={{ left: `${(breachTime / duration) * 100}%` }}
                />
              )}
              <input
                type="range"
                min={0}
                max={Math.max(duration, 1)}
                value={currentTime}
                onChange={(e) => {
                  setCurrentTime(parseFloat(e.target.value));
                  setIsPlaying(false);
                }}
                className="w-full h-1.5 bg-bg rounded-lg appearance-none cursor-pointer accent-accent border border-line"
                aria-label="Timeline scrubber"
              />
            </div>
          </Card>

          {/* Grid: event log + real telemetry */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-3">
              <span className="text-xs font-mono font-bold text-ink-dim uppercase select-none">
                Incident event stream ({activeEvents.length}/{timeline.events.length})
              </span>
              <div className="flex flex-col gap-2.5 h-72 overflow-y-auto scrollbar pr-1">
                {activeEvents.map((e, idx) => (
                  <div
                    key={idx}
                    className={`p-3 border rounded flex justify-between items-center text-xs font-mono ${
                      e.type === 'breach'
                        ? 'border-imminent/50 bg-imminent/10 text-imminent'
                        : e.type === 'verge-alert'
                          ? 'border-accent/50 bg-accent/10 text-accent'
                          : 'border-line bg-panel text-ink-dim'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5 truncate pr-4">
                      <span className="text-micro uppercase opacity-70">[{e.sensor}]</span>
                      <span className={`font-bold leading-normal truncate ${e.type === 'reading' || e.type === 'permit' || e.type === 'shift' ? 'text-ink' : ''}`}>
                        {e.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {e.value && (
                        <Badge variant="generic" color={e.type === 'breach' ? 'imminent' : 'near'} className="py-0.5 scale-90">
                          {e.value}
                        </Badge>
                      )}
                      <span className="text-micro font-bold tabular-nums">+{fmtClock(e.time)}</span>
                    </div>
                  </div>
                ))}
                {activeEvents.length === 0 && (
                  <div className="flex-1 flex items-center justify-center border border-dashed border-line rounded select-none">
                    <span className="text-xs text-ink-dim font-mono uppercase">
                      {loading ? 'Loading incident stream…' : 'Press play to run the recorded stream'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-3 select-none">
              <span className="text-xs font-mono font-bold text-ink-dim uppercase">
                Recorded telemetry · % of sensor peak
              </span>
              <div className="h-72 border border-line bg-panel p-3 rounded-md font-mono text-micro">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={visibleChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid stroke="#262E39" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="time"
                      type="number"
                      domain={[0, duration]}
                      tickFormatter={(t: number) => fmtClock(t)}
                      stroke="#8C96A3"
                      tickLine={false}
                    />
                    <YAxis stroke="#8C96A3" tickLine={false} domain={[0, 100]} />
                    <Tooltip
                      labelFormatter={(t) => fmtClock(Number(t))}
                      contentStyle={{ backgroundColor: '#12161D', borderColor: '#262E39', color: '#E8EDF4' }}
                    />
                    {vergeAlertTime !== null && (
                      <ReferenceLine
                        x={vergeAlertTime}
                        stroke={bandColor(timeline.band)}
                        strokeDasharray="4 3"
                        label={{ value: 'VERGE', fill: bandColor(timeline.band), fontSize: 9, position: 'insideTopLeft' }}
                      />
                    )}
                    {breachTime !== null && (
                      <ReferenceLine
                        x={breachTime}
                        stroke="#FF5C5C"
                        label={{ value: 'BREACH', fill: '#FF5C5C', fontSize: 9, position: 'insideTopRight' }}
                      />
                    )}
                    {chart.sensors.map((sensor, i) => (
                      <Line
                        key={sensor}
                        type="monotone"
                        dataKey={sensor}
                        stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                        strokeWidth={1.6}
                        dot={false}
                        isAnimationActive={false}
                        connectNulls
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}

      {!timeline && !loadError && (
        <div className="flex-1 flex items-center justify-center border border-dashed border-line rounded select-none">
          <span className="text-xs text-ink-dim font-mono uppercase">Loading replay catalog…</span>
        </div>
      )}
    </div>
  );
}
