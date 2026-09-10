import uuid
from datetime import datetime
from backend.domain.models import ObligationStatus, AuditEvent
from backend.repositories.db import get_repo
from backend.services.engine import evaluate_notice_window

def run_scheduled_check() -> int:
    """
    Scans all tracked obligations in the repository, evaluates deadlines/compliance deterministically,
    and commits operational scheduled-check audit logs.
    """
    repo = get_repo()
    obligations = repo.list_obligations()
    checked_count = 0
    
    current_time = datetime(2026, 9, 10)  # Locked to current timeline date for consistent demo runs
    
    for ob in obligations:
        if ob.status == ObligationStatus.COMPLETED:
            continue
            
        checked_count += 1
        audit_id = f"clauserunner-audit-sched-{uuid.uuid4().hex[:8]}"
        
        if ob.obligation_type.value == "renewal" and ob.status == ObligationStatus.MONITORING:
            # Evaluate renewal window
            res = evaluate_notice_window(ob.deadline, current_time=current_time)
            days = res["days_until_deadline"]
            msg = f"Scheduled check: Obligation '{ob.title}' is {days} days away from notice deadline ({ob.deadline.date()}). Status: {res['status'].upper()}."
            
            repo.save_audit_event(AuditEvent(
                id=audit_id, contract_id=ob.contract_id, obligation_id=ob.id,
                action_type="scheduled_check", description=msg, user_or_system="EventBridge Scheduler"
            ))
            
        elif ob.obligation_type.value == "sla" and ob.status == ObligationStatus.EVIDENCE_REQUIRED:
            msg = f"Scheduled check: SLA Obligation '{ob.title}' is awaiting monthly evidence logs. Claim deadline: {ob.deadline.date()}."
            
            repo.save_audit_event(AuditEvent(
                id=audit_id, contract_id=ob.contract_id, obligation_id=ob.id,
                action_type="scheduled_check", description=msg, user_or_system="EventBridge Scheduler"
            ))
            
        else:
            msg = f"Scheduled check: Verified obligation '{ob.title}' in state '{ob.status.value}'."
            repo.save_audit_event(AuditEvent(
                id=audit_id, contract_id=ob.contract_id, obligation_id=ob.id,
                action_type="scheduled_check", description=msg, user_or_system="EventBridge Scheduler"
            ))
            
    return checked_count
