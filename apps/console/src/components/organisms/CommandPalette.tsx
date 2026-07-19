import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Command } from 'cmdk';
import { useFindingsStore } from '@/stores/findings';
import { LeadTimeGauge } from '@/components/molecules/LeadTimeGauge';
import {
  Activity,
  History,
  BarChart2,
  Shield,
  Settings,
  ArrowRightLeft,
  BookOpen,
  Wrench,
  Network,
  Eye,
  Radio,
  CornerDownLeft,
} from 'lucide-react';

/* ⌘K command palette — keyboard-first navigation and finding search.
   Navigation + search only; safety-relevant actions (acknowledge, dispatch,
   declare) stay on their own explicit, approver-gated controls (P8). */

/* Mirrors the shell nav exactly — the palette is a complete map of the
   product; a view missing here is a trust break for keyboard operators. */
const VIEWS = [
  { label: 'Board', to: '/', icon: Activity },
  { label: 'Knowledge', to: '/knowledge', icon: BookOpen },
  { label: 'Graph', to: '/graph', icon: Network },
  { label: 'Maintenance', to: '/maintenance', icon: Wrench },
  { label: 'Replay', to: '/replay', icon: History },
  { label: 'Fleet', to: '/fleet', icon: BarChart2 },
  { label: 'Audit', to: '/audit', icon: Shield },
  { label: 'Admin', to: '/admin', icon: Settings },
  { label: 'Shift handover', to: '/handover', icon: ArrowRightLeft },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { findings, shadow, setShadow } = useFindingsStore();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const activeFindings = useMemo(
    () => findings.filter((f) => f.state !== 'closed' && f.state !== 'resolved').slice(0, 30),
    [findings],
  );

  const go = (fn: () => void) => {
    fn();
    setOpen(false);
  };

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      className="fixed inset-0 z-50"
    >
      <div className="fixed inset-0 bg-[color:var(--scrim)]" onClick={() => setOpen(false)} aria-hidden="true" />
      <div className="fixed left-1/2 top-[18vh] -translate-x-1/2 w-[560px] max-w-[calc(100vw-32px)]">
        <div className="bg-panel border border-line-2 rounded-lg float-layer panel-in overflow-hidden">
          <Command.Input
            placeholder="Jump to a view, search findings…"
            className="w-full h-11 px-4 bg-transparent text-sm text-ink placeholder:text-ink-dim/60 border-b border-line focus:outline-none font-sans"
            autoFocus
          />
          <Command.List className="max-h-[46vh] overflow-y-auto scrollbar p-1.5">
            <Command.Empty className="py-8 text-center text-xs font-mono text-ink-dim select-none">
              Nothing matches.
            </Command.Empty>

            <Command.Group
              heading="Views"
              className="[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-micro [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:text-ink-dim/60"
            >
              {VIEWS.map((v) => (
                <Command.Item
                  key={v.to}
                  value={`view ${v.label}`}
                  onSelect={() => go(() => navigate(v.to))}
                  className="flex items-center gap-2.5 px-2.5 h-9 rounded text-sm text-ink-dim cursor-pointer select-none data-[selected=true]:bg-panel-2 data-[selected=true]:text-ink"
                >
                  <v.icon className="h-4 w-4 shrink-0" />
                  {v.label}
                  <CornerDownLeft className="h-3 w-3 ml-auto opacity-0 data-[selected=true]:opacity-40" />
                </Command.Item>
              ))}
            </Command.Group>

            <Command.Group
              heading="Mode"
              className="[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-micro [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:text-ink-dim/60"
            >
              <Command.Item
                value={shadow ? 'switch to live mode' : 'switch to shadow mode'}
                onSelect={() => go(() => setShadow(!shadow))}
                className="flex items-center gap-2.5 px-2.5 h-9 rounded text-sm text-ink-dim cursor-pointer select-none data-[selected=true]:bg-panel-2 data-[selected=true]:text-ink"
              >
                {shadow ? <Radio className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                {shadow ? 'Switch to live mode' : 'Switch to shadow mode'}
              </Command.Item>
            </Command.Group>

            {activeFindings.length > 0 && (
              <Command.Group
                heading="Active findings"
                className="[&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-micro [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:text-ink-dim/60"
              >
                {activeFindings.map((f) => (
                  <Command.Item
                    key={f.findingId}
                    value={`${f.findingId} ${f.title} ${f.zoneId} ${f.leadTimeBand}`}
                    onSelect={() => go(() => navigate(`/findings/${f.findingId}`))}
                    className="flex items-center gap-2.5 px-2.5 h-10 rounded cursor-pointer select-none data-[selected=true]:bg-panel-2"
                  >
                    <span className="w-24 shrink-0">
                      <LeadTimeGauge band={f.leadTimeBand} size="sm" showLabel={false} />
                    </span>
                    <span className="flex flex-col min-w-0">
                      <span className="text-xs text-ink truncate">{f.title}</span>
                      <span className="text-micro font-mono text-ink-dim">
                        {f.findingId} · {f.zoneId}
                      </span>
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
          <div className="flex items-center gap-3 px-3 h-8 border-t border-line text-micro font-mono text-ink-dim/60 select-none">
            <span className="flex items-center gap-1"><kbd className="kbd">↑↓</kbd> navigate</span>
            <span className="flex items-center gap-1"><kbd className="kbd">↵</kbd> open</span>
            <span className="flex items-center gap-1"><kbd className="kbd">esc</kbd> close</span>
          </div>
        </div>
      </div>
    </Command.Dialog>
  );
}
