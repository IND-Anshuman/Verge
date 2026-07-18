# Verge Console UI Plan — Mission Control + Plant Copilot

**Status:** Planning (UI-first pause, 2026-07-19)  
**Visual system:** [`design-system.md`](./design-system.md) — Instrument Paper  
**Phase bookmark:** [`PHASED_BUILD_PLAN.md`](./PHASED_BUILD_PLAN.md) §0  

---

## 0. Hard rules (no hardcoded product fiction)

Every console surface follows P4. The UI plan **does not** include:

| Forbidden | Instead |
|---|---|
| Seed findings presented as live plant truth without `seedMode` label | Show `seedMode` / DEMO banner when `VERGE_SEED=demo`; empty board when off and no live ingest |
| Fake KPIs (TRIR, fatigue %, compliance %) | Null / “not measured” / omit |
| Hardcoded graph nodes, muster counts, bulletins | Live API only; empty-state copy when unconfigured |
| Invented citations or chat answers without corpus | Degraded answer + reason; never fabricate SOP text |
| Fake photo attach / fake radio ticker | Disabled control + honest reason until ingest path exists |
| Wallboard “demo numbers” | Harness-backed metrics only, or blank |

**Demo Pack** (optional offline rehearsal) is allowed only when explicitly labeled in chrome — never silent.

---

## 1. Two wedges → two primary surfaces

```text
┌─────────────────────────────────────────────────────────────┐
│  Header · nav · ⌘K · LIVE/SHADOW · stream · degrade strip   │
├──────────────────────────────┬──────────────────────────────┤
│  MISSION CONTROL  (/)        │  PLANT COPILOT  (/knowledge) │
│  Live Risk wedge             │  Living Knowledge wedge      │
│  map + board + now-strip     │  chat + ingest + citations   │
└──────────────────────────────┴──────────────────────────────┘
```

Secondary nav (not the hero): Replay · Fleet · Audit · Config · Handover.  
Mobile field is a constrained surface of the same two wedges (ack / ask / photo / muster).

---

## 2. Mission Control (`/`) — Live Risk

**One composition** (not a dashboard of equal cards):

| Region | Content | Data source |
|---|---|---|
| Map | Zones, adjacency, workers, finding tints by band | `/api/plant/graph`, findings, workers |
| Board | Findings by state; band edge + lead-time gauge + lineage chips | `/api/findings` (+ SSE) |
| Now-strip | Live chips: sensor ticks, Melia radio (English), vision hits | readings stream, `/api/voice/events`, `/api/vision/events` |

**Finding object** (full page preferred over modal-only):  
Live · Investigate · Knowledge · Graph · Respond — all bound to real APIs; Investigate shows orchestrator + validator disposition.

**Empty / degrade:** no findings → calm empty state. Speechmatics/Cognee/LLM down → one collapsed degrade strip (existing).

---

## 3. Plant Copilot (`/knowledge`) — AI chat + ingest

Yes — this is the **AI chat portion**. It is the Living Knowledge product surface, not a side panel afterthought.

### 3.1 Jobs (one page, three verbs)

1. **Ask** — grounded chat over plant corpus + Cognee memory (hybrid `/api/knowledge/ask`).  
2. **Ingest** — upload plant documents (SOP, WO, PDF, markdown) via `/api/docs/ingest` → DocIntel + Cognee cognify when configured.  
3. **Attach evidence** — field **photos** / stills (and later short clips) into the same corpus or finding-linked evidence store — honest empty until API path is ready; no fake attach.

### 3.2 Layout (target)

```text
┌──────────── corpus / attachments ────┬──────── Plant Copilot chat ──────────┐
│  Upload docs / photos                 │  Thread: user ↔ grounded answers     │
│  List: title · status · source        │  Each assistant turn:                │
│  Empty → CTA “Add plant documents”    │    answer + citation rail + sources  │
│                                       │  Composer: text (+ attach) + Ask     │
│  Filters: docs | photos | all         │  Degraded chip when LLM/corpus empty │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### 3.3 Chat contract (non-negotiable)

- Answers **only** from retrieved DocIntel chunks and/or Cognee memory (plus optional finding-scoped tools when opened from a finding).  
- Every answer shows **citations** (doc title / memory id) or an honest “cannot answer from corpus.”  
- Multi-turn thread in the UI; each turn still re-grounds (no silent memory of invented facts).  
- Finding-scoped mode: “Ask about this finding” pre-fills zone/title context via existing memory/investigate APIs — still cited.

### 3.4 Ingest contract

| Asset | Path | UI |
|---|---|---|
| SOP / PDF / MD / text | `POST /api/docs/ingest` → cognify hook | Drag-drop + file picker; status in corpus rail |
| Field photo (JPEG/PNG) | Evidence / docintel image path (wire next; today: honest disabled or ingest-as-doc when backend accepts) | Same upload well; type chip `photo` |
| Radio / voice clip | Melia → English ops → optional cognify (existing voice APIs) | Optional “Add voice note” on Copilot or Handover — not fake waveform |

### 3.5 What this is not

- Not a free-form ChatGPT about the plant with no sources.  
- Not Mission Control’s risk engine (P1 stays LLM-free).  
- Not a place to invent compliance scores.

---

## 4. Other surfaces (truthful, secondary)

| Route | Role |
|---|---|
| `/replay` | Time-travel fusion / eval story |
| `/fleet` | Multi-site; unmeasured metrics stay null |
| `/audit` | Hash chain + evidence |
| `/admin` | Sectioned Plant IT (ops, models, thresholds) — no equal-weight dump |
| `/handover` | Shift notes + voice transcript when Melia returns text |
| Wallboard (optional) | Dim, IMMINENT-first; same live APIs |
| Mobile | Ask Copilot · ack finding · photo evidence · muster |

---

## 5. Build order (after this plan is accepted)

1. **Plant Copilot v1** — elevate `/knowledge` to threaded chat UX + clearer ingest well (docs first; photos when API accepts images).  
2. **Mission Control composition** — map + board + now-strip (wire radio/vision chips to live events; no hardcode).  
3. **Finding object page** — tabs over modal.  
4. **Strip remaining fiction** — audit console for seed-unlabeled / null KPIs / disabled fakes.  
5. Pack switcher chrome when packs exist.

---

## 6. Success checks

- Blind tester asks a real ingested SOP question in Copilot and gets a **cited** answer in &lt;15s (or honest empty).  
- Blind tester understands a NEAR finding on Mission Control in &lt;30s.  
- With `VERGE_SEED=off` and no live ingest: board and corpus are empty — never fake-busy.  
- Photo control never claims success without a stored asset id.
