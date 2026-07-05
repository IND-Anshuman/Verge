import { useState, useEffect } from 'react';
import { Card, Badge, Button } from '@/components/atoms';
import { Play, Pause, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface Scenario {
  id: string;
  name: string;
  description: string;
  duration: number; // in seconds
  events: Array<{ time: number; type: string; title: string; sensor: string; value: string }>;
}

const SCENARIOS: Scenario[] = [
  {
    id: 'vizag-2025',
    name: 'Visakhapatnam 2025-01 Gas Ingress',
    description: 'Thermal runaway in secondary reformer feed line leading to critical methane escape.',
    duration: 300,
    events: [
      { time: 10, type: 'sensor_rise', title: 'Temperature anomaly detected', sensor: 'TEMP-0411', value: '48°C' },
      { time: 60, type: 'sensor_high', title: 'Bearing thermal limit exceeded', sensor: 'TEMP-0411', value: '82°C' },
      { time: 120, type: 'gas_alert', title: 'Methane ingress trigger (B1 RoR)', sensor: 'CH4-0412', value: '1.2% LEL' },
      { time: 240, type: 'breach', title: 'CONVERGENCE BREACH EVENT', sensor: 'ALL', value: 'CRITICAL LEL' },
    ],
  },
  {
    id: 'jaipur-2009',
    name: 'Jaipur IOC 2009 Terminal Leak',
    description: 'Gasoline pipeline transfer valve isolation failure resulting in massive vapor cloud accumulation.',
    duration: 600,
    events: [
      { time: 30, type: 'flow_anomaly', title: 'Line pressure drop', sensor: 'PRES-1102', value: '0.8 bar' },
      { time: 180, type: 'leak_detected', title: 'Vapor cloud detection (B2 Multi)', sensor: 'HC-1114', value: '150 ppm' },
      { time: 540, type: 'explosion', title: 'Ignition event logged', sensor: 'ALL', value: 'CRITICAL FIRE' },
    ],
  },
];

export default function ReplayView() {
  const [selectedScenario, setSelectedScenario] = useState<Scenario>(SCENARIOS[0]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<0.5 | 1 | 2 | 4>(1);

  // Playback timer loop
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= selectedScenario.duration) {
            setIsPlaying(false);
            return selectedScenario.duration;
          }
          return prev + 1;
        });
      }, 1000 / speed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, speed, selectedScenario]);

  const handlePlayPause = () => setIsPlaying(!isPlaying);
  const handleReset = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };
  const handleStepForward = () => setCurrentTime((prev) => Math.min(prev + 10, selectedScenario.duration));
  const handleStepBackward = () => setCurrentTime((prev) => Math.max(prev - 10, 0));

  const activeEvents = selectedScenario.events.filter((e) => e.time <= currentTime);

  // Recharts simulation data
  const chartData = Array.from({ length: 20 }, (_, i) => {
    const timeSecs = Math.round((selectedScenario.duration / 20) * i);
    const hasEvent = selectedScenario.events.some((e) => e.time <= timeSecs);
    return {
      time: `${timeSecs}s`,
      Methane: hasEvent ? 0.2 + (timeSecs / selectedScenario.duration) * 1.8 : 0.2,
      Temp: hasEvent ? 45 + (timeSecs / selectedScenario.duration) * 45 : 45,
    };
  });

  return (
    <div className="flex flex-col gap-6 p-4 h-[calc(100vh-80px)] overflow-y-auto scrollbar select-text text-ink font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line pb-3 select-none shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="text-lg font-bold uppercase font-mono tracking-wide">
            Historical Incident Replay & Playback
          </h1>
          <p className="text-xs text-ink-dim font-mono">
            Load historical terminal refinery incidents to verify and audit detection logic models.
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-panel-2 p-0.5 rounded border border-line">
          <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold">
            SCENARIO:
          </span>
          <select
            value={selectedScenario.id}
            onChange={(e) => {
              const sc = SCENARIOS.find((s) => s.id === e.target.value);
              if (sc) {
                setSelectedScenario(sc);
                setCurrentTime(0);
                setIsPlaying(false);
              }
            }}
            className="h-7 px-2 rounded border border-line text-xs bg-panel text-ink focus:outline-none"
          >
            {SCENARIOS.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Replay controller dashboard */}
      <Card className="p-4 border-line bg-panel-2/30 flex flex-col gap-4 select-none shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Timeline playback status */}
          <div className="flex flex-col gap-0.5 font-mono text-xs">
            <span className="text-micro text-ink-dim uppercase">Elapsed Playback Time</span>
            <div className="text-base font-bold text-ink tabular-nums">
              {currentTime}s / {selectedScenario.duration}s
            </div>
          </div>

          {/* Timeline controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleStepBackward}
              icon={<ChevronLeft className="h-4 w-4 text-ink-dim" />}
            />
            <Button
              variant="primary"
              size="sm"
              onClick={handlePlayPause}
              icon={isPlaying ? <Pause className="h-4 w-4 text-bg" /> : <Play className="h-4 w-4 text-bg" />}
              className="h-8 w-16"
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={handleStepForward}
              icon={<ChevronRight className="h-4 w-4 text-ink-dim" />}
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={handleReset}
              icon={<RotateCcw className="h-3.5 w-3.5 text-ink-dim" />}
            />
          </div>

          {/* Speed settings */}
          <div className="flex items-center gap-1.5 bg-panel p-0.5 rounded border border-line">
            <span className="text-micro font-mono text-ink-dim px-2 uppercase font-bold">
              SPEED:
            </span>
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

        {/* Timeline Scrubber */}
        <div className="flex flex-col gap-1 w-full">
          <input
            type="range"
            min={0}
            max={selectedScenario.duration}
            value={currentTime}
            onChange={(e) => {
              setCurrentTime(parseInt(e.target.value));
              setIsPlaying(false);
            }}
            className="w-full h-1.5 bg-bg rounded-lg appearance-none cursor-pointer accent-accent border border-line"
          />
        </div>
      </Card>

      {/* Grid: Scenario details and simulation telemetry */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Scenario description & logs */}
        <div className="flex flex-col gap-3">
          <span className="text-xs font-mono font-bold text-ink-dim uppercase select-none">
            Incident Log Sequence
          </span>
          <div className="flex flex-col gap-2.5 h-64 overflow-y-auto scrollbar pr-1">
            {activeEvents.map((e, idx) => (
              <div
                key={idx}
                className="p-3 border border-line bg-panel rounded flex justify-between items-center text-xs font-mono text-ink-dim"
              >
                <div className="flex flex-col gap-0.5 truncate pr-4">
                  <span className="text-micro text-ink-dim uppercase">[{e.sensor}]</span>
                  <span className="text-ink font-bold leading-normal truncate">{e.title}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="generic" color="near" className="py-0.5 scale-90">
                    {e.value}
                  </Badge>
                  <span className="text-micro font-bold text-ink tabular-nums">+{e.time}s</span>
                </div>
              </div>
            ))}

            {activeEvents.length === 0 && (
              <div className="flex-1 flex items-center justify-center border border-dashed border-line rounded select-none">
                <span className="text-xs text-ink-dim font-mono uppercase">Start playback to trigger events</span>
              </div>
            )}
          </div>
        </div>

        {/* Simulation telemetry charts */}
        <div className="flex flex-col gap-3 select-none">
          <span className="text-xs font-mono font-bold text-ink-dim uppercase">
            Convergence Telemetry Simulation
          </span>
          <div className="h-64 border border-line bg-panel p-3 rounded-md font-mono text-micro">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid stroke="#2a323d" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#8b949e" tickLine={false} />
                <YAxis stroke="#8b949e" tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#161b22',
                    borderColor: '#2a323d',
                    color: '#e6edf3',
                  }}
                />
                <Area type="monotone" dataKey="Methane" stroke="#f06363" fill="rgba(240, 99, 99, 0.1)" />
                <Area type="monotone" dataKey="Temp" stroke="#e8a33d" fill="rgba(232, 163, 61, 0.1)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
