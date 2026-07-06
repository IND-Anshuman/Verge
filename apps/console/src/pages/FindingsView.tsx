import { useEffect } from 'react';
import { useFindingsStore, useFilteredFindings } from '@/stores/findings';
import { useSensorsStore } from '@/stores/sensors';
import { FindingsBoard } from '@/components/organisms/FindingsBoard';
import { FindingFilters } from '@/components/molecules/FindingFilters';
import { SuppressionSuggestion } from '@/components/organisms/SuppressionSuggestion';
import { ResponseOrchestratorPanel } from '@/components/organisms/ResponseOrchestratorPanel';
import { PanelSystem } from '@/components/organisms/PanelSystem';
import { getFindings } from '@/api';
import type { RiskFinding } from '@/types';
import { AlertCircle } from 'lucide-react';

const MOCK_FINDINGS: RiskFinding[] = [
  {
    findingId: 'rf-0491',
    createdAt: new Date(Date.now() - 600000).toISOString(),
    zoneId: 'Zone 4 (Primary Reformer)',
    title: 'Hydrocarbon Gas Accumulation',
    state: 'new',
    confidence: 0.92,
    leadTimeBand: 'IMMINENT',
    estimateQuality: 'high',
    confidenceDegraded: false,
    confidenceDegradedBy: [],
    counterfactual: 'Immediate ESD action recommended to prevent ignition risk.',
    lineage: ['CH4-0411 reading (1.2% LEL)', 'PTW-4091 hot work'],
    shadow: false,
    contributingSignals: [],
  },
  {
    findingId: 'rf-1204',
    createdAt: new Date(Date.now() - 1800000).toISOString(),
    zoneId: 'Zone 12 (Confined Compressor)',
    title: 'Compressor Bearing Thermal Runaway',
    state: 'acknowledged',
    confidence: 0.81,
    leadTimeBand: 'NEAR',
    estimateQuality: 'medium',
    confidenceDegraded: true,
    confidenceDegradedBy: ['TEMP-1201 (faulty calibration)'],
    counterfactual: 'Lubrication inspection dispatch confirmed.',
    lineage: ['TEMP-1201 reading (89C)', 'TEMP-1202 reading (92C)', 'VIB-1203 reading (4.2mm/s)'],
    shadow: false,
    contributingSignals: [],
  },
  {
    findingId: 'rf-0284',
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    zoneId: 'Zone 2 (Storage Dikes)',
    title: 'Nitrogen Purge Pressure Decline',
    state: 'in-progress',
    confidence: 0.74,
    leadTimeBand: 'WATCH',
    estimateQuality: 'low',
    confidenceDegraded: false,
    confidenceDegradedBy: [],
    lineage: ['PRES-0211 reading (1.1 bar)', 'WO-9912 valve maintenance'],
    shadow: false,
    contributingSignals: [],
  },
  {
    findingId: 'rf-0812',
    createdAt: new Date(Date.now() - 14400000).toISOString(),
    zoneId: 'Zone 8 (Sulfur Recovery)',
    title: 'H2S Gas Release Warning',
    state: 'escalated',
    confidence: 0.95,
    leadTimeBand: 'IMMINENT',
    estimateQuality: 'high',
    confidenceDegraded: false,
    confidenceDegradedBy: [],
    counterfactual: 'Evacuation advisory issued.',
    lineage: ['H2S-0814 reading (15 ppm)', 'PA-801 active broadcast'],
    shadow: false,
    contributingSignals: [],
  },
  {
    findingId: 'rf-0391',
    createdAt: new Date(Date.now() - 60000).toISOString(),
    zoneId: 'Zone 3 (Vapor Recovery)',
    title: '[Simulated Shadow] Flare Gas Relief Surge',
    state: 'new',
    confidence: 0.88,
    leadTimeBand: 'NEAR',
    estimateQuality: 'high',
    confidenceDegraded: false,
    confidenceDegradedBy: [],
    lineage: ['FLOW-0312 reading (240 t/h)', 'PTW-312 active'],
    shadow: true,
    contributingSignals: [],
  },
];

import { useState } from 'react';
import { MobileNavigation } from '@/components/organisms/MobileNavigation';
import { FindingCardMobile } from '@/components/organisms/FindingCardMobile';
import { MobileFieldWorkerPanel } from '@/components/organisms/MobileFieldWorkerPanel';
import { PermitsPanel } from '@/components/organisms/PermitsPanel';
import { DigitalTwinMap } from '@/components/organisms/DigitalTwinMap';

export default function FindingsView() {
  const { setFindings, setLoading, setError, isLoading, error, shadow, findings } = useFindingsStore();
  const { setRibbon, setHealth } = useSensorsStore();
  const filteredFindings = useFilteredFindings();

  // Responsive mobile state tracking
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [mobileTab, setMobileTab] = useState<'home' | 'map' | 'permits' | 'profile'>('home');

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getFindings(shadow);
      setFindings(data);
      setError(null);
    } catch (err) {
      setError('API gateway offline. Running in offline mockup mode.');
      const mockResult = MOCK_FINDINGS.filter((f) => f.shadow === shadow);
      setFindings(mockResult);

      setRibbon({
        text: '568/572 LIVE · 3 STALE · 1 MISSING · 0 TAMPERED',
        counts: { live: 568, stale: 3, stuckAtValue: 0, outOfRange: 0, clockSkewed: 0, missing: 1 },
      });
      setHealth({
        status: 'warning',
        llm: { provider: 'aimlapi', degraded: false },
        audit: { entries: 124, head: 'abc123hash', verified: true },
        findings: mockResult.length,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [shadow]);

  // Mobile layout branch
  if (isMobile) {
    return (
      <div className="flex flex-col h-[calc(100vh-120px)] overflow-hidden relative text-ink">
        {/* Offline API Status Warning Bar */}
        {error && mobileTab === 'home' && (
          <div className="bg-imminent/10 border-b border-imminent/20 text-imminent text-[10px] p-2 flex items-center gap-2 select-text shrink-0 font-mono uppercase">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-imminent" />
            <div className="flex-1">
              Ledger offline: mockup mode active.
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto scrollbar p-4 pb-2">
          {mobileTab === 'home' && (
            <div className="flex flex-col gap-3">
              <span className="text-xs font-mono font-bold text-ink-dim uppercase select-none">
                Active Field Findings
              </span>
              {filteredFindings.map((finding) => (
                <FindingCardMobile
                  key={finding.findingId}
                  finding={finding}
                  onChange={loadData}
                />
              ))}
              {filteredFindings.length === 0 && (
                <div className="text-center p-6 border border-dashed border-line text-xs font-mono text-ink-dim uppercase rounded">
                  NO ACTIVE ALARMS
                </div>
              )}
            </div>
          )}

          {mobileTab === 'map' && (
            <div className="h-full min-h-[300px] w-full">
              <DigitalTwinMap findings={filteredFindings} />
            </div>
          )}

          {mobileTab === 'permits' && (
            <div className="h-full">
              <PermitsPanel />
            </div>
          )}

          {mobileTab === 'profile' && (
            <MobileFieldWorkerPanel />
          )}
        </div>

        {/* Bottom tab navigator */}
        <MobileNavigation activeTab={mobileTab} setActiveTab={setMobileTab} />
      </div>
    );
  }

  // Desktop layout branch
  return (
    <div className="flex flex-col gap-4 p-4 h-[calc(100vh-80px)] overflow-hidden">
      {/* Offline API Status Warning Bar */}
      {error && (
        <div className="bg-imminent/10 border border-imminent/20 text-imminent text-xs rounded p-2.5 flex items-center gap-2 select-text shrink-0">
          <AlertCircle className="h-4 w-4 shrink-0 text-imminent" />
          <div className="flex-1">
            <span className="font-bold uppercase tracking-wider mr-1">OFFLINE WORKSPACE:</span>
            {error} Start the backend using <code className="bg-bg px-1 py-0.5 rounded border border-line ml-1">make dev</code> to connect to live telemetry.
          </div>
        </div>
      )}

      {/* Filters and Actions */}
      <div className="flex items-center justify-between border-b border-line pb-3 shrink-0">
        <FindingFilters />
        <div className="text-xs text-ink-dim tabular-nums">
          Showing <span className="font-semibold text-ink">{filteredFindings.length}</span> findings
        </div>
      </div>

      {/* Main Board Area */}
      <div className="flex-1 overflow-hidden flex flex-col gap-3 relative">
        <SuppressionSuggestion activeFindings={findings} onChange={loadData} />

        {isLoading && findings.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center bg-bg/50">
            <span className="text-xs text-ink-dim font-mono animate-pulse">LOADING TELETREAD BOARD...</span>
          </div>
        ) : (
          <PanelSystem
            findings={filteredFindings}
            boardComponent={<FindingsBoard findings={filteredFindings} onChange={loadData} />}
            responseComponent={<ResponseOrchestratorPanel activeFindings={findings} onChange={loadData} />}
          />
        )}
      </div>
    </div>
  );
}
