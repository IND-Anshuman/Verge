/* Chart theme — one system for every Recharts surface.

   CHART_SERIES is the categorical palette for series identity (sensors,
   plants, …): fixed order, never cycled, validated on BOTH
   surfaces — paper #FFFFFF and ink #16181C (OKLCH lightness band, chroma floor, CVD pair separation,
   3:1 contrast — scripts/validate_palette.js, all PASS). Status colors
   (imminent/near/watch/ok) are reserved for state and are NOT series colors —
   the one sanctioned status use in a chart is a threshold/alert reference
   line. Grid and axes are recessive: data owns the ink. */

export const CHART_SERIES = ['#5B8DEF', '#22997E', '#9D7BD8', '#D0638F', '#8A9B3F'] as const;

export const seriesColor = (i: number) => CHART_SERIES[i % CHART_SERIES.length];

export const CHART_GRID = '#ECEAE4'; // subtler than --line: recessive by design
export const CHART_AXIS = '#8A8D94';

export const chartTooltipStyle = {
  backgroundColor: '#FFFFFF',
  border: '1px solid #DEDCD5',
  borderRadius: 4,
  boxShadow: '0 8px 24px rgba(22,24,28,0.10)',
  fontSize: 11,
  fontFamily: "'IBM Plex Mono', monospace",
  color: '#16181C',
  padding: '6px 10px',
} as const;

export const chartAxisProps = {
  stroke: CHART_AXIS,
  tickLine: false,
  axisLine: { stroke: CHART_GRID },
  fontSize: 10,
} as const;
