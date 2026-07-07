"""Commissioning steps 1–2 (spec §14.5): layout import + sensor mapping."""

from __future__ import annotations

import json

from verge_twin import (
    build_plant_model,
    load_plant,
    load_zone_geometries,
    map_sensors,
    to_plant_yaml,
    validate_layout,
)
from verge_twin.plant import PLANTS_DIR

VIZAG_GEOJSON = PLANTS_DIR / "vizag-zones.geojson"


def test_import_and_validate_demo_layout_is_clean():
    zones = load_zone_geometries(VIZAG_GEOJSON)
    report = validate_layout("vizag-coke-oven", zones)

    assert report.ok
    assert not report.overlaps
    assert set(report.zones) == {"B-01", "B-02", "B-03", "B-04", "B-05"}
    # The five batteries form one adjacency chain B-01–B-02–…–B-05.
    assert report.adjacency["B-01"] == ["B-02"]
    assert report.adjacency["B-04"] == ["B-03", "B-05"]
    assert not report.isolated_zones


def test_inferred_adjacency_matches_hand_written_demo_plant():
    zones = load_zone_geometries(VIZAG_GEOJSON)
    report = validate_layout("vizag-coke-oven", zones)
    hand = load_plant().adjacency()
    inferred = {k: set(v) for k, v in report.adjacency.items()}
    for zone, neighbours in inferred.items():
        assert neighbours == hand[zone], zone


def test_overlapping_zones_are_flagged(tmp_path):
    doc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"zoneId": "Z1"},
                "geometry": {"type": "Polygon", "coordinates": [
                    [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]},
            },
            {
                "type": "Feature",
                "properties": {"zoneId": "Z2"},
                "geometry": {"type": "Polygon", "coordinates": [
                    [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]]},
            },
        ],
    }
    p = tmp_path / "overlap.geojson"
    p.write_text(json.dumps(doc), encoding="utf-8")
    report = validate_layout("bad", load_zone_geometries(p))
    assert not report.ok
    assert ("Z1", "Z2") in report.overlaps


def test_sensor_mapping_by_zone_and_by_location_and_unassigned(tmp_path):
    zones = load_zone_geometries(VIZAG_GEOJSON)
    csv_text = "\n".join([
        "sensorId,kind,unit,zone,lon,lat,threshold,cadenceS",
        "LEL-04,gas-lel,%LEL,B-04,,,100,30",          # explicit zone
        "CO-CTR,gas-co,ppm,,83.228,17.690,50,30",     # located inside B-03 by lon/lat
        "GHOST,gas-lel,%LEL,,999,999,100,30",         # outside every zone -> unassigned
        "NOZONE,gas-co,ppm,,,,50,30",                 # no zone, no coords -> unassigned
    ])
    p = tmp_path / "sensors.csv"
    p.write_text(csv_text, encoding="utf-8")

    mapping = map_sensors(p, zones)
    mapped = {s.sensor_id: s.zone_id for s in mapping.mapped}
    assert mapped["LEL-04"] == "B-04"
    assert mapped["CO-CTR"] == "B-03"
    assert set(mapping.unassigned) == {"GHOST", "NOZONE"}


def test_sensor_csv_tolerates_bom(tmp_path):
    zones = load_zone_geometries(VIZAG_GEOJSON)
    p = tmp_path / "bom.csv"
    p.write_bytes("sensorId,kind,unit,zone,threshold,cadenceS\nLEL-04,gas-lel,%LEL,B-04,100,30\n"
                  .encode("utf-8-sig"))
    mapping = map_sensors(p, zones)
    # BOM must not blank the first column and silently drop the sensor.
    assert [s.sensor_id for s in mapping.mapped] == ["LEL-04"]


def test_duplicate_zone_ids_are_flagged_invalid(tmp_path):
    doc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"zoneId": "DUP"},
         "geometry": {"type": "Polygon",
                      "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}},
        {"type": "Feature", "properties": {"zoneId": "DUP"},
         "geometry": {"type": "Polygon",
                      "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]}},
    ]}
    p = tmp_path / "dup.geojson"
    p.write_text(json.dumps(doc), encoding="utf-8")
    report = validate_layout("dup", load_zone_geometries(p))
    assert "DUP" in report.invalid_zones
    assert ("DUP", "DUP") not in report.overlaps  # no nonsensical self-overlap


def test_sensor_on_shared_boundary_is_unassigned(tmp_path):
    # Two zones sharing the x=1 edge; a sensor exactly on that edge is ambiguous
    # and must be left unassigned (not silently claimed by feature order).
    doc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"zoneId": "A"},
         "geometry": {"type": "Polygon",
                      "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}},
        {"type": "Feature", "properties": {"zoneId": "B"},
         "geometry": {"type": "Polygon",
                      "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}},
    ]}
    gp = tmp_path / "z.geojson"
    gp.write_text(json.dumps(doc), encoding="utf-8")
    zones = load_zone_geometries(gp)
    csv_text = "sensorId,kind,unit,zone,lon,lat\nEDGE,gas-lel,%LEL,,1.0,0.5\n"
    cp = tmp_path / "s.csv"
    cp.write_text(csv_text, encoding="utf-8")
    mapping = map_sensors(cp, zones)
    assert "EDGE" in mapping.unassigned


def test_build_plant_model_round_trips_through_yaml(tmp_path):
    zones = load_zone_geometries(VIZAG_GEOJSON)
    layout = validate_layout("vizag-coke-oven", zones)
    csv_text = "sensorId,kind,unit,zone,threshold,cadenceS\nLEL-04,gas-lel,%LEL,B-04,100,30\n"
    p = tmp_path / "s.csv"
    p.write_text(csv_text, encoding="utf-8")
    mapping = map_sensors(p, zones)

    model = build_plant_model("vizag-coke-oven", layout, zones, mapping)
    yaml_path = tmp_path / "plant.yaml"
    yaml_path.write_text(to_plant_yaml(model), encoding="utf-8")

    reloaded = load_plant(yaml_path)
    assert reloaded.name == "vizag-coke-oven"
    assert reloaded.adjacency()["B-04"] == {"B-03", "B-05"}
    assert reloaded.sensors["LEL-04"].zone_id == "B-04"
