import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.domain.models import ObligationStatus, ObligationType, ApprovalStatus, ActionStatus
from backend.domain.state_machine import ObligationStateMachine, InvalidStateTransition
from backend.services.engine import calculate_sla_remedy, evaluate_notice_window
from backend.repositories.sqlite_repo import SQLiteRepository
from backend.repositories.db import init_db, get_repo
from backend.tools.write_tools import propose_action, request_approval, execute_approved_action
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

