import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Card } from '@/components/atoms';
import { TrendingDown, ShieldAlert, Award } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change: string;
  isPositive: boolean;
  icon: React.ReactNode;
}

function MetricCard({ title, value, change, isPositive, icon }: MetricCardProps) {
  return (
    <Card className="flex items-center justify-between p-4 bg-panel-2/30">
      <div className="flex flex-col gap-1">
        <span className="text-micro font-mono text-ink-dim uppercase">{title}</span>
        <span className="text-xl font-bold text-ink tabular-nums leading-none">{value}</span>
        <span
          className={`text-micro font-mono ${
            isPositive ? 'text-ok' : 'text-imminent'
          }`}
        >
          {change}
        </span>
      </div>
      <div className="p-2 bg-panel-2 rounded border border-line text-ink-dim shrink-0">
        {icon}
      </div>
    </Card>
  );
}

export function AlertFatigueMetrics() {
  // Memoize static charts data to prevent re-render loops on Recharts component
  const chartData = useMemo(
    () => [
      { date: '06/29', falseAlarms: 28, useful: 12 },
      { date: '06/30', falseAlarms: 25, useful: 15 },
      { date: '07/01', falseAlarms: 19, useful: 18 },
      { date: '07/02', falseAlarms: 14, useful: 22 },
      { date: '07/03', falseAlarms: 9, useful: 26 },
      { date: '07/04', falseAlarms: 6, useful: 31 },
      { date: '07/05', falseAlarms: 4, useful: 35 },
    ],
    []
  );

  const zonesData = [
    { zone: 'Zone 4 (Reformer)', current: 14, limit: 15, pct: 93, color: 'bg-near' },
    { zone: 'Zone 12 (Cracker)', current: 8, limit: 20, pct: 40, color: 'bg-ok' },
    { zone: 'Zone 2 (Storage)', current: 3, limit: 10, pct: 30, color: 'bg-ok' },
    { zone: 'Zone 8 (Sulfur)', current: 19, limit: 15, pct: 126, color: 'bg-imminent' },
  ];

  return (
    <div className="flex flex-col gap-4 text-ink select-none">
      {/* Top row cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <MetricCard
          title="ALERTS PER SHIFT"
          value="4.2"
          change="-42% FROM PAST SHIFT"
          isPositive={true}
          icon={<ShieldAlert className="h-4 w-4" />}
        />
        <MetricCard
          title="FALSE ALARM RATIO"
          value="10.2%"
          change="-18.5% THIS WEEK"
          isPositive={true}
          icon={<TrendingDown className="h-4 w-4" />}
        />
        <MetricCard
          title="OPERATOR ACTION RATE"
          value="89.8%"
          change="+12.4% VERIFICATION RATE"
          isPositive={true}
          icon={<Award className="h-4 w-4" />}
        />
      </div>

      {/* Grid: Charts + Zone thresholds */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Chart Column */}
        <Card className="lg:col-span-2 flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <span className="text-xs font-mono font-bold text-ink uppercase tracking-wide">
              Signal-To-Noise Trend
            </span>
            <span className="text-micro font-mono text-ink-dim uppercase">
              LAST 7 DAYS
            </span>
          </div>

          <div className="h-48 w-full font-mono text-micro select-text">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid stroke="#2a323d" strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="#8b949e" tickLine={false} />
                <YAxis stroke="#8b949e" tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#161b22',
                    borderColor: '#2a323d',
                    color: '#e6edf3',
                    borderRadius: '4px',
                  }}
                />
                <Line
                  name="False Alarms"
                  type="monotone"
                  dataKey="falseAlarms"
                  stroke="#f06363"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  name="Useful Alerts"
                  type="monotone"
                  dataKey="useful"
                  stroke="#4ec98a"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Zone limits Column */}
        <Card className="flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <span className="text-xs font-mono font-bold text-ink uppercase tracking-wide">
              Alert Volume vs Rate Limits
            </span>
            <span className="text-micro font-mono text-ink-dim uppercase">
              PER ZONE / SHIFT
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {zonesData.map((item) => (
              <div key={item.zone} className="flex flex-col gap-1 text-xs">
                <div className="flex justify-between items-center text-ink-dim">
                  <span className="font-semibold text-ink font-mono">{item.zone}</span>
                  <span className="font-mono tabular-nums">
                    {item.current}/{item.limit} ({item.pct}%)
                  </span>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 w-full bg-panel-2 rounded-full overflow-hidden border border-line">
                  <div
                    className={`h-full ${item.color} transition-all duration-slow`}
                    style={{ width: `${Math.min(100, item.pct)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
