import { useState } from 'react';
import type { RiskFinding } from '@/types';
import { Button } from '@/components/atoms';
import { Download, AlertCircle } from 'lucide-react';
import { getEvidenceManifest } from '@/api/intelligence';

interface ExportButtonProps {
  finding: RiskFinding;
}

export function ExportEvidenceButton({ finding }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setNote(null);
    const packId = `EP-${finding.findingId}`;
    try {
      const manifest = await getEvidenceManifest(packId, finding.findingId);
      const payload =
        manifest.degraded || !manifest.items
          ? {
              exportedAt: new Date().toISOString(),
              findingId: finding.findingId,
              packId,
              degraded: true,
              reason: manifest.reason ?? 'MinIO not configured — local export only',
              title: finding.title,
              zoneId: finding.zoneId,
              lineage: finding.lineage,
            }
          : manifest;

      const dataStr =
        'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(payload, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `evidence-${finding.findingId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();

      if (manifest.degraded) {
        setNote(manifest.reason ?? 'Exported local stub — configure MinIO for stored packs.');
      }
    } catch {
      setNote('Evidence API unavailable — start backend with `make dev`.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      <Button
        variant="secondary"
        size="sm"
        onClick={handleExport}
        loading={isExporting}
        icon={<Download className="h-3.5 w-3.5" />}
        className="text-micro font-mono font-bold uppercase"
      >
        Export Evidence Pack
      </Button>
      {note && (
        <span className="text-micro text-ink-dim font-mono flex items-start gap-1">
          <AlertCircle className="h-3 w-3 shrink-0 mt-0.5" />
          {note}
        </span>
      )}
    </div>
  );
}
