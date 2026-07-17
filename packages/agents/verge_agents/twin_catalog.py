"""Known twin tags for deterministic brief validation (Phase 2.5 G4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TwinCatalog:
    """Equipment / zone / sensor IDs that exist on the commissioned plant."""

    zone_ids: frozenset[str] = field(default_factory=frozenset)
    equipment_ids: frozenset[str] = field(default_factory=frozenset)
    sensor_ids: frozenset[str] = field(default_factory=frozenset)
    muster_ids: frozenset[str] = field(default_factory=frozenset)

    def all_ids(self) -> frozenset[str]:
        return self.zone_ids | self.equipment_ids | self.sensor_ids | self.muster_ids

    def contains(self, tag: str) -> bool:
        return tag in self.all_ids()

    @classmethod
    def from_plant(cls, plant: Any) -> TwinCatalog:
        """Build from a ``PlantModel`` (or any object with the same dict attrs)."""
        zones = getattr(plant, "zones", {}) or {}
        equipment = getattr(plant, "equipment", {}) or {}
        sensors = getattr(plant, "sensors", {}) or {}
        muster = getattr(plant, "muster_points", {}) or {}
        return cls(
            zone_ids=frozenset(str(k) for k in zones),
            equipment_ids=frozenset(str(k) for k in equipment),
            sensor_ids=frozenset(str(k) for k in sensors),
            muster_ids=frozenset(str(k) for k in muster),
        )

    @classmethod
    def empty(cls) -> TwinCatalog:
        return cls()
