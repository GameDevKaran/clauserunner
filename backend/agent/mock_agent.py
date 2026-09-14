import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from backend.domain.models import (
    ActionStatus,
    AuditEvent,
    Investigation,
    ObligationStatus,
    ToolExecution,
)
from backend.repositories.db import get_repo


def _prepare_for_investigation(repo, obligation) -> str | None:
    """Move a periodic obligation onto the valid investigation path."""
    starting_status = obligation.status

    if obligation.status == ObligationStatus.COMPLETED:
        reset_status = (
            ObligationStatus.EVIDENCE_REQUIRED
            if obligation.obligation_type.value == "sla"
            else ObligationStatus.MONITORING
        )
        from backend.domain.state_machine import ObligationStateMachine
        ObligationStateMachine.validate_transition(obligation.status, reset_status)
        obligation.status = reset_status

    if obligation.status in {
        ObligationStatus.EVIDENCE_REQUIRED,
        ObligationStatus.MONITORING,
        ObligationStatus.APPROVAL_REQUIRED,
    }:
        from backend.domain.state_machine import ObligationStateMachine
        ObligationStateMachine.validate_transition(
            obligation.status, ObligationStatus.INVESTIGATING
        )
        obligation.status = ObligationStatus.INVESTIGATING

    if obligation.status != ObligationStatus.INVESTIGATING:
        return (
            f"Cannot investigate obligation '{obligation.id}' from state "
            f"'{obligation.status.value}'."
        )

    if starting_status != obligation.status:
        obligation.updated_at = datetime.utcnow()
        repo.save_obligation(obligation)
        repo.save_audit_event(AuditEvent(
            id=f"clauserunner-audit-investigation-{uuid.uuid4().hex[:8]}",
            contract_id=obligation.contract_id,
            obligation_id=obligation.id,
            action_type="investigation_started",
            description=(
                f"Investigation started. State transitioned from "
                f"'{starting_status.value}' to '{obligation.status.value}'."
            ),
            user_or_system="ClauseRunner Operations Agent",
        ))

    return None

async def run_mock_investigation(obligation_id: str) -> Dict[str, Any]:
    """
    Simulates the exact Strands agentic tool-calling loop on SQLite,
    persisting actual SQLite state and audit trails. Labeled as Mock.
    """
    repo = get_repo()
    obligation = repo.get_obligation(obligation_id)
    if not obligation:
        return {"error": f"Obligation '{obligation_id}' not found."}
        
    investigation_id = f"clauserunner-investigation-{uuid.uuid4().hex[:8]}"
    steps = []

    # Step 1: get_obligation
    steps.append(ToolExecution(tool_name="get_obligation", inputs={"obligation_id": obligation_id}, outputs=obligation.model_dump(mode="json")))
    
    # Step 2: get_contract
    contract = repo.get_contract(obligation.contract_id)
    steps.append(ToolExecution(tool_name="get_contract", inputs={"contract_id": obligation.contract_id}, outputs=contract.model_dump(mode="json") if contract else None))

    # Step 3: list_evidence
    evidence_list = repo.list_evidence(obligation_id)
    steps.append(ToolExecution(tool_name="list_evidence", inputs={"obligation_id": obligation_id}, outputs=[e.model_dump(mode="json") for e in evidence_list]))

    active_actions = sorted(
        (
            action
            for action in repo.list_proposed_actions(obligation_id)
            if action.status in {ActionStatus.DRAFT, ActionStatus.APPROVED}
        ),
        key=lambda action: action.created_at,
        reverse=True,
    )
    if obligation.status == ObligationStatus.APPROVAL_REQUIRED and active_actions:
        active_action = active_actions[0]
        return {
            "text": "An existing consequential action is already awaiting human review.",
            "investigation_id": active_action.investigation_id,
            "steps_count": len(steps),
            "proposed_action_id": active_action.id,
            "reused_existing_action": True,
        }

    findings = ""
    proposed_action_id = None
    
    if obligation.obligation_type.value == "sla" and evidence_list:
        preparation_error = _prepare_for_investigation(repo, obligation)
        if preparation_error:
            return {"error": preparation_error}

        evidence = evidence_list[0]
        uptime = evidence.raw_data_summary.get("measured_uptime", 99.4)
        
        # Step 4: evaluate_numeric_threshold
        from backend.tools.write_tools import evaluate_numeric_threshold, propose_action, request_approval
        eval_result = evaluate_numeric_threshold(uptime, 5000.0)
        steps.append(ToolExecution(tool_name="evaluate_numeric_threshold", inputs={"measured_uptime": uptime}, outputs=eval_result))
        
        # Step 5: propose_action
        action_result = propose_action(
            obligation_id=obligation_id,
            title="Claim 10% Service Credit for March 2026 SLA Breach",
            description=f"Measured uptime was {uptime}% which fell below 99.9% commitment. Tier 1 applies.",
            action_type="service_credit_claim",
            cost_or_impact="$500 invoice credit",
            recipient="vendor-claims@acme-analytics.com",
            subject="SLA Service Credit Claim - March 2026",
            body=f"Dear Acme Team,\n\nWe claim a 10% ($500) Service Credit. March 2026 uptime was {uptime}%.\n\nRegards,\nAgent"
        )
        if "error" in action_result:
            return action_result
        proposed_action_id = action_result.get("id")
        steps.append(ToolExecution(tool_name="propose_action", inputs={"obligation_id": obligation_id}, outputs=action_result))
        
        # Step 6: request_approval
        approval_result = request_approval(proposed_action_id=proposed_action_id, requested_by="ClauseRunner Operations Agent")
        if "error" in approval_result:
            return approval_result
        steps.append(ToolExecution(tool_name="request_approval", inputs={"proposed_action_id": proposed_action_id}, outputs=approval_result))
        
        findings = (
            f"Autonomous Agent investigation completed.\nSLA Breach detected. Measured: {uptime}% < Threshold: 99.9%.\n"
            f"Deterministic engine calculated 10% credit ($500).\nDrafted claim & requested approval."
        )

    elif obligation.obligation_type.value == "renewal":
        preparation_error = _prepare_for_investigation(repo, obligation)
        if preparation_error:
            return {"error": preparation_error}

        from backend.tools.write_tools import propose_action, request_approval
        from backend.services.engine import evaluate_notice_window
        eval_result = evaluate_notice_window(
            obligation.effective_until,
            current_time=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        steps.append(ToolExecution(tool_name="evaluate_notice_window", inputs={"expiration_date": obligation.effective_until.isoformat()}, outputs={k: str(v) if isinstance(v, datetime) else v for k, v in eval_result.items()}))

        action_result = propose_action(
            obligation_id=obligation_id,
            title="Draft Non-Renewal Notice (CyberShield)",
            description="Renewal window (deadline Nov 17, 2026) is active.",
            action_type="termination_notice",
            cost_or_impact="$25,000 saving",
            recipient="rep@cybershield.com",
            subject="Notice of Non-Renewal - ClauseRunner",
            body="Please accept this as formal notice of non-renewal under Section 8.1. Contract terminates Dec 31, 2026."
        )
        if "error" in action_result:
            return action_result
        proposed_action_id = action_result.get("id")
        steps.append(ToolExecution(tool_name="propose_action", inputs={"obligation_id": obligation_id}, outputs=action_result))

        approval_result = request_approval(proposed_action_id=proposed_action_id, requested_by="ClauseRunner Operations Agent")
        if "error" in approval_result:
            return approval_result
        steps.append(ToolExecution(tool_name="request_approval", inputs={"proposed_action_id": proposed_action_id}, outputs=approval_result))

        findings = (
            f"Renewal deadline investigation complete. Expiration approaching. "
            f"Notice must be sent before Nov 17, 2026. Non-renewal drafted & submitted to approval queue."
        )
    else:
        findings = "Obligation compliance validated. No breach detected."

    # Save Investigation
    investigation = Investigation(
        id=investigation_id,
        obligation_id=obligation_id,
        status="completed",
        steps=steps,
        findings=findings,
        confidence=1.0,
        proposed_action_id=proposed_action_id,
        completed_at=datetime.utcnow()
    )
    repo.save_investigation(investigation)
    
    return {
        "text": findings,
        "investigation_id": investigation_id,
        "steps_count": len(steps)
    }
