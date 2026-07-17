import { Search, AlertCircle } from 'lucide-react';
import { useFindingsStore } from '@/stores/findings';
import { Button } from '@/components/atoms';
import type { LeadTimeBand } from '@/types';
import clsx from 'clsx';

const BANDS: { value: LeadTimeBand; label: string }[] = [
  { value: 'IMMINENT', label: 'IMMINENT' },
  { value: 'NEAR', label: 'NEAR' },
  { value: 'WATCH', label: 'WATCH' },
  { value: 'UNKNOWN', label: 'UNKNOWN' },
];

export function FindingFilters() {
  const { filters, setFilters } = useFindingsStore();

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({
      ...filters,
      search: e.target.value || undefined,
    });
  };

  const toggleBand = (band: LeadTimeBand) => {
    const activeBands = filters.leadTimeBands || [];
    const isAlreadyActive = activeBands.includes(band);

    const updatedBands = isAlreadyActive
      ? activeBands.filter((b) => b !== band)
      : [...activeBands, band];

    setFilters({
      ...filters,
      leadTimeBands: updatedBands.length > 0 ? updatedBands : undefined,
    });
  };

  const toggleDegraded = () => {
    setFilters({
      ...filters,
      confidenceDegraded: filters.confidenceDegraded === undefined ? true : undefined,
    });
  };

  const clearFilters = () => {
    setFilters({});
  };

  const hasActiveFilters =
    filters.search ||
    filters.leadTimeBands?.length ||
    filters.confidenceDegraded !== undefined;

  return (
    <div className="flex flex-wrap items-center gap-3 w-full max-w-4xl select-none">
      {/* Search Input */}
      <div className="relative w-64">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-dim/40 pointer-events-none">
          <Search className="h-4 w-4" />
        </span>
        <input
          type="text"
          placeholder="Filter by title, zone, ID..."
          value={filters.search || ''}
          onChange={handleSearchChange}
          className={clsx(
            'h-8 pl-8 pr-3 rounded border text-xs bg-panel-2 text-ink w-full',
            'transition-colors duration-fast border-line placeholder:text-ink-dim/40',
            'focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent'
          )}
        />
      </div>

      {/* Lead Time Band Filter Toggles */}
      <div className="flex items-center gap-1.5 bg-panel-2 p-0.5 rounded border border-line">
        <span className="text-micro font-mono text-ink-dim px-2 select-none uppercase font-bold">
          BAND:
        </span>
        {BANDS.map((b) => {
          const isActive = filters.leadTimeBands?.includes(b.value);
          return (
            <button
              key={b.value}
              onClick={() => toggleBand(b.value)}
              className={clsx(
                'h-6 px-2 text-micro font-mono font-bold rounded-sm transition-all cursor-pointer border',
                isActive
                  ? b.value === 'IMMINENT'
                    ? 'bg-imminent/10 border-imminent/30 text-imminent'
                    : b.value === 'NEAR'
                    ? 'bg-near/10 border-near/30 text-near'
                    : b.value === 'WATCH'
                    ? 'bg-watch/10 border-watch/30 text-watch'
                    : 'bg-unknown/10 border-unknown/30 text-unknown'
                  : 'bg-transparent border-transparent text-ink-dim hover:text-ink hover:bg-panel'
              )}
            >
              {b.label}
            </button>
          );
        })}
      </div>

      {/* Degraded Confidence Filter Toggle */}
      <button
        onClick={toggleDegraded}
        className={clsx(
          'h-8 px-3 rounded border text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer',
          filters.confidenceDegraded !== undefined
            ? 'bg-imminent/10 border-imminent/30 text-imminent'
            : 'bg-panel-2 border-line text-ink-dim hover:text-ink hover:border-line/75'
        )}
      >
        <AlertCircle className="h-3.5 w-3.5" />
        DEGRADED ONLY
      </button>

      {/* Clear Filters action */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="h-8 text-xs text-ink-dim hover:text-ink font-semibold"
        >
          Reset Filters
        </Button>
      )}
    </div>
  );
}
