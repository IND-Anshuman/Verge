import { useEffect } from 'react';
import { useSensorsStore } from '@/stores/sensors';
import { getSensorRibbon, getSystemHealth } from '@/api';
import { Badge } from '@/components/atoms';
import { AlertTriangle, ShieldCheck, ShieldAlert } from 'lucide-react';

export function SensorRibbon() {
  const { ribbon, health, setRibbon, setHealth, setError } = useSensorsStore();

  const tick = async () => {
    try {
      const ribbonData = await getSensorRibbon();
      const healthData = await getSystemHealth();
      setRibbon(ribbonData);
      setHealth(healthData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sensor status unavailable');
    }
  };

  useEffect(() => {
    tick();
    const interval = setInterval(tick, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="h-8 bg-panel-2 border-b border-line flex items-center justify-between px-4 text-xs font-mono select-none shrink-0"
    >
      {/* Left side: Sensor counts summary text */}
      <div className="flex items-center gap-2 text-ink-dim min-w-0 flex-1 whitespace-nowrap">
        <span className="h-1.5 w-1.5 rounded-full bg-ok animate-pulse shrink-0" />
        <span className="font-semibold text-ink uppercase tracking-wide shrink-0">Sensors:</span>
        <span className="tabular-nums truncate">{ribbon?.text ?? 'Connecting to sensor health plane...'}</span>
      </div>

      {/* Right side: LLM degradation and Audit integrity badges */}
      <div className="flex items-center gap-2 shrink-0 whitespace-nowrap">
        {/* LLM Narrative status */}
        {health && health.llm.degraded && (
          <Badge variant="generic" color="imminent" className="flex items-center gap-1 text-micro font-bold py-0.5 border-dashed">
            <AlertTriangle className="h-3 w-3 shrink-0" />
            AI NARRATIVE DEGRADED
          </Badge>
        )}

        {/* Audit Chain Integrity status */}
        {health && (
          <Badge
            variant="generic"
            color={health.audit.verified ? 'ok' : 'imminent'}
            className="flex items-center gap-1 text-micro font-bold py-0.5"
          >
            {health.audit.verified ? (
              <>
                <ShieldCheck className="h-3 w-3 text-ok shrink-0" />
                AUDIT VERIFIED &middot; {health.audit.entries} ENTRIES
              </>
            ) : (
              <>
                <ShieldAlert className="h-3 w-3 text-imminent shrink-0" />
                AUDIT FAILURE &middot; TAMPER DETECTED
              </>
            )}
          </Badge>
        )}
      </div>
    </div>
  );
}
