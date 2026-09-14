import hashlib
from datetime import datetime, timezone
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
    
    current_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    for ob in obligations:
        if ob.status == ObligationStatus.COMPLETED:
            continue
            
        checked_count += 1
        if ob.obligation_type.value == "renewal" and ob.status == ObligationStatus.MONITORING:
            # Evaluate renewal window
            res = evaluate_notice_window(ob.deadline, current_time=current_time)
            days = res["days_until_deadline"]
            msg = f"Scheduled check: Obligation '{ob.title}' is {days} days away from notice deadline ({ob.deadline.date()}). Status: {res['status'].upper()}."
            
        elif ob.obligation_type.value == "sla" and ob.status == ObligationStatus.EVIDENCE_REQUIRED:
            msg = f"Scheduled check: SLA Obligation '{ob.title}' is awaiting monthly evidence logs. Claim deadline: {ob.deadline.date()}."
        else:
            msg = f"Scheduled check: Verified obligation '{ob.title}' in state '{ob.status.value}'."

        # A five-minute rule should not append the same logical observation forever.
        # A changed state, deadline, or daily countdown produces a different event.
        event_key = f"{ob.id}|{ob.status.value}|{msg}"
        audit_id = f"clauserunner-audit-sched-{hashlib.sha256(event_key.encode('utf-8')).hexdigest()[:16]}"
        if repo.get_audit_event(audit_id) is None:
            repo.save_audit_event(AuditEvent(
                id=audit_id, contract_id=ob.contract_id, obligation_id=ob.id,
                action_type="scheduled_check", description=msg, user_or_system="EventBridge Rule"
            ))
            
    return checked_count
