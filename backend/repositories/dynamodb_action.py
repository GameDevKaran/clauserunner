import json
from datetime import datetime
from typing import List, Optional
from backend.domain.models import (
    ProposedAction, ActionType, ActionStatus, ApprovalRequest, ApprovalStatus, 
    ActionExecution, AuditEvent
)
from backend.repositories.dynamodb_base import DynamoDBBase

class DynamoDBAction(DynamoDBBase):
    """Mixin for DynamoDB Proposed Actions, Approvals, Executions, and Audits."""
    def save_proposed_action(self, act: ProposedAction) -> None:
        self._put_item(f"ACTION#{act.id}", "METADATA", act.dict())

    def _hydrate_action(self, r) -> ProposedAction:
        d = dict(r)
        d["action_type"] = ActionType(d["action_type"])
        d["status"] = ActionStatus(d["status"])
        d["requires_approval"] = bool(d["requires_approval"])
        d["draft_payload"] = json.loads(d["draft_payload"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        return ProposedAction(**d)

    def get_proposed_action(self, id: str) -> Optional[ProposedAction]:
        r = self._get_item(f"ACTION#{id}", "METADATA")
        return self._hydrate_action(r) if r else None

    def list_proposed_actions(self, obligation_id: Optional[str] = None) -> List[ProposedAction]:
        items = self._scan_by_sk("METADATA")
        acts = [self._hydrate_action(r) for r in items if r["PK"].startswith("ACTION#")]
        return [a for a in acts if not obligation_id or a.obligation_id == obligation_id]

    def save_approval_request(self, req: ApprovalRequest) -> None:
        self._put_item(f"APPROVAL#{req.id}", "METADATA", req.dict())

    def _hydrate_approval(self, r) -> ApprovalRequest:
        d = dict(r)
        d["status"] = ApprovalStatus(d["status"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        if d.get("decided_at"):
            d["decided_at"] = datetime.fromisoformat(d["decided_at"])
        return ApprovalRequest(**d)

    def get_approval_request(self, id: str) -> Optional[ApprovalRequest]:
        r = self._get_item(f"APPROVAL#{id}", "METADATA")
        return self._hydrate_approval(r) if r else None

    def list_approval_requests(self) -> List[ApprovalRequest]:
        items = self._scan_by_sk("METADATA")
        return [self._hydrate_approval(r) for r in items if r["PK"].startswith("APPROVAL#")]

    def save_action_execution(self, ex: ActionExecution) -> None:
        self._put_item(f"EXECUTION#{ex.id}", "METADATA", ex.dict())

    def get_action_execution(self, id: str) -> Optional[ActionExecution]:
        r = self._get_item(f"EXECUTION#{id}", "METADATA")
        if not r: return None
        return ActionExecution(id=r["id"], proposed_action_id=r["proposed_action_id"], executed_by=r["executed_by"], status=r["status"], result_artifact=json.loads(r["result_artifact"]), executed_at=datetime.fromisoformat(r["executed_at"]))

    def save_audit_event(self, ev: AuditEvent) -> None:
        self._put_item(f"AUDIT#{ev.id}", "METADATA", ev.dict())

    def list_audit_events(self, obligation_id: Optional[str] = None) -> List[AuditEvent]:
        items = self._scan_by_sk("METADATA")
        auds = []
        for r in items:
            if r["PK"].startswith("AUDIT#"):
                aud = AuditEvent(id=r["id"], contract_id=r["contract_id"], obligation_id=r.get("obligation_id"), action_type=r["action_type"], description=r["description"], user_or_system=r["user_or_system"], request_id=r.get("request_id"), timestamp=datetime.fromisoformat(r["timestamp"]), metadata=json.loads(r["metadata"]))
                if not obligation_id or aud.obligation_id == obligation_id:
                    auds.append(aud)
        auds.sort(key=lambda x: x.timestamp, reverse=True)
        return auds
