# Ash — UI notes: references studied & decisions taken

Scope: `apps/console/**` only. System of record: `docs/design-system.md`
("Instrument Paper"). These notes record what I studied before touching CSS,
and the specific discipline each reference contributes. Steal discipline,
not skins.

---

## References actually studied

### 1. NASA Graphics Standards Manual, 1976 (Danne & Blackburn)
The manual's power is *standardization as a virtue*: one signal red, ruled
section headers, a fixed grid that makes every page feel like the same
organization produced it. What I'm taking: the **ruled micro-label** is the
atom of hierarchy — every section on every surface opens the same way, so
the operator's eye learns one grammar. Uppercase is rationed to those labels
and nowhere else.

### 2. Anduril — Lattice / brand site
Swiss-modernist grid, near-total monochrome, color reserved for the subject
itself (a track, a threat, a detection). Nothing on the chrome competes with
the data. What I'm taking: **chrome recedes, state advances** — nav, panels
and buttons stay ink/paper; the only saturated pixels on a Verge screen must
be band state or the brand dot. Also their density: small type, generous
rules, no padding inflation.

### 3. Linear — app chrome, ⌘K, empty states
Linear's tightness comes from three things: a command menu that contains
*everything* reachable, empty states that are designed rather than apologized
for, and row heights that never wobble. What I'm taking: the **palette must
be a complete map of the product** (ours was missing the Knowledge view —
that's a trust break), fixed row heights in list surfaces, and one-line calm
empty copy.

### 4. Braun (Rams) → Teenage Engineering — instrument functionalism
On a TE device, orange is never a theme — it's the record button. Matte
neutral hardware everywhere else. What I'm taking: **orange budget** — audit
every surface and remove orange that decorates instead of warns (e.g. active
tab underlines can be ink; orange stays for SHADOW mode, focus, and the
logo dot). Motion behaves the same way: one annunciator pulse, reserved for
IMMINENT, nothing else moves on the board.

### 5. Palantir Foundry / AIP — investigation workspace
Foundry treats an entity page as a *cockpit*: identity and disposition pinned,
evidence and lineage in stable regions, actions grouped and explicit — never
a modal that feels like a form. What I'm taking: the finding detail modal
becomes an **investigation surface**: sticky identity header (ID, zone, band
tape), left rail = disposition facts, right = evidence tabs whose IA reads
complete even when a tab is thin. The counterfactual — our differentiator —
gets first-class typographic treatment, not an italic afterthought.

Supporting scan: Stripe Dashboard (tables that never shout), Garmin EFIS
(annunciators mean state; no alarm theater), Siemens/AVEVA operator screens
(what to improve: information hierarchy exists but typography is undisciplined
— we keep their honesty about degraded data, fix the type).

---

## Three concrete decisions brought into Verge

1. **One grammar of sections everywhere.** Every surface (board columns,
   detail rail, knowledge corpus, handover steps) opens with the same
   `.ruled-label` micro-label + hairline. Page headers standardize to
   sentence-case Plex Sans 600 with a one-line dim subtitle — no more
   uppercase-mono h1s on some pages and sentence case on others.

2. **Orange budget + calm degradation.** Color = state, so degradation
   banners become near-tinted wells with **ink text** (per the design law)
   instead of full-color shouting; nav active state is ink underline; the
   loading fallback drops the generic spinner island for a paper-and-rule
   skeleton. Uppercase survives only in micro-labels.

3. **Detail = cockpit, Knowledge = one composition.** Finding detail gets a
   sticky identity header, a disposition rail, and a complete evidence IA
   (Signals / Investigate / Lineage / Audit) with the counterfactual set
   large under its own ruled label. Knowledge stops being three random cards:
   a corpus rail (upload affordance always visible, honest empty state) beside
   an ask→answer→citations column where citations read as numbered mono-ID
   excerpts. Busy states are told apart (uploading ≠ asking) so buttons never
   lie about what the system is doing.

---

# Revision — 2026-07-18 type/color/size pass (post-audit)

Arjun's audit was right: the first pass reorganized panels but left the
pixels reading as a small-type cream SaaS board. This pass fixed tokens,
scale, and the orange budget. Verified with DevTools computed styles, not
by eyeballing.

## Token deltas (index.css + tailwind.config.js + design-system.md, all synced)

| Token | Was | Now |
|---|---|---|
| `--bg` | `#F4F3F0` (warm cream) | `#F0F1EF` (cold paper) |
| `--panel-2` | `#ECEBE7` | `#E8E9E4` |
| `--line` / `--line-2` | `#DEDCD5` / `#C6C3BA` | `#D5D6D0` / `#B4B5AE` |
| `--ink` / `--ink-dim` | `#16181C` / `#6E7178` | `#121417` / `#5C6068` |
| root font-size | 13px | 14px |
| type scale | xs 11 · sm 12 · base 13 · md 14 · lg 16 · xl 18 | xs 12 · sm 13 · base 14 · md 15 · lg 18 · xl 22 |
| spacing | rem-drift above 32px | px-locked through `h-12` (48px) |

## Before/after (measured, API up)

1. **Card title 12px → 14px/600 Sans ink** (`FindingCard h3` computed
   `14px · 600 · IBM Plex Sans · rgb(18,20,23)`); metadata row now 12px mono,
   clearly secondary. Hover = underline + chevron darkens — the
   `hover:text-accent` is gone (`hover:text-accent` count on `/`: 0).
2. **Three stacked DEGRADED bars → one collapsed 28px strip** reading
   `Degraded · 3` + first reason in ink; severity colors only the signal
   word; the full list is a click away. Chrome recedes again.
3. **Orange budget enforced**: lineage icons all ink-dim, counterfactual rule
   is `--line-2` with the emphasis carried by 15px medium ink type, state
   dots ink, selection states (assign/snooze/replay/map layers) are
   ink-bordered, export/mic/bot glyphs neutral. Remaining orange on screen:
   logo dot, focus ring, band tape/edges, SHADOW control, danger signal
   words — the sanctioned five.

Also: zero `uppercase font-mono` page titles remain (Audit, Replay, Admin
now `text-lg font-semibold` Sans, computed 18px); panel drag-handles keep
uppercase only as true micro-labels and their microcopy stopped shouting
("TELETREAD ALERTS BOARD" → "Findings board"); route fallback is now shaped
like the route it loads (board columns on `/`, corpus+ask on `/knowledge`).

## Honesty — what still isn't award-level

- **The Plex Mono ribbon line and permit rows** still carry a lot of mono at
  12px; it's data so it's legal, but the permits panel reads dense and could
  use the Fact-row treatment the cockpit got.
- **`FindingsView` chunk is 1.28 MB** (maplibre + recharts in one lazy
  chunk) — first paint of `/` leans hard on the skeleton. Needs a
  manualChunks split; not a CSS problem but it is a perceived-speed problem.
- **Mobile board** got title sizing but not a real one-thumb audit on
  hardware; swipe-to-ack thresholds are untested on touch.
- Screenshots: the in-app browser can't capture the WebGL map view
  (screenshot timeouts), so this pass is verified via computed styles and
  DOM reads; before/after captures need a manual pass.
