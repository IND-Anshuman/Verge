"""Emergency response orchestration (spec §4.4) — the confirmed-trigger path.

One operator-approved action turns the first ten minutes from chaos into a
choreography, entirely LLM-free (P1) and operator-gated (P8):

1. **Evidence freeze** — snapshot the finding's telemetry window and the audit
   head into a hash-bound manifest *before* anything else happens, so the
   sensor picture at declaration time is preserved even if the plant network
   degrades (the Vizag lesson: the data existed, then the moment was gone).
2. **Evacuation plan** — BFS routes on the zone graph avoiding affected zones,
   to usable muster points (``verge_twin.muster``).
3. **Muster roll-call** — expected roster from the worker location plane;
   check-ins accumulate; missing = expected − accounted, each with a
   last-known zone (mustering-industry practice: the live roll-call).
4. **Audit** — declaration, every check-in, and stand-down are hash-chained.

Alert dispatch and the preliminary incident report reuse the existing
operator-gated routes; this module owns the emergency state machine.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from verge_audit import canonical_json
from verge_schema.findings import RiskFinding
from verge_twin import PlantModel
from verge_twin.muster import evacuation_plan


class EmergencyManager:
    """At most one active emergency per site (single-plant scope for now)."""

    def __init__(self) -> None:
        self._active: dict | None = None
        self._accounted: dict[str, dict] = {}

    @property
    def active(self) -> dict | None:
        return self._active

    def declare(
        self,
        finding: RiskFinding,
        *,
        approved_by: str,
        plant: PlantModel,
        occupancy,
        readings,
        thresholds: dict[str, float] | None = None,
        now: datetime | None = None,
    ) -> dict:
        approver = (approved_by or "").strip()
        if not approver:
            raise PermissionError("emergency declaration requires an approver (P8)")
        if self._active is not None:
            raise ValueError(
                f"emergency {self._active['emergencyId']} already active — stand down first"
            )
        now = now or datetime.now(UTC)

        # 1. Evidence freeze — telemetry + roster snapshot, hash-bound.
        telemetry = readings.series_for_finding(finding, thresholds=thresholds or {})
        roster = occupancy.positions(now=now)
        frozen = {
            "findingId": finding.finding_id,
            "zoneId": finding.zone_id,
            "frozenAt": now.isoformat(),
            "telemetry": telemetry,
            "workerRoster": roster,
        }
        evidence_hash = hashlib.sha256(canonical_json(frozen).encode()).hexdigest()

        # 2. Affected zones + evacuation plan.
        affected = {finding.zone_id}
        band = finding.lead_time_band
        band_value = band.value if hasattr(band, "value") else str(band)
        if band_value == "IMMINENT":
            affected |= set(plant.adjacency().get(finding.zone_id, set()))
        plan = evacuation_plan(plant, affected)

        # 3. Muster expectations from the worker plane.
        expected = {w["workerId"]: w for w in roster}

        self._accounted = {}
        self._active = {
            "emergencyId": f"EM-{now.strftime('%Y%m%d-%H%M%S')}",
            "findingId": finding.finding_id,
            "declaredAt": now.isoformat(),
            "declaredBy": approver,
            "affectedZones": plan["affectedZones"],
            "evacuation": plan,
            "expectedWorkers": expected,
            "evidenceFreeze": {"manifest": frozen, "hash": evidence_hash},
        }
        return self.status(now=now)

    def check_in(
        self,
        worker_id: str,
        muster_id: str,
        *,
        recorded_by: str,
        now: datetime | None = None,
    ) -> dict:
        if self._active is None:
            raise LookupError("no active emergency")
        now = now or datetime.now(UTC)
        self._accounted[worker_id] = {
            "workerId": worker_id,
            "musterId": muster_id,
            "recordedBy": (recorded_by or "").strip() or "anonymous",
            "ts": now.isoformat(),
        }
        return self.status(now=now)

    def stand_down(self, *, approved_by: str, now: datetime | None = None) -> dict:
        approver = (approved_by or "").strip()
        if not approver:
            raise PermissionError("stand-down requires an approver (P8)")
        if self._active is None:
            raise LookupError("no active emergency")
        now = now or datetime.now(UTC)
        final = self.status(now=now)
        final["stoodDownAt"] = now.isoformat()
        final["stoodDownBy"] = approver
        self._active = None
        self._accounted = {}
        return final

    def status(self, now: datetime | None = None) -> dict:
        if self._active is None:
            return {"active": False}
        now = now or datetime.now(UTC)
        expected = self._active["expectedWorkers"]
        missing = [
            {
                "workerId": wid,
                "name": w.get("name", ""),
                "role": w.get("role", ""),
                "lastKnownZone": w.get("zoneId", ""),
                "lastFixTs": w.get("ts", ""),
                "lastFixStale": w.get("stale", False),
            }
            for wid, w in sorted(expected.items())
            if wid not in self._accounted
        ]
        return {
            "active": True,
            "emergencyId": self._active["emergencyId"],
            "findingId": self._active["findingId"],
            "declaredAt": self._active["declaredAt"],
            "declaredBy": self._active["declaredBy"],
            "affectedZones": self._active["affectedZones"],
            "evacuation": self._active["evacuation"],
            "muster": {
                "expected": len(expected),
                "accounted": sorted(self._accounted.values(), key=lambda a: a["workerId"]),
                "missing": missing,
                "allAccounted": not missing,
            },
            "evidenceFreeze": {
                "hash": self._active["evidenceFreeze"]["hash"],
                "frozenAt": self._active["evidenceFreeze"]["manifest"]["frozenAt"],
                "telemetrySeries": len(
                    self._active["evidenceFreeze"]["manifest"]["telemetry"].get("series", [])
                ),
                "rosterSize": len(self._active["evidenceFreeze"]["manifest"]["workerRoster"]),
            },
            "asOf": now.isoformat(),
        }

    def frozen_evidence(self) -> dict | None:
        if self._active is None:
            return None
        return self._active["evidenceFreeze"]
