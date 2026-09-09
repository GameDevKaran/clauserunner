import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from strands import tool

from backend.domain.models import (
    EvidenceArtifact, EvidenceStatus, ProposedAction, ActionType, ActionStatus,
    ApprovalRequest, ApprovalStatus, ActionExecution, AuditEvent, ObligationStatus
)
from backend.domain.state_machine import ObligationStateMachine
from backend.services.engine import calculate_sla_remedy, calculate_remediation_deadline
from backend.repositories.db import get_repo

@tool(description="Attaches a new evidence artifact to an obligation.")
def attach_evidence(obligation_id: str, name: str, content_type: str, file_path_or_url: str, raw_data_summary: Dict[str, Any]) -> Dict[str, Any]:
    repo = get_repo()
    obligation = repo.get_obligation(obligation_id)
    if not obligation:
        return {"error": f"Obligation '{obligation_id}' not found."}
    
    evidence_id = f"clauserunner-evidence-{uuid.uuid4().hex[:8]}"
    evidence = EvidenceArtifact(
        id=evidence_id, obligation_id=obligation_id, name=name,
        content_type=content_type, file_path_or_url=file_path_or_url,
        raw_data_summary=raw_data_summary, status=EvidenceStatus.UNVERIFIED
    )
    repo.save_evidence(evidence)
    
    # Transition obligation state to INVESTIGATING
    old_status = obligation.status
    try:
        ObligationStateMachine.validate_transition(old_status, ObligationStatus.INVESTIGATING)
        obligation.status = ObligationStatus.INVESTIGATING
        obligation.updated_at = datetime.utcnow()
        repo.save_obligation(obligation)
    except Exception as e:
        return {"error": f"State transition failed: {str(e)}"}

    # Audit log
    audit_id = f"clauserunner-audit-{uuid.uuid4().hex[:8]}"
    repo.save_audit_event(AuditEvent(
        id=audit_id, contract_id=obligation.contract_id, obligation_id=obligation_id,
        action_type="evidence_attached", description=f"Evidence '{name}' attached. State transitioned from {old_status.value} to {obligation.status.value}.",
        user_or_system="System"
    ))
    return evidence.dict()

@tool(description="Deterministically calculates a claim or remediation deadline from a month end date.")
def calculate_deadline(month_end_iso: str, claim_window_days: int = 30) -> str:
    month_end = datetime.fromisoformat(month_end_iso)
    deadline = calculate_remediation_deadline(month_end, claim_window_days)
    return deadline.isoformat()

@tool(description="Deterministically evaluates SLA uptime logs to calculate breach details and financial remedies.")
def evaluate_numeric_threshold(measured_uptime: float, base_monthly_fee: float = 5000.0) -> Dict[str, Any]:
    return calculate_sla_remedy(measured_uptime, base_monthly_fee)

@tool(description="Records a manual audit event for traceability.")
def record_audit_event(contract_id: str, obligation_id: str, action_type: str, description: str, user_or_system: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    repo = get_repo()
    event_id = f"clauserunner-audit-{uuid.uuid4().hex[:8]}"
    event = AuditEvent(
        id=event_id, contract_id=contract_id, obligation_id=obligation_id,
        action_type=action_type, description=description, user_or_system=user_or_system,
        metadata=metadata or {}
    )
    repo.save_audit_event(event)
    return event.dict()

@tool(description="Proposes an operational or financial action. Consequential actions (financial/termination) require human approval.")
def propose_action(obligation_id: str, title: str, description: str, action_type: str, cost_or_impact: str, recipient: str, subject: str, body: str) -> Dict[str, Any]:
    repo = get_repo()
    obligation = repo.get_obligation(obligation_id)
    if not obligation:
        return {"error": f"Obligation '{obligation_id}' not found."}

    # Enforce Approval Policy in Code
    consequential_types = {ActionType.SERVICE_CREDIT_CLAIM.value, ActionType.RENEWAL_NOTICE.value, ActionType.TERMINATION_NOTICE.value}
    requires_approval = action_type in consequential_types or obligation.approval_policy

    action_id = f"clauserunner-action-{uuid.uuid4().hex[:8]}"
    investigation_id = f"clauserunner-investigation-{uuid.uuid4().hex[:8]}"
    
    proposed_action = ProposedAction(
        id=action_id, obligation_id=obligation_id, investigation_id=investigation_id,
        title=title, description=description, action_type=ActionType(action_type),
        cost_or_impact=cost_or_impact, requires_approval=requires_approval,
        draft_payload={"recipient": recipient, "subject": subject, "body": body},
        status=ActionStatus.DRAFT
    )
    repo.save_proposed_action(proposed_action)

    # Transition obligation state to ACTION_REQUIRED or APPROVAL_REQUIRED
    old_status = obligation.status
    target_status = ObligationStatus.APPROVAL_REQUIRED if requires_approval else ObligationStatus.ACTION_REQUIRED
    try:
        ObligationStateMachine.validate_transition(old_status, target_status)
        obligation.status = target_status
        obligation.updated_at = datetime.utcnow()
        repo.save_obligation(obligation)
    except Exception as e:
        return {"error": f"State transition failed: {str(e)}"}

    # Audit log
    audit_id = f"clauserunner-audit-{uuid.uuid4().hex[:8]}"
    repo.save_audit_event(AuditEvent(
        id=audit_id, contract_id=obligation.contract_id, obligation_id=obligation_id,
        action_type="action_proposed", description=f"Proposed action '{title}' ({action_type}). Requires approval: {requires_approval}.",
        user_or_system="System"
    ))
    return proposed_action.dict()

@tool(description="Submits a formal request for human approval of a proposed action.")
def request_approval(proposed_action_id: str, requested_by: str) -> Dict[str, Any]:
    repo = get_repo()
    action = repo.get_proposed_action(proposed_action_id)
    if not action:
        return {"error": f"Proposed action '{proposed_action_id}' not found."}

    approval_id = f"clauserunner-approval-{uuid.uuid4().hex[:8]}"
    request = ApprovalRequest(
        id=approval_id, proposed_action_id=proposed_action_id,
        requested_by=requested_by, status=ApprovalStatus.PENDING
    )
    repo.save_approval_request(request)

    # Audit log
    repo.save_audit_event(AuditEvent(
        id=f"clauserunner-audit-{uuid.uuid4().hex[:8]}", contract_id="unknown", obligation_id=action.obligation_id,
        action_type="approval_requested", description=f"Requested human approval for action '{action.title}'.",
        user_or_system=requested_by
    ))
    return request.dict()

@tool(description="Executes an action, validating human approval boundaries for consequential actions.")
def execute_approved_action(proposed_action_id: str, executed_by: str) -> Dict[str, Any]:
    repo = get_repo()
    action = repo.get_proposed_action(proposed_action_id)
    if not action:
        return {"error": f"Proposed action '{proposed_action_id}' not found."}

    obligation = repo.get_obligation(action.obligation_id)
    if not obligation:
        return {"error": f"Obligation '{action.obligation_id}' not found."}

    # Enforce Approval Policy
    if action.requires_approval:
        approvals = repo.list_approval_requests()
        matching_approval = next((a for a in approvals if a.proposed_action_id == proposed_action_id and a.status == ApprovalStatus.APPROVED), None)
        if not matching_approval:
            return {"error": "EXECUTION BLOCKED: Human approval is strictly required but has not been granted."}

    # Transition Action and Obligation Statuses
    action.status = ActionStatus.EXECUTED
    action.updated_at = datetime.utcnow()
    repo.save_proposed_action(action)

    old_status = obligation.status
    try:
        ObligationStateMachine.validate_transition(old_status, ObligationStatus.COMPLETED)
        obligation.status = ObligationStatus.COMPLETED
        obligation.updated_at = datetime.utcnow()
        repo.save_obligation(obligation)
    except Exception as e:
        return {"error": f"State transition failed: {str(e)}"}

    # Save Execution
    exec_id = f"clauserunner-exec-{uuid.uuid4().hex[:8]}"
    execution = ActionExecution(
        id=exec_id, proposed_action_id=proposed_action_id,
        executed_by=executed_by, status="success",
        result_artifact={"executed_payload": action.draft_payload, "dispatched_at": datetime.utcnow().isoformat()}
    )
    repo.save_action_execution(execution)

    # Audit log
    repo.save_audit_event(AuditEvent(
        id=f"clauserunner-audit-{uuid.uuid4().hex[:8]}", contract_id=obligation.contract_id, obligation_id=obligation.id,
        action_type="action_executed", description=f"Successfully executed action '{action.title}' by {executed_by}.",
        user_or_system=executed_by
    ))
    return execution.dict()
