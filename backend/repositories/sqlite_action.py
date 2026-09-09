import json
from datetime import datetime
from typing import List, Optional
from backend.domain.models import (
    ProposedAction, ActionType, ActionStatus, ApprovalRequest, ApprovalStatus, 
    ActionExecution, AuditEvent
)
from backend.repositories.sqlite_base import SQLiteBase

class SQLiteAction(SQLiteBase):
    """Mixin for Proposed Actions, Approval Requests, Action Executions and Audits."""
    # ProposedAction
    def save_proposed_action(self, act: ProposedAction) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO proposed_actions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (act.id, act.obligation_id, act.investigation_id, act.title, act.description, act.action_type.value, act.cost_or_impact, 1 if act.requires_approval else 0, json.dumps(act.draft_payload), act.status.value, act.created_at.isoformat(), act.updated_at.isoformat()))
            conn.commit()

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
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM proposed_actions WHERE id = ?", (id,)).fetchone()
            return self._hydrate_action(r) if r else None

    def list_proposed_actions(self, obligation_id: Optional[str] = None) -> List[ProposedAction]:
        with self._get_connection() as conn:
            q = "SELECT * FROM proposed_actions WHERE obligation_id = ?" if obligation_id else "SELECT * FROM proposed_actions"
            rows = conn.execute(q, (obligation_id,) if obligation_id else ()).fetchall()
            return [self._hydrate_action(r) for r in rows]

    # ApprovalRequest
    def save_approval_request(self, req: ApprovalRequest) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO approval_requests VALUES (?,?,?,?,?,?,?,?)", (req.id, req.proposed_action_id, req.requested_by, req.approved_by, req.status.value, req.comments, req.created_at.isoformat(), req.decided_at.isoformat() if req.decided_at else None))
            conn.commit()

    def _hydrate_approval(self, r) -> ApprovalRequest:
        d = dict(r)
        d["status"] = ApprovalStatus(d["status"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        if d["decided_at"]:
            d["decided_at"] = datetime.fromisoformat(d["decided_at"])
        return ApprovalRequest(**d)

    def get_approval_request(self, id: str) -> Optional[ApprovalRequest]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (id,)).fetchone()
            return self._hydrate_approval(r) if r else None

    def list_approval_requests(self) -> List[ApprovalRequest]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM approval_requests").fetchall()
            return [self._hydrate_approval(r) for r in rows]

    # ActionExecution
    def save_action_execution(self, ex: ActionExecution) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO action_executions VALUES (?,?,?,?,?,?)", (ex.id, ex.proposed_action_id, ex.executed_by, ex.status, json.dumps(ex.result_artifact), ex.executed_at.isoformat()))
            conn.commit()

    def get_action_execution(self, id: str) -> Optional[ActionExecution]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM action_executions WHERE id = ?", (id,)).fetchone()
            if not r: return None
            return ActionExecution(id=r["id"], proposed_action_id=r["proposed_action_id"], executed_by=r["executed_by"], status=r["status"], result_artifact=json.loads(r["result_artifact"]), executed_at=datetime.fromisoformat(r["executed_at"]))

    # Audit Trail
    def save_audit_event(self, ev: AuditEvent) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO audit_events VALUES (?,?,?,?,?,?,?,?,?)", (ev.id, ev.contract_id, ev.obligation_id, ev.action_type, ev.description, ev.user_or_system, ev.request_id, ev.timestamp.isoformat(), json.dumps(ev.metadata)))
            conn.commit()

    def list_audit_events(self, obligation_id: Optional[str] = None) -> List[AuditEvent]:
        with self._get_connection() as conn:
            q = "SELECT * FROM audit_events WHERE obligation_id = ? ORDER BY timestamp DESC" if obligation_id else "SELECT * FROM audit_events ORDER BY timestamp DESC"
            rows = conn.execute(q, (obligation_id,) if obligation_id else ()).fetchall()
            return [AuditEvent(id=r["id"], contract_id=r["contract_id"], obligation_id=r["obligation_id"], action_type=r["action_type"], description=r["description"], user_or_system=r["user_or_system"], request_id=r["request_id"], timestamp=datetime.fromisoformat(r["timestamp"]), metadata=json.loads(r["metadata"])) for r in rows]
