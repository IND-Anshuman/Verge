"""CSV-backed work-order store. Never invents WOs — empty when file missing."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
DEFAULT_CSV = FIXTURES / "vizag-work-orders.csv"


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    equipment_id: str
    zone_id: str
    failure_code: str
    state: str
    title: str
    opened_at: str
    closed_at: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "orderId": self.order_id,
            "equipmentId": self.equipment_id,
            "zoneId": self.zone_id,
            "failureCode": self.failure_code,
            "state": self.state,
            "title": self.title,
            "openedAt": self.opened_at,
            "closedAt": self.closed_at or None,
            "description": self.description,
        }


@dataclass
class WorkOrderStore:
    orders: list[WorkOrder] = field(default_factory=list)

    @classmethod
    def from_csv(cls, path: Path | str | None = None) -> WorkOrderStore:
        p = Path(path) if path else DEFAULT_CSV
        if not p.exists():
            return cls([])
        orders: list[WorkOrder] = []
        with p.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                oid = (row.get("orderId") or row.get("order_id") or "").strip()
                if not oid:
                    continue
                orders.append(
                    WorkOrder(
                        order_id=oid,
                        equipment_id=(
                            row.get("equipmentId") or row.get("equipment_id") or ""
                        ).strip(),
                        zone_id=(row.get("zoneId") or row.get("zone_id") or "").strip(),
                        failure_code=(
                            row.get("failureCode") or row.get("failure_code") or ""
                        ).strip(),
                        state=(row.get("state") or "closed").strip().lower(),
                        title=(row.get("title") or "").strip(),
                        opened_at=(row.get("openedAt") or row.get("opened_at") or "").strip(),
                        closed_at=(row.get("closedAt") or row.get("closed_at") or "").strip(),
                        description=(row.get("description") or "").strip(),
                    )
                )
        return cls(orders)

    def list(
        self,
        *,
        zone_id: str | None = None,
        equipment_id: str | None = None,
        state: str | None = None,
        limit: int = 50,
    ) -> list[WorkOrder]:
        out = list(self.orders)
        if zone_id:
            out = [o for o in out if o.zone_id == zone_id]
        if equipment_id:
            out = [o for o in out if o.equipment_id == equipment_id]
        if state:
            out = [o for o in out if o.state == state.lower()]
        return out[: max(1, min(limit, 200))]

    def known_ids(self) -> set[str]:
        return {o.order_id for o in self.orders}


_DEFAULT: WorkOrderStore | None = None


def default_store() -> WorkOrderStore:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = WorkOrderStore.from_csv()
    return _DEFAULT
