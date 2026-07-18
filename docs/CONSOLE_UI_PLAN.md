# Verge Console UI Plan

**Status:** Planning (UI-first pause, 2026-07-19)  
**Visual system:** [`design-system.md`](./design-system.md) — Instrument Paper  
**Phase bookmark:** [`PHASED_BUILD_PLAN.md`](./PHASED_BUILD_PLAN.md) §0  

**Design intent:** Separate pages with **one clear job** each. Elegant, calm, useful — not a single mega-dashboard that merges map, chat, graph, admin, and radio into one screen.

---

## 0. Product principles for UI

1. **One job per page** — if a section needs its own headline and mental model, it is its own route (or a full finding page), not a panel bolted onto Mission Control.  
2. **Visually meaningful** — space, type hierarchy, and Instrument Paper restraint; orange only for real lead-time / danger signal.  
3. **User-friendly** — short paths: see risk → open finding → act; or open Copilot → ask / upload. No training required for the happy path.  
4. **Useful** — every control binds to a live API or is honestly disabled.  
5. **No hardcoded fiction** — see §1.

---

## 1. Hard rules (no hardcoded product fiction)

| Forbidden | Instead |
|---|---|
| Seed findings as live truth without label | `seedMode` / DEMO chrome when seeding; empty when off |
| Fake KPIs (TRIR, fatigue %, compliance %) | Null / “not measured” / omit |
| Hardcoded graph nodes, muster counts, bulletins | Live API only; calm empty state |
| Invented chat answers / citations | Degraded + reason |
| Fake photo attach or fake radio ticker | Disabled + reason until real asset/event ids exist |
| Wallboard “demo numbers” | Harness-backed or blank |

---

## 2. Information architecture — separate surfaces

Primary nav stays light. Each route owns one job:

| Route | Job (one sentence) | What belongs here | What does **not** |
|---|---|---|---|
| **`/` Board** | See and triage live risk findings | Lead-time board, filters, open finding | Map chrome dump, chat, admin, graph explorer |
| **`/map`** *(or map as Board’s optional focus mode — not a third dump)* | Spatial situation | Twin map, zone select → filters board / opens finding | Chat, corpus, compliance tables |
| **`/findings/:id`** | Understand and act on **one** finding | Live context · Investigate · linked Knowledge ask · Respond | Site-wide chat history, plant-wide graph |
| **`/knowledge` Plant Copilot** | Ask the plant’s documents; grow the corpus | Threaded cited chat + ingest (docs / photos) | Risk board columns, sensor ribbon as main UI |
| **`/graph`** | Explore plant relationships | Live twin / Neo4j drill-in | Finding triage, free chat |
| **`/handover`** | Shift continuity | Notes + Melia transcript when available | Full Copilot corpus management |
| **`/replay`** | Prove / rehearse a story | Replay + eval linkage | Live ops triage |
| **`/audit`** | Evidence & integrity | Hash chain, packs | Risk board |
| **`/fleet`** | Multi-site glance | Honest nulls where unmeasured | Fake bulletins |
| **`/admin`** | Plant IT config | Sectioned ops / models / thresholds | Operator Mission Control |

**Shared chrome only (every page):** logo, nav, ⌘K, LIVE/SHADOW, stream dot, one collapsed degrade strip, sensor ribbon if it helps that page (Board/Map yes; Copilot/Audit no — keep Copilot visually quiet).

---

## 3. Board (`/`) — Live Risk triage

**Not** “map + board + now-strip + emergency + permits + chat” stacked.

**Default Board layout (elegant):**
- Full-height **findings board** (states / bands).  
- Optional **split**: board primary + **narrow map** (or “Map” toggle that expands map without burying the board).  
- Finding click → **`/findings/:id`** (full page), not a kitchen-sink modal.

**Live awareness without clutter:**
- Sensor ribbon stays in chrome (one line).  
- Radio / vision: small **count chips** or “latest event” link on Board that deep-links to finding lineage or a lightweight Events drawer — **not** a permanent ticker wall competing with the board.

Emergency / permits: open from Board actions or finding Respond — not permanent equal-weight side panels on the home screen.

---

## 4. Finding page (`/findings/:id`) — depth without home-screen merge

One finding, clear tabs (or ruled sections), sequential reading:

| Section | Job |
|---|---|
| **Summary** | Band, zone, title, lineage chips |
| **Live** | Telemetry / permits / exposure for this finding |
| **Investigate** | Orchestrator brief + specialists + validator |
| **Ask** | Copilot scoped to this finding (deep-link into `/knowledge?finding=…`) — not a second full corpus UI |
| **Respond** | Ack, barriers, alert, CAPA, emergency |

No requirement to show plant-wide graph or full corpus on this page — links out to `/graph` and `/knowledge` when needed.

---

## 5. Plant Copilot (`/knowledge`) — AI chat + ingest (own world)

A **dedicated** Living Knowledge page. Calm, document-forward, chat-forward — not attached under the risk board.

### Jobs
1. **Ask** — threaded, grounded chat (`/api/knowledge/ask`).  
2. **Ingest** — docs (SOP/PDF/MD) and field photos when the API stores a real id.  
3. **Browse corpus** — what was ingested; status; open citation source.

### Layout
```text
┌── Corpus (secondary) ──┬──────── Chat (primary) ────────────┐
│ Upload · list · filter │ Thread + citations per turn         │
│                        │ Composer                            │
└────────────────────────┴─────────────────────────────────────┘
```

Chat is the visual focus; corpus rail supports it. No map, no finding columns, no IMMINENT pulse here unless a linked finding chip is in context.

### Contract
- Cited or honest “cannot answer.”  
- Not ChatGPT-about-the-plant with no sources.  
- Not the P1 risk engine.

---

## 6. Graph (`/graph`) — its own exploration room

Live, filterable twin/Neo4j. Click node → object or finding.  
**Do not** embed a full graph canvas on Board home.

---

## 7. Craft bar (elegant + useful)

- Instrument Paper: cold canvas, hairline rules, IBM Plex, orange = signal only.  
- Generous whitespace on Copilot and Finding pages; Board can be denser (ops triage) without becoming a panel mall.  
- Motion budget: IMMINENT pulse, map fly-to on finding open, citation highlight — then stop.  
- Mobile: separate flows (list → finding; Copilot ask; photo; muster) — not a shrunk mega-dashboard.

---

## 8. Build order

1. **Clarify routes** — Board home stays triage-first; Finding full page; Copilot elevated chat UX; Graph as own route if not already first-class.  
2. **Remove panel sprawl from `/`** — emergency/permits/admin-like blocks leave the home composition.  
3. **Plant Copilot v1** — threaded chat + ingest well (docs; photos when API ready).  
4. **Finding page** — replace modal-as-only-depth.  
5. Fiction audit pass on remaining views.

---

## 9. Success checks

- New operator triage a NEAR finding from Board → Finding page in &lt;30s without opening Copilot or Graph.  
- New operator asks a cited SOP question on Copilot in &lt;15s without seeing the risk board.  
- Home screen does not require scrolling through chat, graph, and admin to see findings.  
- `VERGE_SEED=off` + no ingest → empty Board and empty corpus — never fake-busy.
