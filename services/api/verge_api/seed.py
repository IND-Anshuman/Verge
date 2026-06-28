"""A small in-memory seed so the console and the demo have findings in flight
(spec §11 Act 0: six findings already in different states at shift start)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from verge_schema.enums import DataQuality, EstimateQuality, FindingState, LeadTimeBand
from verge_schema.findings import ContributingSignal, RiskFinding

from .store_base import StoreProtocol

T = datetime(2025, 1, 13, 6, 38, tzinfo=UTC)


def seed(store: StoreProtocol) -> StoreProtocol:
    """Populate a store via its protocol — works for in-memory and SQL alike."""
    store.set_sensor_health({
        DataQuality.LIVE: 847, DataQuality.STALE: 12, DataQuality.STUCK_AT_VALUE: 3,
        DataQuality.MISSING: 0,
    })

    findings = [
        RiskFinding(finding_id="F-NEW-01", created_at=T + timedelta(minutes=-7), zone_id="B-04",
                    title="ambient CO sensor drift", state=FindingState.NEW, confidence=0.45,
                    lead_time_band=LeadTimeBand.WATCH, estimate_quality=EstimateQuality.MEDIUM,
                    lineage=["reading:CO-11"]),
        RiskFinding(finding_id="F-ACK-01", created_at=T + timedelta(minutes=-20), zone_id="C-12",
                    title="stale-sensor advisory", state=FindingState.ACKNOWLEDGED, confidence=0.5,
                    confidence_degraded=True, confidence_degraded_by=["CAM-09"],
                    lineage=["reading:CAM-09"]),
        RiskFinding(finding_id="F-ACK-02", created_at=T + timedelta(minutes=-25), zone_id="B-04",
                    title="open night-shift permit awaiting sign-off",
                    state=FindingState.ACKNOWLEDGED, confidence=0.55, lineage=["permit:PW-0140"]),
        RiskFinding(finding_id="F-SNZ-01", created_at=T + timedelta(minutes=-40), zone_id="A-02",
                    title="vibration trend on pump P-3", state=FindingState.SNOOZED, confidence=0.5,
                    lineage=["reading:VIB-03"]),
        RiskFinding(finding_id="F-ESC-01", created_at=T + timedelta(minutes=-23), zone_id="D-01",
                    title="escalated: repeated LEL spikes", state=FindingState.ESCALATED,
                    confidence=0.7, owner="shift-supervisor", lineage=["reading:LEL-21"]),
        RiskFinding(finding_id="F-RES-01", created_at=T + timedelta(minutes=-60), zone_id="B-01",
                    title="resolved by night shift", state=FindingState.RESOLVED, confidence=0.8,
                    lineage=["reading:CO-02"]),
    ]
    for f in findings:
        store.add_finding(f)

    # The convergence (Act 2) arrives as the seventh, in NEW.
    store.add_finding(RiskFinding(
        finding_id="F-CONV-07", created_at=T + timedelta(minutes=6), zone_id="B-04",
        title="Hot work + rising flammable gas during shift changeover",
        state=FindingState.NEW, confidence=0.85,
        contributing_signals=[
            ContributingSignal(
                kind="permit", ref_id="PW-2025-0142", summary="hot-work permit active"
            ),
            ContributingSignal(kind="reading", ref_id="LEL-04", summary="gas-lel 91.5 (rising)"),
            ContributingSignal(
                kind="shift", ref_id="changeover", summary="shift changeover window"
            ),
        ],
        lead_time_band=LeadTimeBand.NEAR, lead_time_basis="rate-of-rise 1.0/min, R^2=0.98, n=10",
        estimate_quality=EstimateQuality.HIGH,
        counterfactual="risk drops to LOW if permit PW-2025-0142 is closed",
        lineage=["permit:PW-2025-0142", "reading:LEL-04", "shift:changeover"],
    ))
    return store
