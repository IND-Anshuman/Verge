import { useCallback, useEffect, useState } from "react";
import type { RiskFinding } from "@verge/schema";
import { api } from "./api";
import { FindingsBoard } from "./components/FindingsBoard";
import { SensorRibbon } from "./components/SensorRibbon";

export default function App() {
  const [findings, setFindings] = useState<RiskFinding[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [shadow, setShadow] = useState(false);

  const refresh = useCallback(() => {
    api
      .findings(shadow)
      .then((f) => {
        setFindings(f);
        setError(null);
      })
      .catch((e) => setError(String(e)));
  }, [shadow]);

  useEffect(() => {
    refresh();
    const h = setInterval(refresh, 3000);
    return () => clearInterval(h);
  }, [refresh]);

  return (
    <div className="app">
      <header className="topbar">
        <span className="wordmark">Verge</span>
        <span className="tagline">lead-time intelligence · operator console</span>
        <span className="topbar-spacer" />
        <div className="mode-toggle">
          <button
            className={`mode ${!shadow ? "mode-on" : ""}`}
            onClick={() => setShadow(false)}
          >
            Live
          </button>
          <button
            className={`mode ${shadow ? "mode-on" : ""}`}
            onClick={() => setShadow(true)}
          >
            Shadow
          </button>
        </div>
      </header>
      <SensorRibbon />
      {shadow && (
        <div className="shadow-banner">
          Shadow mode — what Verge would have flagged. Not surfaced as live alerts (§14.5).
        </div>
      )}
      {error && <div className="error">API unreachable ({error}). Is the gateway up on :8000?</div>}
      <FindingsBoard findings={findings} onChange={refresh} />
    </div>
  );
}
