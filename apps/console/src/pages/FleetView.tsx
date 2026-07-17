import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Badge, Button, EmptyState } from '@/components/atoms';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { CHART_SERIES, CHART_GRID, chartAxisProps, chartTooltipStyle } from '@/lib/chartTheme';
import { AlertTriangle, AlertCircle, Radio } from 'lucide-react';
import { getFleetSummary, type FleetPlant } from '@/api/fleet';

export default function FleetView() {
  const navigate = useNavigate();
  const [plants, setPlants] = useState<FleetPlant[]>([]);
  const [connectedSite, setConnectedSite] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const summary = await getFleetSummary();
        setPlants(summary.plants);
        setConnectedSite(summary.connectedSite);
        setLoadError(null);
      } catch {
        setPlants([]);
        setLoadError('Fleet summary unavailable — start API with `make dev`.');
      }
    };
    void load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const chartData = plants.map((p) => ({
    name: p.plantId.replace('PLT-', ''),
    'Sensor Health %': p.sensorHealth ?? 0,
    'Active Alarms': p.activeRisks,
  }));

  return (
    <div className="flex flex-col gap-6 p-4 h-[calc(100vh-80px)] overflow-y-auto scrollbar select-text text-ink">
      <div className="flex flex-col gap-1 border-b border-line pb-3 select-none">
        <h1 className="text-lg font-semibold tracking-tight">Multi-site fleet</h1>
        <p className="text-xs text-ink-dim">
          Live risk counts only. Unmeasured KPIs (TRIR, alert fatigue) stay hidden until a site feeds
          them.
          {connectedSite ? (
            <span className="font-mono text-micro ml-2 text-ink-dim/70">
              CONNECTED · {connectedSite}
            </span>
          ) : null}
        </p>
      </div>

      {loadError && (
        <div className="bg-imminent/10 border border-imminent/20 text-imminent text-xs p-2 rounded flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {loadError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-3">
          <span className="text-micro font-mono text-ink-dim uppercase tracking-[0.1em] select-none">
            Production sites
          </span>
          {plants.length === 0 && !loadError && (
            <span className="text-xs font-mono text-ink-dim">Loading fleet…</span>
          )}
          {plants.map((plant) => {
            const connected = plant.connected ?? plant.plantId === connectedSite;
            return (
              <Card
                key={plant.plantId}
                className={`p-3.5 border flex justify-between items-center ${
                  plant.status === 'imminent'
                    ? 'border-imminent/30 bg-imminent/5'
                    : plant.status === 'near'
                      ? 'border-near/30 bg-near/5'
                      : 'border-line bg-panel-2/30'
                }`}
              >
                <div className="flex flex-col gap-1 pr-4">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="generic"
                      color={
                        plant.status === 'imminent'
                          ? 'imminent'
                          : plant.status === 'near'
                            ? 'near'
                            : 'ok'
                      }
                      className="font-mono text-micro font-bold py-0.5"
                    >
                      {plant.plantId}
                    </Badge>
                    <span className="text-xs font-semibold text-ink leading-relaxed">
                      {plant.name}
                    </span>
                  </div>
                  <span className="text-micro font-mono text-ink-dim">
                    {plant.location}
                    {!connected ? ' · not connected' : ' · live'}
                  </span>
                  <div className="flex items-center gap-3 text-micro font-mono text-ink-dim mt-1">
                    <span>
                      Active risks:{' '}
                      <strong className="text-ink tabular-nums">{plant.activeRisks}</strong>
                    </span>
                    <span>
                      Sensor health:{' '}
                      <strong className="text-ink tabular-nums">
                        {plant.measured.sensorHealth && plant.sensorHealth != null
                          ? `${plant.sensorHealth}%`
                          : '—'}
                      </strong>
                    </span>
                  </div>
                </div>

                <div className="flex flex-col gap-1.5 shrink-0 select-none">
                  {plant.status === 'imminent' && connected && (
                    <div className="flex items-center gap-1 text-micro font-mono text-imminent font-bold uppercase animate-pulse">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Imminent
                    </div>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      if (connected) navigate('/');
                    }}
                    disabled={!connected}
                    className="text-micro font-mono font-medium text-ink-dim hover:text-ink"
                  >
                    {connected ? 'Open console' : 'Not connected'}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>

        <div className="flex flex-col gap-3">
          <span className="text-micro font-mono text-ink-dim uppercase tracking-[0.1em] select-none">
            Measured comparison
          </span>
          <div className="h-56 w-full border border-line bg-panel-2/30 p-3 rounded-md select-none font-mono text-micro">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" {...chartAxisProps} />
                  <YAxis {...chartAxisProps} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Bar
                    dataKey="Active Alarms"
                    fill={CHART_SERIES[1]}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={28}
                  />
                  <Bar
                    dataKey="Sensor Health %"
                    fill={CHART_SERIES[0]}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={28}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-ink-dim text-xs">No fleet data</span>
            )}
          </div>
        </div>
      </div>

      <EmptyState
        icon={<Radio className="h-5 w-5" />}
        title="Fleet circulars not connected"
        hint="Broadcast bulletins will appear here when a multi-site messaging API is commissioned — local fake circulars were removed."
        className="mt-2"
      />
    </div>
  );
}
