"""Unified live runtime: gas rules + SIMOPS conflicts + plant model + shadow mode.

Composes risk-engine (run_stream) with the permit SIMOPS detector and the twin
plant model — the same wiring the `python -m verge_risk` CLI uses.
"""

from verge_permit import conflict_findings
from verge_risk import STARTER_RULES, load_rules, run_stream
from verge_sims import simops_demo, vizag_like
from verge_twin import load_plant

RULES = load_rules(STARTER_RULES)
PLANT = load_plant()


def _simops_detector(adjacency):
    def detect(state):
        return conflict_findings(state.permits, adjacency=adjacency, now=state.now, at=state.now)

    return detect


def test_plant_supplies_thresholds_and_adjacency() -> None:
    assert PLANT.thresholds_by_kind() == {"gas-lel": 100.0, "gas-co": 50.0}
    assert "B-05" in PLANT.adjacency()["B-04"]


def test_simops_conflict_surfaces_from_live_stream() -> None:
    findings = []
    run_stream(
        simops_demo().events(), RULES, findings.append,
        thresholds=PLANT.thresholds_by_kind(),
        detectors=[_simops_detector(PLANT.adjacency())],
    )
    simops = [f for f in findings if f.title.startswith("SIMOPS conflict")]
    assert simops, "the hot-work + confined-space SIMOPS conflict must surface"
    f = simops[0]
    assert f.confidence >= 0.8
    assert f.lineage == ["permit:PW-HW-21", "permit:PW-CS-22"]  # both permits (P3)
    assert f.lead_time_band == "UNKNOWN"  # permits are not a rate-to-threshold process


def test_gas_and_simops_coexist_and_dedup() -> None:
    findings = []
    run_stream(
        simops_demo().events(), RULES, findings.append,
        thresholds=PLANT.thresholds_by_kind(),
        detectors=[_simops_detector(PLANT.adjacency())],
    )
    kinds = {("simops" if f.title.startswith("SIMOPS") else "gas") for f in findings}
    assert {"simops", "gas"} <= kinds  # both detectors contribute
    keys = [(f.zone_id, tuple(sorted(f.lineage))) for f in findings]
    assert len(keys) == len(set(keys))  # deduped by zone + lineage


def test_shadow_mode_tags_every_finding() -> None:
    live, shadow = [], []
    run_stream(vizag_like().events(), RULES, live.append,
               thresholds=PLANT.thresholds_by_kind())
    run_stream(vizag_like().events(), RULES, shadow.append,
               thresholds=PLANT.thresholds_by_kind(), shadow=True)
    assert live and shadow
    assert all(f.shadow is False for f in live)
    assert all(f.shadow is True for f in shadow)
