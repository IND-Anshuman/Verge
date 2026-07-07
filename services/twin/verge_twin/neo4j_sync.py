"""Neo4j graph sync for equipment-permit-zone relationships (spec §5).

Degrades when the driver or ``NEO4J_URI`` is unset — twin YAML remains the
source of truth for scoring; the graph is for compound-risk queries at scale.
"""

from __future__ import annotations

import os
from typing import Any

from verge_twin.plant import PlantModel


def sync_plant(model: PlantModel, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or dict(os.environ)
    uri = env.get("NEO4J_URI")
    user = env.get("NEO4J_USER", "neo4j")
    password = env.get("NEO4J_PASSWORD")
    if not uri or not password:
        return {"degraded": True, "reason": "NEO4J_URI/NEO4J_PASSWORD not configured"}

    try:
        from neo4j import GraphDatabase
    except ImportError:
        return {"degraded": True, "reason": "neo4j driver not installed"}

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("MERGE (p:Plant {id: $id}) SET p.name = $name",
                        id=model.plant_id, name=model.plant_id)
            for z in model.zones:
                session.run(
                    "MERGE (z:Zone {id: $id}) SET z.name = $name "
                    "WITH z MATCH (p:Plant {id: $plant}) MERGE (p)-[:HAS_ZONE]->(z)",
                    id=z.zone_id, name=z.name, plant=model.plant_id,
                )
            for s in model.sensors.values():
                session.run(
                    "MERGE (e:Equipment {id: $id}) SET e.kind = $kind "
                    "WITH e MATCH (z:Zone {id: $zone}) MERGE (z)-[:HAS_SENSOR]->(e)",
                    id=s.sensor_id, kind=s.kind, zone=s.zone_id,
                )
        driver.close()
        return {
            "degraded": False,
            "zones": len(model.zones),
            "sensors": len(model.sensors),
        }
    except Exception as exc:
        return {"degraded": True, "reason": f"neo4j sync failed: {type(exc).__name__}"}
