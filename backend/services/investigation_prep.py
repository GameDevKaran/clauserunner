import uuid
from typing import Optional, Tuple
from datetime import datetime
from backend.domain.models import Obligation, ObligationStatus, ActionStatus, AuditEvent, ProposedAction
from backend.domain.state_machine import ObligationStateMachine
from backend.repositories.db import get_repo

def prepare_investigation_cycle(obligation_id: str) -> Tuple[Optional[Obligation], Optional[ProposedAction], Optional[str]]:
    """
    Unifies the deterministic investigation-cycle preparation for both fallback and live paths.
    Validates state machine rules, detects existing active actions, and transitions statuses safely.
    """
    repo = get_repo()
    obligation = repo.get_obligation(obligation_id)
    if not obligation:
        return None, None, f"Obligation '{obligation_id}' not found."

    # Active workflow statuses where we allow reusing existing actions
    active_workflow_statuses = {
        ObligationStatus.INVESTIGATING,
        ObligationStatus.APPROVAL_REQUIRED,
        ObligationStatus.ACTION_REQUIRED
    }

    # 1. Inspect existing proposed actions
    actions = repo.list_proposed_actions(obligation_id)
    active_actions = []
    
    if obligation.status in active_workflow_statuses:
        # Search for the most recent "investigation_started" audit event to determine current cycle
        audits = repo.list_audit_events(obligation_id)
        last_reset_dt = None
        for a in audits:
            if a.action_type == "investigation_started":
                last_reset_dt = a.timestamp
                break
                
        for a in actions:
            if a.status in {ActionStatus.DRAFT, ActionStatus.APPROVED}:
                if last_reset_dt is None or a.created_at >= last_reset_dt:
                    active_actions.append(a)
    
    # 2. If an active DRAFT or APPROVED action exists, reuse it and do not restart the cycle
    if active_actions:
        return obligation, active_actions[0], None

    old_status = obligation.status
    target_status = ObligationStatus.INVESTIGATING

    if old_status == ObligationStatus.COMPLETED:
        # COMPLETED periodic SLA/renewal cycle reset
        inter_status = (
            ObligationStatus.EVIDENCE_REQUIRED
            if obligation.obligation_type.value == "sla"
            else ObligationStatus.MONITORING
        )
        try:
            # Transition COMPLETED -> Intermediate
            ObligationStateMachine.validate_transition(old_status, inter_status)
            obligation.status = inter_status
            obligation.updated_at = datetime.utcnow()
            repo.save_obligation(obligation)
            
            repo.save_audit_event(AuditEvent(
                id=f"clauserunner-audit-prep-{uuid.uuid4().hex[:8]}",
                contract_id=obligation.contract_id, obligation_id=obligation.id,
                action_type="scheduled_check",
                description=f"Periodic cycle reset. Transitioned from '{old_status.value}' to '{inter_status.value}'.",
                user_or_system="ClauseRunner Operations Agent"
            ))
            
            # Transition Intermediate -> INVESTIGATING
            ObligationStateMachine.validate_transition(inter_status, target_status)
            obligation.status = target_status
            obligation.updated_at = datetime.utcnow()
            repo.save_obligation(obligation)
            
            repo.save_audit_event(AuditEvent(
                id=f"clauserunner-audit-prep-{uuid.uuid4().hex[:8]}",
                contract_id=obligation.contract_id, obligation_id=obligation.id,
                action_type="investigation_started",
                description=f"Investigation started. Transitioned from '{inter_status.value}' to '{target_status.value}'.",
                user_or_system="ClauseRunner Operations Agent"
            ))
        except Exception as e:
            return None, None, f"Periodic cycle reset failed: {str(e)}"
            
    elif old_status in {ObligationStatus.EVIDENCE_REQUIRED, ObligationStatus.MONITORING, ObligationStatus.APPROVAL_REQUIRED}:
        # Transition directly to INVESTIGATING (or recover APPROVAL_REQUIRED without action)
        try:
            ObligationStateMachine.validate_transition(old_status, target_status)
            obligation.status = target_status
            obligation.updated_at = datetime.utcnow()
            repo.save_obligation(obligation)
            
            repo.save_audit_event(AuditEvent(
                id=f"clauserunner-audit-prep-{uuid.uuid4().hex[:8]}",
                contract_id=obligation.contract_id, obligation_id=obligation.id,
                action_type="investigation_started",
                description=f"Investigation started. Transitioned from '{old_status.value}' to '{target_status.value}'.",
                user_or_system="ClauseRunner Operations Agent"
            ))
        except Exception as e:
            return None, None, f"State transition to INVESTIGATING failed: {str(e)}"
            
    elif old_status == ObligationStatus.INVESTIGATING:
        pass
    else:
        return None, None, f"Cannot investigate obligation '{obligation_id}' from state '{old_status.value}'."

    return obligation, None, None
