"""Resolve extracted entity mentions against the plant twin (Phase 1.2)."""

from __future__ import annotations

import re

from verge_schema.documents import EntityKind, EntityMention


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def resolve_entities(
    entities: list[EntityMention],
    *,
    zone_ids: set[str],
    sensor_ids: set[str],
    equipment_ids: set[str],
) -> list[EntityMention]:
    """Attach ``resolved_ref`` when a mention matches a twin id. Unresolved stay null."""
    zone_n = {_norm(z): z for z in zone_ids}
    sensor_n = {_norm(s): s for s in sensor_ids}
    equip_n = {_norm(e): e for e in equipment_ids}
    out: list[EntityMention] = []
    for ent in entities:
        key = _norm(ent.normalized or ent.raw)
        ref: str | None = None
        if ent.kind == EntityKind.ZONE or str(ent.kind) == "zone":
            ref = zone_n.get(key)
        elif ent.kind == EntityKind.EQUIPMENT or str(ent.kind) == "equipment":
            ref = sensor_n.get(key) or equip_n.get(key)
            if ref is None:
                # P-3 ↔ PUMP-3 soft match
                for cand_n, cand in {**sensor_n, **equip_n}.items():
                    if key.endswith(cand_n) or cand_n.endswith(key) or key in cand_n:
                        ref = cand
                        break
        out.append(ent.model_copy(update={"resolved_ref": ref}))
    return out
