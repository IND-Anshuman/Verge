import { useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { useFindingsStore } from '@/stores/findings';
import { useConnectionStore } from '@/stores/connection';
import { useSensorsStore } from '@/stores/sensors';
import { getSystemHealth } from '@/api';
import { SensorRibbon } from '@/components/organisms/SensorRibbon';
import { DegradationBannerStrip } from '@/components/organisms/DegradationBannerStrip';
import { CommandPalette } from '@/components/organisms/CommandPalette';
import { Activity, BarChart2, Settings, History, ArrowRightLeft, Shield, Search, BookOpen, Wrench, Network } from 'lucide-react';
import { Logo, Toaster, Kbd } from '@/components/atoms';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const NAV = [
  { to: '/', key: 'board', icon: Activity },
  { to: '/knowledge', key: 'knowledge', icon: BookOpen },
  { to: '/graph', key: 'graph', icon: Network },
  { to: '/maintenance', key: 'maintenance', icon: Wrench },
  { to: '/replay', key: 'replay', icon: History },
  { to: '/fleet', key: 'fleet', icon: BarChart2 },
  { to: '/audit', key: 'audit', icon: Shield },
  { to: '/admin', key: 'config', icon: Settings },
  { to: '/handover', key: 'handover', icon: ArrowRightLeft },
] as const;

function openPalette() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }));
}

export default function AppShell() {
  const { shadow, setShadow } = useFindingsStore();
  const { status } = useConnectionStore();
  const { health, setHealth } = useSensorsStore();
  const { t, i18n } = useTranslation();
  const { pathname } = useLocation();
  const onBoard = pathname === '/';

  // Seed truth gate (design_plan §8): when the backend booted with
  // VERGE_SEED=demo the chrome must say so on every route — never silent.
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const h = await getSystemHealth();
        if (!cancelled) setHealth(h);
      } catch {
        /* offline — the pages surface their own error states */
      }
    };
    void load();
    const id = window.setInterval(load, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [setHealth]);

  const demoSeed = health?.seedMode === 'demo';

  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col font-sans select-none">
      {/* Top Header Navigation */}
      <header className="h-12 border-b border-line bg-panel flex items-center justify-between px-4 shrink-0 z-30 gap-4">
        <div className="flex items-center gap-4 min-w-0">
          <Link to="/" className="flex items-center shrink-0" aria-label="Verge home">
            <Logo size={22} />
          </Link>
          <span className="h-4 w-[1px] bg-line shrink-0" />
          <span className="text-micro text-ink-dim font-mono tracking-[0.14em] hidden xl:inline truncate">
            LEAD-TIME INTELLIGENCE · OPERATOR CONSOLE
          </span>
          {demoSeed && (
            <span
              className="text-micro font-mono uppercase tracking-[0.1em] text-ink-dim border border-dashed border-line-2 rounded-sm px-1.5 py-0.5 shrink-0 select-none"
              title="The backend booted with VERGE_SEED=demo — findings and plant data are a labeled demonstration, not live plant truth."
            >
              Demo seed
            </span>
          )}
        </div>

        {/* Global Navigation — editorial: 2px ink underline marks the active
            view; no chips, no fills (docs/design-system.md) */}
        <nav className="flex items-center gap-1 h-full" aria-label="Primary">
          {NAV.map(({ to, key, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-1.5 h-full px-2.5 text-xs font-medium border-b-2 -mb-px transition-colors duration-fast',
                  isActive
                    ? 'text-ink border-ink'
                    : 'text-ink-dim border-transparent hover:text-ink'
                )
              }
            >
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">{t(key)}</span>
            </NavLink>
          ))}
        </nav>

        {/* Right cluster: search, language, connection, mode */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={openPalette}
            className="hidden md:flex items-center gap-2 h-7 pl-2 pr-1.5 rounded border border-line bg-bg text-ink-dim hover:text-ink hover:border-line-2 transition-colors duration-fast text-xs cursor-pointer"
            aria-label="Open command palette"
          >
            <Search className="h-3 w-3" />
            <span className="font-sans">Search</span>
            <Kbd>⌘K</Kbd>
          </button>

          <select
            value={i18n.language}
            onChange={(e) => i18n.changeLanguage(e.target.value)}
            className="h-7 px-1 rounded border border-line text-micro bg-bg text-ink-dim hover:text-ink focus:outline-none font-mono cursor-pointer"
            aria-label="Language"
          >
            <option value="en">EN</option>
            <option value="hi">HI</option>
            <option value="ta">TA</option>
            <option value="te">TE</option>
            <option value="kn">KN</option>
          </select>

          <div className="flex items-center gap-1.5" title={`Stream ${status}`}>
            <span
              className={clsx(
                'h-1.5 w-1.5 rounded-full',
                status === 'connected' ? 'bg-ok' : status === 'reconnecting' ? 'bg-near animate-pulse' : 'bg-unknown'
              )}
            />
            <span className="text-micro font-mono text-ink-dim uppercase hidden sm:inline">{status}</span>
          </div>

          <span className="h-4 w-[1px] bg-line" />

          {/* Live / Shadow mode — active LIVE inverts to ink (the instrument's
              power switch); SHADOW is the orange-signal state */}
          <div className="flex bg-panel-2 border border-line p-0.5 rounded" role="group" aria-label="Mode">
            <button
              onClick={() => setShadow(false)}
              className={clsx(
                'px-2.5 h-6 text-micro font-mono font-medium uppercase rounded-sm transition-colors duration-fast cursor-pointer',
                !shadow ? 'bg-ink text-panel' : 'text-ink-dim hover:text-ink'
              )}
            >
              {t('live')}
            </button>
            <button
              onClick={() => setShadow(true)}
              className={clsx(
                'px-2.5 h-6 text-micro font-mono font-medium uppercase rounded-sm transition-colors duration-fast cursor-pointer',
                shadow ? 'bg-near/12 text-near border border-near/35' : 'text-ink-dim hover:text-near'
              )}
            >
              {t('shadow')}
            </button>
          </div>
        </div>
      </header>

      {/* Sensor health ribbon — Board / Map only (design_plan chrome rule) */}
      {onBoard && <SensorRibbon />}

      <DegradationBannerStrip />

      {/* Live Ops stage lives inside FindingsView (Board) — not a hideable chrome strip. */}

      {/* Shadow banner — a calm tinted well with ink text, not a shout.
          The micro-label carries the state; prose stays sentence case. */}
      {shadow && (
        <div className="bg-near/10 border-b border-near/25 py-1.5 px-4 flex items-baseline gap-2 select-text">
          <span className="text-micro font-mono uppercase tracking-[0.1em] text-near font-semibold shrink-0">
            Shadow mode
          </span>
          <span className="text-xs text-ink truncate">
            Surfacing forecasted findings that are recorded but not active in the live system.
          </span>
        </div>
      )}

      {/* Page Content Viewport — keyed page-settle: one 150ms rise per route
          enter (§13.2), never on data refresh */}
      <main className="flex-1 overflow-hidden relative">
        <div key={pathname} className="page-settle h-full">
          <Outlet />
        </div>
      </main>

      <CommandPalette />
      <Toaster />
    </div>
  );
}
