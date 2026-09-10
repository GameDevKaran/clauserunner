import json
from datetime import datetime
from typing import List, Optional
from backend.domain.models import (
    Obligation, ObligationStatus, ObligationType, EvidenceArtifact, EvidenceStatus, 
    Investigation, ToolExecution
)
from backend.repositories.dynamodb_base import DynamoDBBase

class DynamoDBObligation(DynamoDBBase):
    """Mixin for DynamoDB Obligation, Evidence and Investigation CRUD."""
    def save_obligation(self, ob: Obligation) -> None:
        self._put_item(f"OBLIGATION#{ob.id}", "METADATA", ob.dict())

    def _hydrate_ob(self, r) -> Obligation:
        d = dict(r)
        d["obligation_type"] = ObligationType(d["obligation_type"])
        d["status"] = ObligationStatus(d["status"])
        d["approval_policy"] = bool(d["approval_policy"])
        for k in ["effective_from", "effective_until", "created_at", "updated_at"]:
            d[k] = datetime.fromisoformat(d[k])
        if d.get("deadline"):
            d["deadline"] = datetime.fromisoformat(d["deadline"])
        return Obligation(**d)

    def get_obligation(self, id: str) -> Optional[Obligation]:
        r = self._get_item(f"OBLIGATION#{id}", "METADATA")
        return self._hydrate_ob(r) if r else None

    def list_obligations(self, contract_id: Optional[str] = None) -> List[Obligation]:
        items = self._scan_by_sk("METADATA")
        obs = [self._hydrate_ob(r) for r in items if r["PK"].startswith("OBLIGATION#")]
        return [o for o in obs if not contract_id or o.contract_id == contract_id]

    def save_evidence(self, ev: EvidenceArtifact) -> None:
        self._put_item(f"EVIDENCE#{ev.id}", "METADATA", ev.dict())

    def _hydrate_ev(self, r) -> EvidenceArtifact:
        d = dict(r)
        d["status"] = EvidenceStatus(d["status"])
        d["raw_data_summary"] = json.loads(d["raw_data_summary"])
        d["upload_date"] = datetime.fromisoformat(d["upload_date"])
        return EvidenceArtifact(**d)

    def get_evidence(self, id: str) -> Optional[EvidenceArtifact]:
        r = self._get_item(f"EVIDENCE#{id}", "METADATA")
        return self._hydrate_ev(r) if r else None

    def list_evidence(self, obligation_id: Optional[str] = None) -> List[EvidenceArtifact]:
        items = self._scan_by_sk("METADATA")
        evs = [self._hydrate_ev(r) for r in items if r["PK"].startswith("EVIDENCE#")]
        return [e for e in evs if not obligation_id or e.obligation_id == obligation_id]

    def save_investigation(self, inv: Investigation) -> None:
        self._put_item(f"INVESTIGATION#{inv.id}", "METADATA", inv.dict())

    def get_investigation(self, id: str) -> Optional[Investigation]:
        r = self._get_item(f"INVESTIGATION#{id}", "METADATA")
        if not r: return None
        steps = [ToolExecution(tool_name=s["tool_name"], inputs=s["inputs"], outputs=s["outputs"], timestamp=datetime.fromisoformat(s["timestamp"])) for s in json.loads(r["steps"])]
        return Investigation(id=r["id"], obligation_id=r["obligation_id"], status=r["status"], steps=steps, findings=r.get("findings"), confidence=float(r["confidence"]), proposed_action_id=r.get("proposed_action_id"), created_at=datetime.fromisoformat(r["created_at"]), completed_at=datetime.fromisoformat(r["completed_at"]) if r.get("completed_at") else None)
