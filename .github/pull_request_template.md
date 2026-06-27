## What & why

<!-- One paragraph. Link the spec section (e.g. §4.2) this advances. -->

## Checklist

- [ ] `pytest -q` green (whole workspace)
- [ ] `ruff check .` clean
- [ ] If a metric changed, the **eval harness reproduces it** (`make eval`) — no
      hand-edited numbers (spec §10, P5)
- [ ] No new dependency from the safety core (`risk-engine`) on the LLM (P1)
- [ ] No automated write to OT/control/permit systems; advisory only (P8)
- [ ] Schema changes mirrored in `packages/schema/js/index.ts`
