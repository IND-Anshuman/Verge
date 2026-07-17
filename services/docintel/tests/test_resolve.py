from verge_docintel import extract_entities, resolve_entities
from verge_schema.documents import EntityKind


def test_resolve_zone_and_sensor() -> None:
    ents = extract_entities(
        "Confirm LEL-04 in zone B-04 before welding near PUMP-3.",
        document_id="D1",
    )
    resolved = resolve_entities(
        ents,
        zone_ids={"B-04", "B-05"},
        sensor_ids={"LEL-04", "CO-04"},
        equipment_ids={"charging-car-hydraulics"},
    )
    by_kind = {str(e.kind): e for e in resolved}
    zone = next(e for e in resolved if e.kind == EntityKind.ZONE or str(e.kind) == "zone")
    assert zone.resolved_ref == "B-04"
    lel = next(e for e in resolved if "LEL" in (e.normalized or e.raw).upper())
    assert lel.resolved_ref == "LEL-04"
    assert by_kind  # sanity
