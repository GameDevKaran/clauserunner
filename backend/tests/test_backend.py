import os
import re
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.domain.models import AuditEvent, ObligationStatus, ObligationType, ApprovalStatus, ActionStatus
from backend.domain.state_machine import ObligationStateMachine, InvalidStateTransition
from backend.services.engine import calculate_sla_remedy, evaluate_notice_window
from backend.repositories.sqlite_repo import SQLiteRepository
from backend.repositories.db import init_db, get_repo
from backend.tools.write_tools import propose_action, request_approval, execute_approved_action
from backend.agent.mock_agent import run_mock_investigation
from backend.main import app

# 1. Test Deterministic SLA calculations
def test_sla_calculations():
    # Compliant case
    res1 = calculate_sla_remedy(99.95)
    assert not res1["is_breached"]
    assert res1["tier"] == 0
    assert res1["credit_amount"] == 0.0

    # Tier 1 breach case
    res2 = calculate_sla_remedy(99.4)
    assert res2["is_breached"]
    assert res2["tier"] == 1
    assert res2["credit_percentage"] == 0.10
    assert res2["credit_amount"] == 500.0

    # Tier 2 breach case
    res3 = calculate_sla_remedy(98.5)
    assert res3["is_breached"]
    assert res3["tier"] == 2
    assert res3["credit_percentage"] == 0.20
    assert res3["credit_amount"] == 1000.0

# 2. Test Obligation State Machine
def test_state_machine():
    # Valid transition
    ObligationStateMachine.validate_transition(ObligationStatus.PENDING, ObligationStatus.MONITORING)
    
    # Same state transition is valid
    ObligationStateMachine.validate_transition(ObligationStatus.MONITORING, ObligationStatus.MONITORING)

    # Invalid transitions should throw
    with pytest.raises(InvalidStateTransition):
        ObligationStateMachine.validate_transition(ObligationStatus.PENDING, ObligationStatus.COMPLETED)
        
    with pytest.raises(InvalidStateTransition):
        ObligationStateMachine.validate_transition(ObligationStatus.COMPLETED, ObligationStatus.INVESTIGATING)

# 3. Test Repository & Seeding
def test_repository_and_seed():
    # Use memory database
    repo = SQLiteRepository(":memory:")
    contracts = repo.list_contracts()
    assert len(contracts) == 2
    
    acme_contract = repo.get_contract("clauserunner-contract-acme")
    assert acme_contract is not None
    assert acme_contract.counterparty == "Acme Cloud Solutions LLC"
    
    clauses = repo.list_contract_clauses("clauserunner-contract-acme")
    assert len(clauses) == 2
    
    obligations = repo.list_obligations()
    assert len(obligations) == 3

# 4. Test Human Approval Boundary
def test_approval_policy_boundary():
    # Initialize global in-memory DB for tools testing
    repo = init_db(":memory:")
    
    # We should have our seeded SLA obligation in EVIDENCE_REQUIRED
    ob_id = "clauserunner-obligation-acme-sla"
    ob = repo.get_obligation(ob_id)
    assert ob.status == ObligationStatus.EVIDENCE_REQUIRED
    
    # Transition to INVESTIGATING before proposing an action (as required by the state machine rules!)
    ob.status = ObligationStatus.INVESTIGATING
    repo.save_obligation(ob)
    
    # Propose a service credit claim (which requires approval)
    action = propose_action.__wrapped__(
        obligation_id=ob_id,
        title="SLA Refund",
        description="Claiming credit",
        action_type="service_credit_claim",
        cost_or_impact="$500",
        recipient="claims@vendor.com",
        subject="Claim",
        body="Refund body"
    )
    assert action["requires_approval"] is True
    assert action["status"] == ActionStatus.DRAFT.value
    
    # Check that obligation transitioned to APPROVAL_REQUIRED
    updated_ob = repo.get_obligation(ob_id)
    assert updated_ob.status == ObligationStatus.APPROVAL_REQUIRED

    # Try to execute the action WITHOUT approval. Should be BLOCKED.
    exec_res = execute_approved_action.__wrapped__(proposed_action_id=action["id"], executed_by="Test Runner")
    assert "error" in exec_res
    assert "EXECUTION BLOCKED" in exec_res["error"]
    
    # Status should still be APPROVAL_REQUIRED
    assert repo.get_obligation(ob_id).status == ObligationStatus.APPROVAL_REQUIRED

    # Create an approval request
    req = request_approval.__wrapped__(proposed_action_id=action["id"], requested_by="Test Agent")
    assert req["status"] == ApprovalStatus.PENDING.value
    
    # Approve it
    req_obj = repo.get_approval_request(req["id"])
    req_obj.status = ApprovalStatus.APPROVED
    repo.save_approval_request(req_obj)
    
    # Update action status
    action_obj = repo.get_proposed_action(action["id"])
    action_obj.status = ActionStatus.APPROVED
    repo.save_proposed_action(action_obj)

    # Try executing now. Should SUCCEED.
    exec_res2 = execute_approved_action.__wrapped__(proposed_action_id=action["id"], executed_by="Manager")
    assert "error" not in exec_res2
    assert exec_res2["status"] == "success"
    
    # Obligation should now be COMPLETED
    assert repo.get_obligation(ob_id).status == ObligationStatus.COMPLETED

# 5. Test FastAPI Integration
def test_api_integration():
    init_db(":memory:")
    client = TestClient(app)
    
    # Test Health Endpoint
    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"
    
    # Test Contracts List
    resp_contracts = client.get("/api/contracts")
    assert resp_contracts.status_code == 200
    assert len(resp_contracts.json()) == 2
    
    # Test Obligations List
    resp_obs = client.get("/api/obligations")
    assert resp_obs.status_code == 200
    assert len(resp_obs.json()) == 3


def test_global_and_obligation_audit_endpoints():
    repo = init_db(":memory:")
    client = TestClient(app)

    acme_event = AuditEvent(
        id="audit-api-global-acme",
        contract_id="clauserunner-contract-acme",
        obligation_id="clauserunner-obligation-acme-sla",
        action_type="test_event",
        description="Global audit endpoint test event.",
        user_or_system="Test Suite",
    )
    cyber_event = AuditEvent(
        id="audit-api-global-cyber",
        contract_id="clauserunner-contract-cybershield",
        obligation_id="clauserunner-obligation-cyber-soc2",
        action_type="test_event",
        description="Obligation audit endpoint test event.",
        user_or_system="Test Suite",
    )
    repo.save_audit_event(acme_event)
    repo.save_audit_event(cyber_event)

    global_response = client.get("/api/audit")
    assert global_response.status_code == 200
    global_ids = {event["id"] for event in global_response.json()}
    assert acme_event.id in global_ids
    assert cyber_event.id in global_ids

    obligation_response = client.get(
        "/api/obligations/clauserunner-obligation-acme-sla/audit"
    )
    assert obligation_response.status_code == 200
    obligation_events = obligation_response.json()
    assert acme_event.id in {event["id"] for event in obligation_events}
    assert cyber_event.id not in {event["id"] for event in obligation_events}

    first_page = client.get("/api/audit?limit=1")
    second_page = client.get("/api/audit?limit=1&offset=1")
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]

    obligation_page = client.get(
        "/api/obligations/clauserunner-obligation-acme-sla/audit?limit=1"
    )
    assert obligation_page.status_code == 200
    assert len(obligation_page.json()) == 1


# 6. Test Scheduled Checker Capability
def test_scheduled_checker():
    # Use memory database
    repo = init_db(":memory:")
    
    from backend.services.checker import run_scheduled_check
    count = run_scheduled_check()
    assert count == 2  # Seeder creates 3 obligations, 1 is completed (SOC 2), so 2 active obligations are checked!
    
    # Verify that scheduled_check audit events are created
    audits = repo.list_audit_events()
    sched_events = [a for a in audits if a.action_type == "scheduled_check"]
    assert len(sched_events) == 2
    assert "Scheduled check" in sched_events[0].description
    assert all(event.user_or_system == "EventBridge Rule" for event in sched_events)

    renewal = repo.get_obligation("clauserunner-obligation-cyber-renewal")
    renewal_event = next(event for event in sched_events if event.obligation_id == renewal.id)
    reported_days = int(re.search(r"is (-?\d+) days away", renewal_event.description).group(1))
    expected_days = (
        renewal.deadline - datetime.now(timezone.utc).replace(tzinfo=None)
    ).days
    assert reported_days in {expected_days, expected_days - 1}
    assert f"({renewal.deadline.date()})" in renewal_event.description

    # Re-running an unchanged check must not grow the ledger with duplicates.
    count_again = run_scheduled_check()
    sched_events_again = [
        a for a in repo.list_audit_events() if a.action_type == "scheduled_check"
    ]
    assert count_again == 2
    assert len(sched_events_again) == 2


@pytest.mark.asyncio
async def test_golden_sla_workflow_is_repeatable_and_idempotent():
    repo = init_db(":memory:")
    client = TestClient(app)
    obligation_id = "clauserunner-obligation-acme-sla"

    # The intended fixture already includes 99.4% evidence but starts pre-investigation.
    assert repo.get_obligation(obligation_id).status == ObligationStatus.EVIDENCE_REQUIRED
    assert repo.list_evidence(obligation_id)[0].raw_data_summary["measured_uptime"] == 99.4

    first_run = await run_mock_investigation(obligation_id)
    assert "error" not in first_run
    assert repo.get_obligation(obligation_id).status == ObligationStatus.APPROVAL_REQUIRED
    assert len(repo.list_proposed_actions(obligation_id)) == 1
    assert len(repo.list_approval_requests()) == 1

    # A repeated click while approval is pending reuses the active action.
    repeated_run = await run_mock_investigation(obligation_id)
    assert repeated_run["reused_existing_action"] is True
    assert len(repo.list_proposed_actions(obligation_id)) == 1
    assert len(repo.list_approval_requests()) == 1

    approval = repo.list_approval_requests()[0]
    approve_response = client.post(
        f"/api/approvals/{approval.id}/approve",
        json={"approved_by": "Test Manager", "comments": "Verified."},
    )
    assert approve_response.status_code == 200

    action = repo.list_proposed_actions(obligation_id)[0]
    execute_response = client.post(
        f"/api/actions/{action.id}/execute",
        json={"executed_by": "Test Operator"},
    )
    assert execute_response.status_code == 200
    assert repo.get_obligation(obligation_id).status == ObligationStatus.COMPLETED

    # The periodic SLA can start a new clean cycle after completion.
    second_cycle = await run_mock_investigation(obligation_id)
    assert "error" not in second_cycle
    assert repo.get_obligation(obligation_id).status == ObligationStatus.APPROVAL_REQUIRED
    assert len(repo.list_proposed_actions(obligation_id)) == 2
    assert len(repo.list_approval_requests()) == 2

# 7. Test Bedrock Provider Fallback Logic
def test_bedrock_provider_live_state():
    from backend.agent.strands_agent import is_bedrock_available
    # If no keys or profiles are configured in test runner, should default to False
    import os
    orig_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    orig_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    orig_profile = os.environ.get("AWS_PROFILE")
    
    try:
        # Force unset credentials to simulate mock environment
        if "AWS_ACCESS_KEY_ID" in os.environ: del os.environ["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in os.environ: del os.environ["AWS_SECRET_ACCESS_KEY"]
        if "AWS_PROFILE" in os.environ: del os.environ["AWS_PROFILE"]
        
        assert is_bedrock_available() is False
    finally:
        # Restore original credentials
        if orig_access_key: os.environ["AWS_ACCESS_KEY_ID"] = orig_access_key
        if orig_secret: os.environ["AWS_SECRET_ACCESS_KEY"] = orig_secret
        if orig_profile: os.environ["AWS_PROFILE"] = orig_profile

