import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from backend.domain.models import ActionStatus, AuditEvent, Investigation, ObligationStatus, ToolExecution
from backend.repositories.db import get_repo

async def run_mock_investigation(obligation_id: str) -> Dict[str, Any]:
    repo = get_repo()
    from backend.services.investigation_prep import prepare_investigation_cycle
    obligation, active_action, err = prepare_investigation_cycle(obligation_id)
    if err: return {"error": err}
    steps = []
    steps.append(ToolExecution(tool_name="get_obligation", inputs={"obligation_id": obligation_id}, outputs=obligation.model_dump(mode="json")))
    contract = repo.get_contract(obligation.contract_id)
    steps.append(ToolExecution(tool_name="get_contract", inputs={"contract_id": obligation.contract_id}, outputs=contract.model_dump(mode="json") if contract else None))
    evidence_list = repo.list_evidence(obligation_id)
    steps.append(ToolExecution(tool_name="list_evidence", inputs={"obligation_id": obligation_id}, outputs=[e.model_dump(mode="json") for e in evidence_list]))
    if active_action:
        return {
            "text": "An existing consequential action is already awaiting human review.",
            "investigation_id": active_action.investigation_id,
            "steps_count": len(steps),
            "proposed_action_id": active_action.id,
            "reused_existing_action": True,
        }
    findings = ""
    proposed_action_id = None
    investigation_id = f"clauserunner-investigation-{uuid.uuid4().hex[:8]}"
    if obligation.obligation_type.value == "sla" and evidence_list:
        uptime = evidence_list[0].raw_data_summary.get("measured_uptime", 99.4)
        from backend.tools.write_tools import evaluate_numeric_threshold, propose_action, request_approval
        eval_result = evaluate_numeric_threshold(uptime, 5000.0)
        steps.append(ToolExecution(tool_name="evaluate_numeric_threshold", inputs={"measured_uptime": uptime}, outputs=eval_result))
        action_result = propose_action(
            obligation_id=obligation_id, title="Claim 10% Service Credit for March 2026 SLA Breach",
            description=f"Measured uptime was {uptime}% which fell below 99.9% commitment. Tier 1 applies.",
            action_type="service_credit_claim", cost_or_impact="$500 invoice credit",
            recipient="vendor-claims@acme-analytics.com", subject="SLA Service Credit Claim - March 2026",
            body=f"Dear Acme Team,\n\nWe claim a 10% ($500) Service Credit. March 2026 uptime was {uptime}%.\n\nRegards,\nAgent"
        )
        if "error" in action_result: return action_result
        proposed_action_id = action_result.get("id")
        steps.append(ToolExecution(tool_name="propose_action", inputs={"obligation_id": obligation_id}, outputs=action_result))
        approval_result = request_approval(proposed_action_id=proposed_action_id, requested_by="ClauseRunner Operations Agent")
        if "error" in approval_result: return approval_result
        steps.append(ToolExecution(tool_name="request_approval", inputs={"proposed_action_id": proposed_action_id}, outputs=approval_result))
        findings = f"Autonomous Agent investigation completed.\nSLA Breach detected. Measured: {uptime}% < Threshold: 99.9%.\nDeterministic engine calculated 10% credit ($500).\nDrafted claim & requested approval."
    elif obligation.obligation_type.value == "renewal":
        from backend.tools.write_tools import propose_action, request_approval
        from backend.services.engine import evaluate_notice_window
        eval_result = evaluate_notice_window(obligation.effective_until, current_time=datetime.now(timezone.utc).replace(tzinfo=None))
        steps.append(ToolExecution(tool_name="evaluate_notice_window", inputs={"expiration_date": obligation.effective_until.isoformat()}, outputs={k: str(v) if isinstance(v, datetime) else v for k, v in eval_result.items()}))
        action_result = propose_action(
            obligation_id=obligation_id, title="Draft Non-Renewal Notice (CyberShield)",
            description="Renewal window (deadline Nov 17, 2026) is active.",
            action_type="termination_notice", cost_or_impact="$25,000 saving",
            recipient="rep@cybershield.com", subject="Notice of Non-Renewal - ClauseRunner",
            body="Please accept this as formal notice of non-renewal under Section 8.1. Contract terminates Dec 31, 2026."
        )
        if "error" in action_result: return action_result
        proposed_action_id = action_result.get("id")
        steps.append(ToolExecution(tool_name="propose_action", inputs={"obligation_id": obligation_id}, outputs=action_result))
        approval_result = request_approval(proposed_action_id=proposed_action_id, requested_by="ClauseRunner Operations Agent")
        if "error" in approval_result: return approval_result
        steps.append(ToolExecution(tool_name="request_approval", inputs={"proposed_action_id": proposed_action_id}, outputs=approval_result))
        findings = f"Renewal deadline investigation complete. Expiration approaching. Notice must be sent before Nov 17, 2026. Non-renewal drafted & submitted to approval queue."
    else:
        findings = "Obligation compliance validated. No breach detected."
    investigation = Investigation(
        id=investigation_id, obligation_id=obligation_id, status="completed",
        steps=steps, findings=findings, confidence=1.0,
        proposed_action_id=proposed_action_id, completed_at=datetime.utcnow()
    )
    repo.save_investigation(investigation)
    return {"text": findings, "investigation_id": investigation_id, "steps_count": len(steps)}
