# Verge Design System — "Instrument Paper"

The console reads like an engineering document from a plant that takes safety
seriously: paper, ink, hairline rules, and exactly one signal color. No
gradients, no glassmorphism, no dark-dashboard clichés, no decoration that
isn't information.

## Lineage (researched, not vibes)

- **Anduril** — Swiss-modernist grid, monochrome discipline, color reserved
  for the subject itself. Their brand treats defense hardware with editorial
  restraint; we treat safety data the same way.
- **NASA Graphics Standards Manual, 1976 (Danne & Blackburn)** — "unity,
  technological precision." One signal color with strict usage rules; ruled
  section headers; standardization as a virtue. Verge's signal orange plays
  the role NASA Red played.
- **Braun (Rams) → Teenage Engineering** — instrument-panel functionalism:
  matte neutral hardware, selective orange accents that always MEAN something
  (record, warning, power). *Weniger, aber besser.*

## Tokens

### Surfaces (warm paper neutrals)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#F4F3F0` | canvas (paper) |
| `--panel` | `#FFFFFF` | cards, header, table rows |
| `--panel-2` | `#ECEBE7` | wells, insets, hover fills, chips |
| `--line` | `#DEDCD5` | hairline rules (1px, everywhere) |
| `--line-2` | `#C6C3BA` | hover borders, strong rules |
| `--ink` | `#16181C` | primary text, primary buttons |
| `--ink-dim` | `#6E7178` | secondary text, micro-labels |
| scrim | `rgba(22,24,28,.34)` | modal/palette overlay |

### Signal (color only ever means state)
| Token | Value | Meaning |
|---|---|---|
| `--accent` | `#D9480F` | THE brand signal — Verge orange. Logo dot, focus ring, active accents. Same family as NEAR: the brand mark *is* the early-warning band. |
| `--imminent` | `#C92A2A` | <15 min band, breach, danger |
| `--near` | `#D9480F` | 15–45 min band |
| `--watch` | `#1864AB` | >45 min band |
| `--ok` | `#2B8A3E` | healthy, verified, accounted |
| `--unknown` | `#868E96` | insufficient signal (honest gray) |

Tints = band color at 8–12% over white. Never gradients.

### Categorical chart palette (series identity ≠ status)
`#5B8DEF → #22997E → #9D7BD8 → #D0638F → #8A9B3F` — fixed order, never
cycled. Machine-validated (OKLCH lightness band, chroma floor, CVD adjacent
separation, ≥3:1 contrast) on **both** `#FFFFFF` and `#16181C`. Grid
`#ECEAE4`, axes `#8A8D94`, tooltips: white, hairline, ink text.

### Type
- **IBM Plex Sans** (self-hosted): all UI text. Titles 600, body 400/500.
- **IBM Plex Mono**: data only — IDs, readings, timestamps, tick labels,
  micro-labels. Never for prose or titles.
- Micro-label: 10px mono, uppercase, tracking 0.08–0.14em, `--ink-dim`.
  This is the ONLY sanctioned uppercase. Everything else sentence case.
- Numerals always `tabular-nums`.

### Geometry & elevation
- Radii: 2 / 4 / 6 / 8 px (sharp, technical). Pills only for count chips.
- Elevation = borders. The ONLY shadow in the system is the floating-layer
  shadow (`0 8px 24px rgba(22,24,28,.10)`) on modal, palette, toasts,
  popovers — everything else sits flat on the paper.
- Hover = border lightens `--line` → `--line-2`; never scale, never shadow.
- Ruled headers: micro-label followed by a hairline that runs to the edge —
  the drawing-title-block motif (`.ruled-label`).

### Motion
- 150ms ease color/border transitions; buttons press `scale(0.98)`.
- The annunciator pulse remains reserved EXCLUSIVELY for IMMINENT.
- `prefers-reduced-motion` kills everything.

## Surface-by-surface

- **Header (48px, white, hairline bottom):** logo (ink strokes + orange dot),
  hairline divider, micro tagline. Nav = text items with a 2px ink underline
  on active (editorial, not chips). Right: search chip (⌘K), language, stream
  dot, LIVE/SHADOW segmented control — active LIVE is ink-on-white inverted;
  active SHADOW is orange-tinted.
- **Sensor ribbon (32px, well):** single line, truncates, never wraps.
  Audit chip = ok-tinted. Degradation banners = near-tinted wells with
  hairlines, ink text.
- **Board:** columns transparent on paper, hairline-bounded, 2px band-colored
  top rule, micro-label headers + white count chips. Cards white with 3px
  band edge; title 600 ink; gauge tints on white; footer actions ghost until
  card hover.
- **LeadTimeGauge (light):** zone tints 0.15 inactive / 0.45 active band,
  extent underline 0.7, breach end-stop solid imminent, hollow gray UNKNOWN.
- **Map:** field `#E9E7E1`, zones white with `#D8D5CE` outlines, band-tinted
  fills when findings are live; chrome cards white/95; worker chips white.
- **Modal / ⌘K palette / toasts:** white, hairline, floating shadow, ink scrim.
- **Charts:** categorical palette above; status colors appear ONLY as
  threshold/alert reference lines; legends always; recessive grid.
- **Buttons:** primary = ink bg / paper text (color is signal, so the primary
  action is *black*); secondary = white + hairline; ghost = dim→ink;
  danger = imminent tint. Focus ring = accent.
- **Empty/loading:** dashed hairline EmptyState (icon + one calm line);
  content-shaped Skeletons. Never bare text.

## Hard rules

1. One signal color. Orange never decorates; it warns or brands.
2. No gradients. No glassmorphism. No shadows except the floating layer.
3. Uppercase only in micro-labels. Mono only for data.
4. Status colors never become chart series.
5. Every number is tabular. Every rule is 1px. Every surface is a token.
