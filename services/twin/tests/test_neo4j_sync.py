"""Neo4j graph sync degrades without credentials."""

from __future__ import annotations

from verge_twin import load_plant
from verge_twin.neo4j_sync import sync_plant
from verge_twin.plant import DEMO_PLANT


def test_sync_degrades_without_neo4j_env():
    plant = load_plant(DEMO_PLANT)
    result = sync_plant(plant, env={})
    assert result["degraded"] is True
    assert "NEO4J" in result["reason"]
