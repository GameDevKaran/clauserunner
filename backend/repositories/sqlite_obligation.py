import json
from datetime import datetime
from typing import List, Optional
from backend.domain.models import (
    Obligation, ObligationStatus, ObligationType, EvidenceArtifact, EvidenceStatus, 
    Investigation, ToolExecution
)
from backend.repositories.sqlite_base import SQLiteBase

class SQLiteObligation(SQLiteBase):
    """Mixin for Obligation, Evidence and Investigation CRUD."""
    def save_obligation(self, ob: Obligation) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO obligations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (ob.id, ob.contract_id, ob.source_clause_id, ob.title, ob.description, ob.obligation_type.value, ob.responsible_party, ob.counterparty, ob.effective_from.isoformat(), ob.effective_until.isoformat(), ob.trigger, ob.deadline.isoformat() if ob.deadline else None, ob.measurement_period, ob.evidence_requirements, ob.threshold, ob.remedy, 1 if ob.approval_policy else 0, ob.status.value, ob.created_at.isoformat(), ob.updated_at.isoformat()))
            conn.commit()

    def _hydrate_ob(self, r) -> Obligation:
        d = dict(r)
        d["obligation_type"] = ObligationType(d["obligation_type"])
        d["status"] = ObligationStatus(d["status"])
        d["approval_policy"] = bool(d["approval_policy"])
        for k in ["effective_from", "effective_until", "created_at", "updated_at"]:
            d[k] = datetime.fromisoformat(d[k])
        if d["deadline"]:
            d["deadline"] = datetime.fromisoformat(d["deadline"])
        return Obligation(**d)

    def get_obligation(self, id: str) -> Optional[Obligation]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM obligations WHERE id = ?", (id,)).fetchone()
            return self._hydrate_ob(r) if r else None

    def list_obligations(self, contract_id: Optional[str] = None) -> List[Obligation]:
        with self._get_connection() as conn:
            q = "SELECT * FROM obligations WHERE contract_id = ?" if contract_id else "SELECT * FROM obligations"
            rows = conn.execute(q, (contract_id,) if contract_id else ()).fetchall()
            return [self._hydrate_ob(r) for r in rows]

    def save_evidence(self, ev: EvidenceArtifact) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO evidence_artifacts VALUES (?,?,?,?,?,?,?,?)", (ev.id, ev.obligation_id, ev.name, ev.content_type, ev.file_path_or_url, json.dumps(ev.raw_data_summary), ev.status.value, ev.upload_date.isoformat()))
            conn.commit()

    def _hydrate_ev(self, r) -> EvidenceArtifact:
        d = dict(r)
        d["status"] = EvidenceStatus(d["status"])
        d["raw_data_summary"] = json.loads(d["raw_data_summary"])
        d["upload_date"] = datetime.fromisoformat(d["upload_date"])
        return EvidenceArtifact(**d)

    def get_evidence(self, id: str) -> Optional[EvidenceArtifact]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM evidence_artifacts WHERE id = ?", (id,)).fetchone()
            return self._hydrate_ev(r) if r else None

    def list_evidence(self, obligation_id: Optional[str] = None) -> List[EvidenceArtifact]:
        with self._get_connection() as conn:
            q = "SELECT * FROM evidence_artifacts WHERE obligation_id = ?" if obligation_id else "SELECT * FROM evidence_artifacts"
            rows = conn.execute(q, (obligation_id,) if obligation_id else ()).fetchall()
            return [self._hydrate_ev(r) for r in rows]

    def save_investigation(self, inv: Investigation) -> None:
        with self._get_connection() as conn:
            steps_json = json.dumps([s.dict() for s in inv.steps])
            conn.execute("INSERT OR REPLACE INTO investigations VALUES (?,?,?,?,?,?,?,?,?)", (inv.id, inv.obligation_id, inv.status, steps_json, inv.findings, inv.confidence, inv.proposed_action_id, inv.created_at.isoformat(), inv.completed_at.isoformat() if inv.completed_at else None))
            conn.commit()

    def get_investigation(self, id: str) -> Optional[Investigation]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM investigations WHERE id = ?", (id,)).fetchone()
            if not r: return None
            steps = [ToolExecution(tool_name=s["tool_name"], inputs=s["inputs"], outputs=s["outputs"], timestamp=datetime.fromisoformat(s["timestamp"])) for s in json.loads(r["steps"])]
            return Investigation(id=r["id"], obligation_id=r["obligation_id"], status=r["status"], steps=steps, findings=r["findings"], confidence=r["confidence"], proposed_action_id=r["proposed_action_id"], created_at=datetime.fromisoformat(r["created_at"]), completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None)
