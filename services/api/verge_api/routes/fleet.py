"""Multi-site fleet summary for the console command center."""

from __future__ import annotations

from fastapi import APIRouter, Request
from verge_schema.enums import DataQuality

from ..fleet_catalog import ACTIVE_STATES, PLANTS, plant_for_zone, risk_status

router = APIRouter(tags=["fleet"])


def _sensor_health_pct(store) -> int | None:
    health = store.get_sensor_health()
    total = sum(health.values())
    if total == 0:
        return None
    live = health.get(DataQuality.LIVE, 0)
    return round(100 * live / total)


@router.get("/fleet/summary")
def fleet_summary(request: Request) -> dict:
    """Aggregate live finding counts per plant; baselines for unmeasured KPIs."""
    store = request.app.state.store
    findings = [f for f in store.list_findings(shadow=False) if f.state in ACTIVE_STATES]

    by_plant: dict[str, list] = {p.plant_id: [] for p in PLANTS}
    for f in findings:
        plant = plant_for_zone(f.zone_id)
        if plant:
            by_plant[plant.plant_id].append(f)

    vizag_health = _sensor_health_pct(store)
    plants_out = []
    for entry in PLANTS:
        active = by_plant[entry.plant_id]
        bands = {f.lead_time_band for f in active}
        plants_out.append(
            {
                "plantId": entry.plant_id,
                "name": entry.name,
                "location": entry.location,
                "activeRisks": len(active),
                "sensorHealth": vizag_health if entry.plant_id == "PLT-VIZAG" else None,
                # Unmeasured baselines stay null — console must not render fiction.
                "alertFatigueRate": None,
                "trir": None,
                "status": risk_status(len(active), bands),
                "connected": entry.plant_id == "PLT-VIZAG",
                "measured": {
                    "activeRisks": True,
                    "sensorHealth": entry.plant_id == "PLT-VIZAG" and vizag_health is not None,
                    "alertFatigueRate": False,
                    "trir": False,
                },
            }
        )

    return {"plants": plants_out, "connectedSite": "PLT-VIZAG"}
