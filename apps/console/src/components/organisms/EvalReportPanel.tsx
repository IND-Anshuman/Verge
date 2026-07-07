import { useEffect, useState } from 'react';
import { Card } from '@/components/atoms';
import { AlertCircle, BarChart3 } from 'lucide-react';
import { getEvalReport } from '@/api/platform';

interface EvalRow {
  incident: string;
  verge: { leadMin: number | null; band?: string | null; bandCalibrated?: boolean | null };
  b0: { leadMin: number | null };
  b1: { leadMin: number | null };
  b2: { leadMin: number | null };
  fpr?: number | null;
}

function fmtLead(v: number | null | undefined): string {
  return v == null ? 'silent' : `${v} min`;
}

export function EvalReportPanel() {
  const [rows, setRows] = useState<EvalRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getEvalReport()
      .then((data) => {
        setRows(data as EvalRow[]);
        setError(null);
      })
      .catch(() => {
        setRows([]);
        setError('No eval report — run `make eval` or `uv run verge replay --all`.');
      });
  }, []);

  return (
    <Card className="p-3 border-line bg-panel-2/30 flex flex-col gap-2">
      <span className="text-micro font-mono font-bold text-ink-dim uppercase flex items-center gap-1.5">
        <BarChart3 className="h-3.5 w-3.5" />
        Replay Harness (§10)
      </span>
      {error && (
        <div className="text-xs text-ink-dim flex items-center gap-2 font-mono">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}
      {rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-micro font-mono text-left">
            <thead className="text-ink-dim uppercase">
              <tr>
                <th className="py-1 pr-2">Incident</th>
                <th className="py-1 pr-2">Verge</th>
                <th className="py-1 pr-2">B0</th>
                <th className="py-1 pr-2">B1</th>
                <th className="py-1 pr-2">B2</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.incident} className="border-t border-line/60">
                  <td className="py-1 pr-2 text-ink">{r.incident}</td>
                  <td className="py-1 pr-2 text-accent font-bold">
                    {fmtLead(r.verge?.leadMin)} ({r.verge?.band ?? '—'})
                  </td>
                  <td className="py-1 pr-2">{fmtLead(r.b0?.leadMin)}</td>
                  <td className="py-1 pr-2">{fmtLead(r.b1?.leadMin)}</td>
                  <td className="py-1 pr-2">{fmtLead(r.b2?.leadMin)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
