/* Chart theme — one system for every Recharts surface.

   CHART_SERIES is the categorical palette for series identity (sensors,
   plants, …): fixed order, never cycled, validated for the dark surface
   #12161D (OKLCH lightness band, chroma floor, CVD adjacent-pair separation,
   3:1 contrast — scripts/validate_palette.js, all PASS). Status colors
   (imminent/near/watch/ok) are reserved for state and are NOT series colors —
   the one sanctioned status use in a chart is a threshold/alert reference
   line. Grid and axes are recessive: data owns the ink. */

export const CHART_SERIES = ['#5B8DEF', '#2FA98C', '#9D7BD8', '#D0638F', '#8A9B3F'] as const;

export const seriesColor = (i: number) => CHART_SERIES[i % CHART_SERIES.length];

export const CHART_GRID = '#1B222C'; // subtler than --line: recessive by design
export const CHART_AXIS = '#5F6B78';

export const chartTooltipStyle = {
  backgroundColor: '#12161D',
  border: '1px solid #262E39',
  borderRadius: 6,
  fontSize: 11,
  fontFamily: "'IBM Plex Mono', monospace",
  color: '#E8EDF4',
  padding: '6px 10px',
} as const;

export const chartAxisProps = {
  stroke: CHART_AXIS,
  tickLine: false,
  axisLine: { stroke: CHART_GRID },
  fontSize: 10,
} as const;
