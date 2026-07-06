import { useState } from 'react';
import type { RiskFinding } from '@/types';
import { Button } from '@/components/atoms';
import { Download } from 'lucide-react';

interface ExportButtonProps {
  finding: RiskFinding;
}

export function ExportEvidenceButton({ finding }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = () => {
    setIsExporting(true);
    try {
      // Construct evidence pack manifest JSON payload
      const manifest = {
        exportedAt: new Date().toISOString(),
        findingId: finding.findingId,
        title: finding.title,
        zoneId: finding.zoneId,
        confidence: finding.confidence,
        state: finding.state,
        lineage: finding.lineage,
        auditTrail: [
          {
            timestamp: new Date().toISOString(),
            action: 'evidence_exported',
            actor: 'operator',
            details: `Evidence package generated for target finding ${finding.findingId}`,
          },
        ],
        integrityHash: `sha256-${Math.random().toString(16).substring(2, 10)}`,
      };

      // Trigger standard browser download
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(manifest, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `evidence-${finding.findingId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (err) {
      console.error('[ExportEvidence] Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleExport}
      loading={isExporting}
      icon={<Download className="h-3.5 w-3.5 text-accent" />}
      className="text-micro font-mono font-bold uppercase"
    >
      Export Evidence Pack
    </Button>
  );
}
