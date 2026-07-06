import { useState, useMemo } from 'react';
import { Card, Badge, Button } from '@/components/atoms';
import { ShieldCheck, ShieldAlert, Download, Search, AlertTriangle } from 'lucide-react';

interface AuditEntry {
  index: number;
  hash: string;
  prevHash: string;
  timestamp: string;
  actor: string;
  eventType: string;
  details: string;
  isValid: boolean;
}

const MOCK_AUDIT_LOGS: AuditEntry[] = [
  {
    index: 3,
    hash: '8fcf2b01cc28f7311d9f06363c48de13cf14a1a361efb701a892b0e98038b3a1',
    prevHash: '4b29c9183d8a9e7019f2a0b12c88de130f14a1b0266efb7012892b1e98038b2d',
    timestamp: '2026-07-05T16:22:16Z',
    actor: 'operator',
    eventType: 'finding_acknowledged',
    details: 'Acknowledged finding RF-0491 in Zone 4 (Primary Reformer)',
    isValid: true,
  },
  {
    index: 2,
    hash: '4b29c9183d8a9e7019f2a0b12c88de130f14a1b0266efb7012892b1e98038b2d',
    prevHash: 'a1bcf91c28f11d9a0f0638c4de230cf14a1b0286efb7012892b1e98038b9d034',
    timestamp: '2026-07-05T15:45:57Z',
    actor: 'system',
    eventType: 'finding_created',
    details: 'Imminent risk finding RF-0491 co-convergence trigger logged',
    isValid: true,
  },
  {
    index: 1,
    hash: 'a1bcf91c28f11d9a0f0638c4de230cf14a1b0286efb7012892b1e98038b9d034',
    prevHash: '0000000000000000000000000000000000000000000000000000000000000000',
    timestamp: '2026-07-05T15:00:00Z',
    actor: 'system',
    eventType: 'genesis_block',
    details: 'Operator telemetry ledger chain initialized',
    isValid: true,
  },
];

export default function AuditView() {
  const [logs, setLogs] = useState<AuditEntry[]>(MOCK_AUDIT_LOGS);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(logs[0]);
  const [search, setSearch] = useState('');

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const q = search.toLowerCase();
      return (
        log.details.toLowerCase().includes(q) ||
        log.hash.toLowerCase().includes(q) ||
        log.eventType.toLowerCase().includes(q)
      );
    });
  }, [logs, search]);

  const handleExportAudit = () => {
    try {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(logs, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', 'verge-audit-chain.json');
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (err) {
      console.error('[AuditExport] Export failed:', err);
    }
  };

  const handleSimulateDiscontinuity = () => {
    // Inject a tampered log block to test validation indicators
    const tamperedEntry: AuditEntry = {
      index: 4,
      hash: 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
      prevHash: 'corrupted-hash-link',
      timestamp: new Date().toISOString(),
      actor: 'unknown',
      eventType: 'unauthorized_patch',
      details: 'ATTEMPTED MANIPULATION: Log database entry updated externally',
      isValid: false,
    };
    setLogs((prev) => [tamperedEntry, ...prev]);
    setSelectedEntry(tamperedEntry);
  };

  return (
    <div className="flex flex-col gap-6 p-4 h-[calc(100vh-80px)] overflow-hidden text-ink font-sans">
      {/* Header section */}
      <div className="flex items-center justify-between border-b border-line pb-3 select-none shrink-0">
        <div className="flex flex-col gap-1">
          <h1 className="text-lg font-bold uppercase font-mono tracking-wide">
            Audit Ledger Chain Verification
          </h1>
          <p className="text-xs text-ink-dim font-mono">
            Verify sha256 block-level audit trail logs to trace system configuration changes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSimulateDiscontinuity}
            icon={<AlertTriangle className="h-3.5 w-3.5 text-imminent" />}
            className="text-micro font-mono font-bold uppercase text-ink-dim hover:text-imminent"
          >
            Simulate Tamper
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportAudit}
            icon={<Download className="h-3.5 w-3.5 text-accent" />}
            className="text-micro font-mono font-bold uppercase"
          >
            Export Ledger
          </Button>
        </div>
      </div>

      {/* Main Content viewport */}
      <div className="flex-1 flex flex-col md:flex-row gap-4 overflow-hidden">
        {/* Left Side: Search & Table Logs */}
        <div className="w-full md:w-2/3 flex flex-col gap-3 overflow-hidden">
          {/* Search bar */}
          <div className="relative shrink-0 select-none">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-ink-dim/40" />
            <input
              type="text"
              placeholder="Search logs by hash, event, or keyword description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-8 pl-9 pr-3 rounded border border-line text-xs bg-panel text-ink placeholder:text-ink-dim/40 focus:outline-none"
            />
          </div>

          {/* Table Container */}
          <div className="flex-1 overflow-y-auto scrollbar border border-line rounded">
            <table className="w-full text-left font-mono text-xs select-text">
              <thead className="bg-panel-2/50 border-b border-line text-ink-dim text-micro uppercase select-none">
                <tr>
                  <th className="p-2.5 w-12">Index</th>
                  <th className="p-2.5 w-32">Event Type</th>
                  <th className="p-2.5">Hash Linkage</th>
                  <th className="p-2.5 w-16 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/30 bg-bg">
                {filteredLogs.map((log) => (
                  <tr
                    key={log.index}
                    onClick={() => setSelectedEntry(log)}
                    className={`cursor-pointer hover:bg-panel-2/20 transition-colors ${
                      selectedEntry?.index === log.index ? 'bg-panel-2/50' : ''
                    } ${!log.isValid ? 'bg-imminent/5' : ''}`}
                  >
                    <td className="p-2.5 text-ink-dim">{log.index}</td>
                    <td className="p-2.5 uppercase font-bold text-ink-dim truncate max-w-[120px]">{log.eventType}</td>
                    <td className="p-2.5 truncate max-w-[180px]">{log.hash}</td>
                    <td className="p-2.5 text-center select-none">
                      {log.isValid ? (
                        <ShieldCheck className="h-4 w-4 text-ok mx-auto" />
                      ) : (
                        <ShieldAlert className="h-4 w-4 text-imminent mx-auto animate-pulse" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Side: Block Detail Panel */}
        <div className="flex-1 flex flex-col gap-3 overflow-hidden select-text">
          <span className="text-xs font-mono font-bold text-ink-dim uppercase select-none">
            Block Properties
          </span>
          {selectedEntry ? (
            <Card className={`p-4 border flex flex-col gap-3 h-full overflow-y-auto scrollbar bg-panel ${
              selectedEntry.isValid ? 'border-line' : 'border-imminent/40 bg-imminent/5'
            }`}>
              <div className="flex justify-between items-center border-b border-line pb-2 mb-1 shrink-0 select-none">
                <span className="font-bold text-ink font-mono">BLOCK #{selectedEntry.index}</span>
                <Badge
                  variant="generic"
                  color={selectedEntry.isValid ? 'ok' : 'imminent'}
                  className="font-mono text-micro font-bold py-0.5"
                >
                  {selectedEntry.isValid ? 'VERIFIED' : 'INTEGRITY FAILED'}
                </Badge>
              </div>

              <div className="flex flex-col gap-1 font-mono text-xs">
                <span className="text-micro text-ink-dim uppercase select-none">Event Class</span>
                <span className="text-ink font-semibold uppercase">{selectedEntry.eventType}</span>
              </div>

              <div className="flex flex-col gap-1 font-mono text-xs">
                <span className="text-micro text-ink-dim uppercase select-none">Timestamp</span>
                <span className="text-ink">{selectedEntry.timestamp}</span>
              </div>

              <div className="flex flex-col gap-1 font-mono text-xs">
                <span className="text-micro text-ink-dim uppercase select-none">Actor</span>
                <span className="text-ink uppercase">{selectedEntry.actor}</span>
              </div>

              <div className="flex flex-col gap-1 font-mono text-xs">
                <span className="text-micro text-ink-dim uppercase select-none">Transaction Details</span>
                <p className="text-ink leading-relaxed">{selectedEntry.details}</p>
              </div>

              <div className="flex flex-col gap-1 font-mono text-micro text-ink-dim break-all">
                <span className="text-micro text-ink-dim uppercase select-none">BLOCK HASH (SHA-256)</span>
                <span className="bg-bg border border-line p-1.5 rounded">{selectedEntry.hash}</span>
              </div>

              <div className="flex flex-col gap-1 font-mono text-micro text-ink-dim break-all">
                <span className="text-micro text-ink-dim uppercase select-none">PREVIOUS HASH</span>
                <span className="bg-bg border border-line p-1.5 rounded">{selectedEntry.prevHash}</span>
              </div>

              {!selectedEntry.isValid && (
                <div className="bg-imminent/5 border border-imminent/10 p-3 rounded flex items-start gap-2 text-xs text-imminent leading-normal select-none">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Ledger Discontinuity:</span> Previous block hash link is corrupted or missing. The chain verify fails.
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <div className="flex-1 flex items-center justify-center border border-dashed border-line rounded">
              <span className="text-xs text-ink-dim font-mono uppercase">Select a block to inspect</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
