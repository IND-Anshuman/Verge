import { useEffect, useMemo, useState } from 'react';
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
import { AlertCircle } from 'lucide-react';
import type { RiskFinding } from '@/types';
import { getFindingTelemetry, type FindingTelemetry } from '@/api/telemetry';

interface TemporalChartProps {
  finding: RiskFinding;
}

const SERIES_COLORS = ['#FF5C5C', '#F0A83E', '#4FA3C7', '#43C989'];

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function TemporalConvergenceChart({ finding }: TemporalChartProps) {
  const [telemetry, setTelemetry] = useState<FindingTelemetry | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadError(null);
    getFindingTelemetry(finding.findingId)
      .then((data) => {
        if (!cancelled) setTelemetry(data);
      })
      .catch(() => {
        if (!cancelled) {
          setTelemetry(null);
          setLoadError('Telemetry unavailable — start API with live readings.');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [finding.findingId]);

  const { chartData, seriesKeys, thresholds } = useMemo(() => {
    if (!telemetry?.series.length) {
      return { chartData: [], seriesKeys: [] as string[], thresholds: {} as Record<string, number> };
    }
    const keys = telemetry.series.map((s) => s.sensorId);
    const thresh: Record<string, number> = {};
    for (const s of telemetry.series) {
      if (s.threshold != null) thresh[s.sensorId] = s.threshold;
    }
    const byTime = new Map<string, Record<string, number | string>>();
    for (const s of telemetry.series) {
      for (const p of s.points) {
        const label = formatTime(p.ts);
        const row = byTime.get(label) ?? { time: label };
        row[s.sensorId] = p.value;
        byTime.set(label, row);
      }
    }
    const data = [...byTime.values()].sort((a, b) =>
      String(a.time).localeCompare(String(b.time)),
    );
    return { chartData: data, seriesKeys: keys, thresholds: thresh };
  }, [telemetry]);

  return (
    <div className="flex flex-col gap-3 w-full text-ink">
      <div className="flex items-center justify-between text-xs select-none">
        <span className="font-semibold font-mono text-ink-dim uppercase">
          Co-Convergence Timeline · {finding.zoneId}
        </span>
        <div className="flex items-center gap-3 font-mono text-micro text-ink-dim flex-wrap justify-end">
          {seriesKeys.map((key, i) => (
            <span key={key} className="flex items-center gap-1">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: SERIES_COLORS[i % SERIES_COLORS.length] }}
              />
              {key}
            </span>
          ))}
        </div>
      </div>

      {loadError && (
        <div className="bg-imminent/10 border border-imminent/20 text-imminent text-xs p-2 rounded flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {loadError}
        </div>
      )}

      {telemetry?.degraded && !loadError && (
        <p className="text-xs text-ink-dim font-mono">{telemetry.reason ?? 'No sensor series for this finding.'}</p>
      )}

      {chartData.length > 0 ? (
        <div className="h-56 w-full font-mono text-micro select-text">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid stroke="#262E39" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#8C96A3" tickLine={false} />
              <YAxis stroke="#8C96A3" tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#12161D',
                  borderColor: '#262E39',
                  color: '#E8EDF4',
                  borderRadius: '4px',
                }}
              />
              {seriesKeys.map((key, i) =>
                thresholds[key] != null ? (
                  <ReferenceLine
                    key={`${key}-thresh`}
                    y={thresholds[key]}
                    stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                    strokeDasharray="4 4"
                    strokeWidth={1}
                  />
                ) : null,
              )}
              {seriesKeys.map((key, i) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        !loadError && (
          <div className="h-56 flex items-center justify-center border border-line bg-panel-2/30 rounded text-xs text-ink-dim font-mono uppercase">
            Loading telemetry…
          </div>
        )
      )}

      {chartData.length > 0 && (
        <div className="sr-only">
          <table>
            <caption>Sensor convergence telemetry for {finding.findingId}</caption>
            <thead>
              <tr>
                <th>Time</th>
                {seriesKeys.map((k) => (
                  <th key={k}>{k}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {chartData.map((row, idx) => (
                <tr key={idx}>
                  <td>{row.time as string}</td>
                  {seriesKeys.map((k) => (
                    <td key={k}>{row[k] as number}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
