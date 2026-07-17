# Ash — Task 1: Console UI/UX craft

**Owner:** Ash  
**Status:** **PASSED re-audit 2026-07-18 — pushed to `main`**  
**Workspace:** `C:\Users\arjun\Desktop\Economic-Times\Verge`  
**Scope:** `apps/console/` + `docs/design-system.md`

---

## Re-audit result (Arjun / agent, measured)

| Gate | Result |
|---|---|
| Finding card title ≥ 14px | **PASS** — computed `14px / 600 / IBM Plex Sans` |
| Page `h1` ≥ 18px Sans sentence-case | **PASS** — Knowledge `18px`; Audit/Replay fixed |
| No `hover:text-accent` on titles | **PASS** — count 0 on `/` |
| Lineage icons ink-dim (no rainbow) | **PASS** |
| Degradation = one collapsed strip | **PASS** — `DEGRADED · 3` + expand |
| Paper cooler than cream `#F4F3F0` | **PASS** — `--bg #F0F1EF` / `rgb(240,241,239)` |
| typecheck + build | **PASS** |
| Backend untouched | **PASS** (console API client stringify fix only) |

Notes in `apps/console/ASH_UI_NOTES.md` revision section are accurate.

### Still polish (not blocking)
- Secondary surfaces still use some `uppercase` micro on export/panel chrome — legal if micro-label, watch density on permits/ribbon
- FindingsView chunk ~1.28 MB — split later
- Mobile one-thumb pass still open

**No further Task-1 instructions required.** Optional follow-ups only if Arjun opens a Task 2.
