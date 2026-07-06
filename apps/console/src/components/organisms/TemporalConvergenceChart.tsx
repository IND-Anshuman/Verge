import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import type { RiskFinding } from '@/types';

interface TemporalChartProps {
  finding: RiskFinding;
}

export function TemporalConvergenceChart({ finding }: TemporalChartProps) {
  // Generate mock time-series data for traces based on the finding's zone and lineage
  // Traces: Sensor A (CH4 gas level), Sensor B (Bearing temperature), etc.
  const chartData = useMemo(() => {
    const data = [];
    const baseTime = new Date(finding.createdAt).getTime();

    // Generate 10 data points leading up to convergence (at index 7) and forecasted breach
    for (let i = 0; i < 12; i++) {
      const ts = new Date(baseTime - (10 - i) * 60000).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
      data.push({
        time: ts,
        methane: i < 8 ? 0.2 + i * 0.15 : i === 8 ? 1.5 : 1.9, // threshold: 1.0% LEL
        temp: i < 8 ? 45 + i * 4 : i === 8 ? 82 : 88,          // threshold: 80C
        limitMethane: 1.0,
        limitTemp: 80,
      });
    }
    return data;
  }, [finding]);

  return (
    <div className="flex flex-col gap-3 w-full text-ink">
      <div className="flex items-center justify-between text-xs select-none">
        <span className="font-semibold font-mono text-ink-dim uppercase">
          Co-Convergence Timeline
        </span>
        <div className="flex items-center gap-3 font-mono text-micro text-ink-dim">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-imminent" />
            CH4 GAS (% LEL)
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            BEARING TEMP (°C)
          </span>
        </div>
      </div>

      {/* Recharts Container */}
      <div className="h-56 w-full font-mono text-micro select-text">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid stroke="#2a323d" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#8b949e" tickLine={false} />
            <YAxis stroke="#8b949e" tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#161b22',
                borderColor: '#2a323d',
                color: '#e6edf3',
                borderRadius: '4px',
              }}
            />
            {/* Shaded Forecast Breach Window (Indexes 8 to 11) */}
            <ReferenceArea
              x1={chartData[8]?.time}
              x2={chartData[11]?.time}
              fill="rgba(240, 99, 99, 0.08)"
              label={{ value: 'FORECAST BREACH', fill: '#f06363', position: 'insideTopRight', fontSize: 9 }}
            />
            {/* Threshold reference lines */}
            <ReferenceLine y={1.0} stroke="#f06363" strokeDasharray="4 4" strokeWidth={1} />
            {/* Vertical convergence moment indicator */}
            <ReferenceLine
              x={chartData[7]?.time}
              stroke="#e8a33d"
              strokeWidth={1.5}
              label={{ value: 'CONVERGENCE EVENT', fill: '#e8a33d', position: 'top', fontSize: 9 }}
            />

            <Line
              type="monotone"
              dataKey="methane"
              stroke="#f06363"
              strokeWidth={2}
              dot={{ r: 2 }}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="temp"
              stroke="#e8a33d"
              strokeWidth={2}
              dot={{ r: 2 }}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Screen Reader Data Table Fallback */}
      <div className="sr-only">
        <table>
          <caption>Methane and Temperature Convergence Telemetry</caption>
          <thead>
            <tr>
              <th>Time</th>
              <th>Methane (% LEL)</th>
              <th>Temp (°C)</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((row, idx) => (
              <tr key={idx}>
                <td>{row.time}</td>
                <td>{row.methane}</td>
                <td>{row.temp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
