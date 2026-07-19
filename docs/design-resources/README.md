# Design resources — premium craft references

**Purpose:** Concrete visual references backing §13 of [`design_plan.md`](../design_plan.md)
("Premium craft escalation"). This folder is the handoff package for whoever
builds the visual layer (Figma / Stitch) — every image here has an explicit
verdict, not just a vibe.

Do not treat this folder as a moodboard to reproduce wholesale. Two of the
four references are here to be **rejected in part** — see verdicts below.

## Inventory

| File | Source | Verdict | Why |
|---|---|---|---|
| `inspiration/anduril-command-control-page.png` | anduril.com/lattice/command-and-control | **Adopt as north star** | Cold dot-matrix paper canvas, huge sentence-case editorial headline, uppercase micro-label category tag ("LATTICE," "COMMAND AND CONTROL"), pure monochrome ink — this *is* `design-system.md`'s Instrument Paper direction, confirmed at Awwwards-adjacent production quality. Premium reads through typographic confidence and restraint, not decoration. |
| `inspiration/teenage-engineering-home.png` | teenage.engineering | **Adopt selectively** | Confident oversized type, hairline icon marks, one orange accent used exactly once for emphasis ("BUSY" sign) — same "weniger, aber besser" discipline as the design-system.md lineage. Ignore the illustration/mascot layer; it's a consumer-brand device Verge shouldn't borrow. |
| `inspiration/ai-chat-metallic-widgets-cover.png` | Figma Community — "AI Chat Metallic Widgets" (user-supplied) | **Adopt narrowly, for hero instruments only** | The brushed-chrome sphere with a real specular highlight and the glossy black input surface are genuine tactile craft — Braun/Teenage-Engineering "instrument panel" made literal. Use this *material* language only on the one or two most important physical-feeling controls (e.g. the lead-time gauge dial, an IMMINENT alert orb, a physical-feeling toggle) — never as a full-surface reskin. Everywhere else stays flat Instrument Paper; if every panel goes glossy-metallic it stops meaning anything (violates D3 — signal is sacred). |
| `inspiration/financial-global-payment-cover.png` | Figma Community — "Financial Global Payment Website" (user-supplied) | **Reject the surface, note the ambition** | Neon purple/blue/pink gradients, glow, dark-glassmorphism ribbon graphic — this is precisely the "dark-cyber cliché" `design_plan.md` §4 already lists as an anti-pattern, and it uses color as decoration rather than signal (violates D2, D3). Kept in this folder only as a labeled *contrast reference*: what "premium" does NOT mean for Verge. The ambition to look expensive is right; gradients/glow is the wrong tool for an industrial-safety product where color must stay reserved for lead-time/danger state. |

## The synthesis (what actually changes)

"Premium" for Verge is earned through **craft depth**, not chrome:
- Typographic confidence (bigger, more confident headline moments — see §13.1)
- A real, specified motion system (§13.2) instead of ad hoc transitions
- Data-viz that's edited, not just plotted (§13.3)
- Exactly one or two components with genuine tactile/material rendering (§13.4),
  spent on the things that deserve attention — never spread thin across every card.

Full detail lives in `design_plan.md` §13.
