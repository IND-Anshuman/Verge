"""Static multi-site catalog — live KPIs are merged in routes/fleet.py."""

from __future__ import annotations

from dataclasses import dataclass

from verge_schema.enums import FindingState, LeadTimeBand


@dataclass(frozen=True)
class PlantCatalogEntry:
    plant_id: str
    name: str
    location: str
    zone_prefixes: tuple[str, ...]
    zone_ids: frozenset[str]
    trir_baseline: float
    alert_fatigue_baseline: float


PLANTS: tuple[PlantCatalogEntry, ...] = (
    PlantCatalogEntry(
        plant_id="PLT-VIZAG",
        name="Visakhapatnam Steel Complex",
        location="Andhra Pradesh, IN",
        zone_prefixes=("B-", "C-", "A-", "D-"),
        zone_ids=frozenset(),
        trir_baseline=0.85,
        alert_fatigue_baseline=14.0,
    ),
    PlantCatalogEntry(
        plant_id="PLT-JAIPUR",
        name="Jaipur Terminal Refinery",
        location="Rajasthan, IN",
        zone_prefixes=(),
        zone_ids=frozenset({"TF-A"}),
        trir_baseline=0.42,
        alert_fatigue_baseline=4.0,
    ),
    PlantCatalogEntry(
        plant_id="PLT-TEXAS",
        name="Texas City Petromin",
        location="Texas City, US",
        zone_prefixes=(),
        zone_ids=frozenset({"RS-T"}),
        trir_baseline=1.12,
        alert_fatigue_baseline=28.0,
    ),
)

ACTIVE_STATES = frozenset(
    {FindingState.NEW, FindingState.ACKNOWLEDGED, FindingState.ESCALATED, FindingState.SNOOZED}
)


def plant_for_zone(zone_id: str) -> PlantCatalogEntry | None:
    for plant in PLANTS:
        if zone_id in plant.zone_ids:
            return plant
        if any(zone_id.startswith(p) for p in plant.zone_prefixes):
            return plant
    return None


def risk_status(active: int, bands: set[LeadTimeBand]) -> str:
    if active == 0:
        return "ok"
    if LeadTimeBand.IMMINENT in bands or (
        LeadTimeBand.NEAR in bands and active >= 2
    ):
        return "imminent"
    if LeadTimeBand.NEAR in bands or LeadTimeBand.WATCH in bands:
        return "near"
    return "ok"
