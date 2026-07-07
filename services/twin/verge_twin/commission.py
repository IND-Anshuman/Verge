"""Commissioning steps 1–2 (spec §14.5): import a plant layout and map sensors.

A plant is *configured, not coded* (see ``plant.py``). Commissioning is the
first thing every pilot plant does — and the first two steps are pure spatial
bookkeeping that must run anywhere, so they live here on top of the
dependency-free :mod:`verge_twin.geometry` toolkit:

  1. **Import plant layout** — read zone polygons from GeoJSON, validate that
     zones do not overlap, infer zone adjacency from shared boundaries, and
     report coverage so gaps are visible before go-live.
  2. **Map sensors to zones** — from a CSV, by explicit zone or by point-in-zone
     location. Any sensor that lands in no zone is flagged ``unassigned`` and is
     excluded from risk scoring until a safety engineer assigns it.

Steps 3–6 (adopt rules, thresholds, dry-run replay, shadow mode) compose these
outputs and live in the ``verge`` CLI, which bridges the engine and the replay
harness. This module stays a leaf: geometry + the plant model, nothing else.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import geometry as g
from .plant import PlantModel, SensorNode, ZoneNode


@dataclass(frozen=True)
class ZoneGeometry:
    zone_id: str
    name: str
    polygon: list[list[g.Point]]  # rings; ring 0 is the exterior

    @property
    def area(self) -> float:
        return g.polygon_area(self.polygon)


@dataclass
class LayoutReport:
    """Result of validating an imported plant layout (step 1)."""

    plant: str
    zones: list[str] = field(default_factory=list)
    overlaps: list[tuple[str, str]] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    zone_area: dict[str, float] = field(default_factory=dict)
    isolated_zones: list[str] = field(default_factory=list)
    invalid_zones: list[str] = field(default_factory=list)
    covered_area: float = 0.0
    footprint_area: float = 0.0

    @property
    def coverage_ratio(self) -> float:
        return self.covered_area / self.footprint_area if self.footprint_area else 0.0

    @property
    def ok(self) -> bool:
        """A layout is clean when no zones overlap and every zone is valid."""
        return not self.overlaps and not self.invalid_zones

    def to_dict(self) -> dict:
        return {
            "plant": self.plant,
            "zones": self.zones,
            "overlaps": [list(p) for p in self.overlaps],
            "adjacency": {k: sorted(v) for k, v in self.adjacency.items()},
            "zoneArea": {k: round(v, 10) for k, v in self.zone_area.items()},
            "isolatedZones": self.isolated_zones,
            "invalidZones": self.invalid_zones,
            "coverageRatio": round(self.coverage_ratio, 4),
            "ok": self.ok,
        }


def load_zone_geometries(geojson_path: str | Path) -> list[ZoneGeometry]:
    """Read zone polygons from a GeoJSON FeatureCollection.

    Each feature needs a ``zoneId`` (or ``id``) property and a Polygon geometry.
    MultiPolygon features are flattened to their first polygon; a plant zone is a
    single contiguous area by convention.
    """
    doc = json.loads(Path(geojson_path).read_text(encoding="utf-8-sig"))
    zones: list[ZoneGeometry] = []
    for feat in doc.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        zone_id = props.get("zoneId") or props.get("id")
        if not zone_id:
            continue
        coords = geom.get("coordinates") or []
        gtype = geom.get("type")
        if gtype == "Polygon":
            rings = coords
        elif gtype == "MultiPolygon":
            rings = coords[0] if coords else []
        else:
            rings = []
        # A malformed / non-finite coordinate yields an empty polygon, which
        # validate_layout then flags as an invalid zone — one bad cell must not
        # crash the whole layout import (P4).
        polygon = _parse_rings(rings)
        zones.append(ZoneGeometry(zone_id, props.get("name", zone_id), polygon))
    return zones


def _parse_rings(rings: list) -> list[list[g.Point]]:
    out: list[list[g.Point]] = []
    try:
        for ring in rings:
            parsed: list[g.Point] = []
            for x, y in ring:
                fx, fy = float(x), float(y)
                if not (math.isfinite(fx) and math.isfinite(fy)):
                    return []
                parsed.append((fx, fy))
            out.append(parsed)
    except (TypeError, ValueError):
        return []
    return out


def validate_layout(plant: str, zones: list[ZoneGeometry]) -> LayoutReport:
    """Step 1 validation: overlaps (errors), adjacency (inferred), coverage."""
    report = LayoutReport(plant=plant, zones=[z.zone_id for z in zones])

    valid: list[ZoneGeometry] = []
    seen: set[str] = set()
    for z in zones:
        if z.zone_id in seen:
            # A duplicate zoneId would collapse two polygons into one node and
            # emit a nonsensical self-overlap — flag it, don't silently drop data.
            if z.zone_id not in report.invalid_zones:
                report.invalid_zones.append(z.zone_id)
            continue
        seen.add(z.zone_id)
        if not z.polygon or len(z.polygon[0]) < 3 or z.area <= g.EPS:
            report.invalid_zones.append(z.zone_id)
        else:
            valid.append(z)
            report.zone_area[z.zone_id] = z.area

    adjacency: dict[str, set[str]] = {z.zone_id: set() for z in valid}
    for i, a in enumerate(valid):
        for b in valid[i + 1 :]:
            if g.polygons_overlap(a.polygon, b.polygon):
                report.overlaps.append((a.zone_id, b.zone_id))
            elif g.polygons_touch(a.polygon, b.polygon):
                adjacency[a.zone_id].add(b.zone_id)
                adjacency[b.zone_id].add(a.zone_id)
    report.adjacency = {k: sorted(v) for k, v in adjacency.items()}

    # Zones with no neighbour are flagged: a plant is normally one connected
    # footprint, so an island is usually a mis-placed or mis-scaled polygon.
    if len(valid) > 1:
        report.isolated_zones = sorted(z for z, nbrs in adjacency.items() if not nbrs)

    report.covered_area = sum(report.zone_area.values())
    if valid:
        boxes = [g.bbox(z.polygon) for z in valid]
        min_x = min(b[0] for b in boxes)
        min_y = min(b[1] for b in boxes)
        max_x = max(b[2] for b in boxes)
        max_y = max(b[3] for b in boxes)
        report.footprint_area = (max_x - min_x) * (max_y - min_y)
    return report


@dataclass
class SensorMapping:
    """Result of mapping sensors to zones (step 2)."""

    plant: str
    mapped: list[SensorNode] = field(default_factory=list)
    unassigned: list[str] = field(default_factory=list)

    @property
    def by_zone(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for s in self.mapped:
            out.setdefault(s.zone_id, []).append(s.sensor_id)
        return out

    def to_dict(self) -> dict:
        return {
            "plant": self.plant,
            "mapped": {s.sensor_id: s.zone_id for s in self.mapped},
            "byZone": {k: sorted(v) for k, v in self.by_zone.items()},
            "unassigned": sorted(self.unassigned),
        }


def _float_or_none(v: str | None) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    return float(v)


def map_sensors(csv_path: str | Path, zones: list[ZoneGeometry]) -> SensorMapping:
    """Step 2: assign each CSV sensor to a zone.

    CSV columns: ``sensorId,kind,unit,zone,lon,lat,threshold,cadenceS``. A sensor
    is placed by explicit ``zone`` if given and valid, else by ``lon/lat``
    point-in-zone. A sensor that matches no zone is left ``unassigned`` — it is
    recorded but excluded from risk scoring (spec §14.5 step 2).
    """
    by_id = {z.zone_id: z for z in zones}
    mapping = SensorMapping(plant="")
    rows = list(csv.DictReader(Path(csv_path).read_text(encoding="utf-8-sig").splitlines()))
    for row in rows:
        sid = (row.get("sensorId") or "").strip()
        if not sid:
            continue
        zone = (row.get("zone") or "").strip()
        if zone not in by_id:
            zone = _locate_zone(row, zones) or ""
        if not zone:
            mapping.unassigned.append(sid)
            continue
        mapping.mapped.append(
            SensorNode(
                sensor_id=sid,
                kind=(row.get("kind") or "").strip(),
                unit=(row.get("unit") or "").strip(),
                zone_id=zone,
                threshold=_float_or_none(row.get("threshold")),
                cadence_s=_float_or_none(row.get("cadenceS")) or 30.0,
            )
        )
    return mapping


def _locate_zone(row: dict, zones: list[ZoneGeometry]) -> str | None:
    lon, lat = _float_or_none(row.get("lon")), _float_or_none(row.get("lat"))
    if lon is None or lat is None or not (math.isfinite(lon) and math.isfinite(lat)):
        return None
    # boundary=False on purpose: a sensor exactly on a shared zone edge is
    # ambiguous, and picking by feature order would be nondeterministic. Leave it
    # unassigned so a safety engineer resolves it explicitly (spec §14.5 step 2).
    matches = [z.zone_id for z in zones
               if z.polygon and g.point_in_polygon((lon, lat), z.polygon, boundary=False)]
    return matches[0] if len(matches) == 1 else None


def build_plant_model(
    name: str, layout: LayoutReport, zones: list[ZoneGeometry], mapping: SensorMapping
) -> PlantModel:
    """Assemble a commissioned :class:`PlantModel` from validated layout + sensors."""
    zone_nodes = {
        z.zone_id: ZoneNode(z.zone_id, z.name, frozenset(layout.adjacency.get(z.zone_id, [])))
        for z in zones
        if z.zone_id not in layout.invalid_zones
    }
    sensor_nodes = {s.sensor_id: s for s in mapping.mapped if s.zone_id in zone_nodes}
    return PlantModel(name=name, zones=zone_nodes, sensors=sensor_nodes)


def to_plant_yaml(model: PlantModel) -> str:
    """Serialize a commissioned plant to the YAML shape ``load_plant`` reads."""
    doc = {
        "name": model.name,
        "zones": [
            {"id": z.zone_id, "name": z.name, "adjacent": sorted(z.adjacent)}
            for z in model.zones.values()
        ],
        "sensors": [
            {
                "id": s.sensor_id,
                "kind": s.kind,
                "unit": s.unit,
                "zone": s.zone_id,
                **({"threshold": s.threshold} if s.threshold is not None else {}),
                "cadenceS": s.cadence_s,
            }
            for s in model.sensors.values()
        ],
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
