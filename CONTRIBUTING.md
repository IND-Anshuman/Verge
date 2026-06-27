# Contributing to Verge

## Dev setup

Python 3.11+. The workspace runs from a checkout without install — a root
`conftest.py` wires the in-repo packages onto `sys.path`.

```bash
pip install pydantic pyyaml httpx "fastapi>=0.111" uvicorn pytest ruff
pytest -q          # whole workspace (55+ tests)
ruff check .       # lint
make eval          # run the replay harness vs B0/B1/B2
```

For the full stack: `make up` (docker compose) then `make api` + the console.

## Non-negotiable invariants (enforced in review + the PR template)

1. **P1 — the safety core never depends on the LLM.** `risk-engine` and
   `forecaster` must import nothing from `verge_llm`. The LLM degrades, never
   raises into detection.
2. **P5 — no hand-edited numbers.** Any metric in docs/decks must be reproduced
   by `make eval`. If the number isn't impressive, fix the system, not the slide.
3. **P8 — advisory only.** No code writes to OT/control/permit systems, triggers
   ESD, or auto-suppresses a finding. The operator is the interlock.
4. **P3 — lineage.** Every finding carries `lineage` + `contributingSignals`.
5. **Schema is the contract.** Changes to `packages/schema` must be mirrored in
   `packages/schema/js/index.ts`.

## Commit style

Conventional-ish: `feat(scope): …`, `fix(scope): …`, `chore: …`, `ci: …`.
Keep commits small and green (`pytest` + `ruff` pass on each).

## Adding a replay (eval)

1. Create `eval/replays/<id>/generate.py` documenting the synthesis assumptions
   (these are reconstructions, not ground truth — say so).
2. Emit `events.jsonl`, `ground-truth.json`, `feedback.jsonl`.
3. `python -m eval.harness --incident <id>` and confirm Verge's lead vs B0/B1/B2.
