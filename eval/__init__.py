"""Verge eval harness — replay-provable evidence (spec §10).

The harness replays a reconstructed incident, runs Verge alongside three
baselines (B0 fixed-threshold, B1 rate-of-rise, B2 multi-sensor AND-gate), and
reports who caught what, at which lead-time band, and how far ahead of breach.

Methodological honesty (spec §10): these replays are *reconstructions* from
public narrative reports, not per-sensor ground truth. The harness is a strong
demo and a regression test — not unbiased proof. The first unbiased number comes
from a pilot plant's own history (Horizon 1).
"""

# Dev-time path bootstrap. Importing the `eval` package (which always happens
# before eval.harness on `python -m eval.harness`) wires the in-repo packages
# onto sys.path so the harness's top-level verge imports resolve without install.
# Kept here (not in harness.py) so ruff's import sorting can't reorder it after
# the verge imports it must precede.
import sys as _sys
from pathlib import Path as _Path

_ROOT = _Path(__file__).resolve().parents[1]
for _rel in ("packages/schema", "services/forecaster", "services/risk-engine"):
    _p = str(_ROOT / _rel)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
