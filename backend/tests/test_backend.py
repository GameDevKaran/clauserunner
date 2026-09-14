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


# 8. Test DynamoDB codec serialization and pagination
def test_dynamodb_codec_and_pagination():
    import json
    from decimal import Decimal
    from backend.repositories.dynamodb_base import DynamoDBBase, DynamoDBJSONEncoder
    from backend.domain.models import ActionStatus
    
    class MockTable:
        def __init__(self):
            self.items = []
            self.scan_calls = 0
            
        def put_item(self, Item):
            self.items.append(Item)
            
        def scan(self, **kwargs):
            self.scan_calls += 1
            if self.scan_calls == 1:
                return {
                    "Items": [{"PK": "TEST#1", "SK": "METADATA", "val": "first"}],
                    "LastEvaluatedKey": "page1"
                }
            return {
                "Items": [{"PK": "TEST#2", "SK": "METADATA", "val": "second"}]
            }

    base = DynamoDBBase.__new__(DynamoDBBase)
    base.table = MockTable()
    
    assert base._serialize_value(1.5) == Decimal("1.5")
    assert base._serialize_value(datetime(2026, 9, 14)) == "2026-09-14T00:00:00"
    assert base._serialize_value(ActionStatus.DRAFT) == "draft"
    
    nested = {"date": datetime(2026, 9, 14), "status": ActionStatus.DRAFT, "val": Decimal("1.5")}
    serialized_nested = base._serialize_value(nested)
    parsed = json.loads(serialized_nested)
    assert parsed["date"] == "2026-09-14T00:00:00"
    assert parsed["status"] == "draft"
    assert parsed["val"] == 1.5

    all_items = base._scan_by_sk("METADATA")
    assert len(all_items) == 2
    assert base.table.scan_calls == 2

# 9. Test Bedrock Runtime probe and fallback mechanics
def test_bedrock_runtime_probe_and_fallback(monkeypatch):
    from backend.agent.strands_agent import is_bedrock_available
    import botocore.exceptions
    
    class MockBedrockRuntimeClientNotAuthorized:
        def converse(self, **kwargs):
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Operation not allowed"}},
                "Converse"
            )
            
    class MockSessionNotAuthorized:
        def client(self, service_name, **kwargs):
            return MockBedrockRuntimeClientNotAuthorized()
            
    monkeypatch.setattr("boto3.Session", lambda *args, **kwargs: MockSessionNotAuthorized())
    assert is_bedrock_available(force_fresh=True) is False

    class MockBedrockRuntimeClientSuccess:
        def converse(self, **kwargs):
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}
            
    class MockSessionSuccess:
        def client(self, service_name, **kwargs):
            return MockBedrockRuntimeClientSuccess()
            
    monkeypatch.setattr("boto3.Session", lambda *args, **kwargs: MockSessionSuccess())
    assert is_bedrock_available(force_fresh=True) is True

# 10. Test Live Agent Tools Boundary and JSON safety
def test_live_agent_tools_boundary_and_json_safety():
    from backend.tools import INVESTIGATION_TOOLS, ALL_TOOLS
    from backend.tools.write_tools import execute_approved_action
    from backend.repositories.dynamodb_base import DynamoDBJSONEncoder
    
    assert execute_approved_action not in INVESTIGATION_TOOLS
    assert execute_approved_action in ALL_TOOLS
    
    import json
    from backend.services.engine import evaluate_notice_window
    res = evaluate_notice_window(datetime(2027, 1, 1), current_time=datetime(2026, 9, 14))
    serialized = json.dumps(res, cls=DynamoDBJSONEncoder)
    assert "2027-01-01" in serialized

# 11. Test repeatable API-driven Golden SLA workflow and tool idempotency
@pytest.mark.asyncio
async def test_repeatable_api_workflow_and_idempotency():
    repo = init_db(":memory:")
    client = TestClient(app)
    ob_id = "clauserunner-obligation-acme-sla"
    
    res1 = client.post(f"/api/obligations/{ob_id}/investigate")
    assert res1.status_code == 200
    assert len(repo.list_proposed_actions(ob_id)) == 1
    assert len(repo.list_approval_requests()) == 1
    
    res2 = client.post(f"/api/obligations/{ob_id}/investigate")
    assert res2.status_code == 200
    assert res2.json().get("reused_existing_action") is True
    assert len(repo.list_proposed_actions(ob_id)) == 1
    assert len(repo.list_approval_requests()) == 1

    approval = repo.list_approval_requests()[0]
    app_res1 = client.post(f"/api/approvals/{approval.id}/approve", json={"approved_by": "Test Manager", "comments": "Approve SLA"})
    assert app_res1.status_code == 200
    
    app_res2 = client.post(f"/api/approvals/{approval.id}/approve", json={"approved_by": "Test Manager", "comments": "Approve SLA"})
    assert app_res2.status_code == 200
    
    rej_res = client.post(f"/api/approvals/{approval.id}/reject", json={"approved_by": "Test Manager", "comments": "Reject SLA"})
    assert rej_res.status_code == 409

    action = repo.list_proposed_actions(ob_id)[0]
    exec_res1 = client.post(f"/api/actions/{action.id}/execute", json={"executed_by": "Test Operator"})
    assert exec_res1.status_code == 200
    assert repo.get_obligation(ob_id).status == ObligationStatus.COMPLETED

    exec_res2 = client.post(f"/api/actions/{action.id}/execute", json={"executed_by": "Test Operator"})
    assert exec_res2.status_code == 200
    assert exec_res2.json().get("already_executed") is True

    res_new = client.post(f"/api/obligations/{ob_id}/investigate")
    assert res_new.status_code == 200
    assert repo.get_obligation(ob_id).status == ObligationStatus.APPROVAL_REQUIRED
    assert len(repo.list_proposed_actions(ob_id)) == 2
    assert len(repo.list_approval_requests()) == 2

# 12. Test BedrockModel constructor parameters and signature compliance
def test_strands_bedrock_constructor_signature_compliance():
    from strands.models import BedrockModel
    import inspect
    sig = inspect.signature(BedrockModel.__init__)
    assert "boto_client_config" in sig.parameters
    assert "botocore_config" not in sig.parameters

# 13. Test domain SLA evaluation tool results
def test_evaluate_sla_obligation_deterministic_policy():
    repo = init_db(":memory:")
    from backend.repositories.seed import seed_demo_data
    seed_demo_data(repo)
    
    from backend.tools.write_tools import evaluate_sla_obligation
    res = evaluate_sla_obligation("clauserunner-obligation-acme-sla")
    assert res["threshold"] == 99.9
    assert res["measured_uptime"] == 99.4
    assert res["breach_status"] is True
    assert res["tier"] == 1
    assert res["credit_percentage"] == 0.10
    assert res["credit_amount"] == 500.0
    assert "Tier 1 SLA Breach" in res["remedy_description"]

# 14. Test live Bedrock postconditions and security guards
@pytest.mark.asyncio
async def test_live_bedrock_postconditions_and_guards(monkeypatch):
    from backend.agent.strands_agent import run_live_investigation
    repo = init_db(":memory:")
    from backend.repositories.seed import seed_demo_data
    seed_demo_data(repo)
    
    from unittest.mock import MagicMock
    mock_session = MagicMock()
    monkeypatch.setattr("boto3.Session", lambda *args, **kwargs: mock_session)
    
    class FakeAgent:
        def __init__(self, **kwargs):
            pass
        async def invoke_async(self, *args, **kwargs):
            assert "limits" in kwargs
            assert kwargs["limits"]["turns"] == 8
            assert kwargs["limits"]["output_tokens"] == 3000
            assert kwargs["limits"]["total_tokens"] == 12000
            return "Completed"
            
    monkeypatch.setattr("backend.agent.strands_agent.Agent", FakeAgent)
    
    res = await run_live_investigation("clauserunner-obligation-acme-sla")
    assert "error" in res
    assert "incorrect final status" in res["error"]


# 15. Regression test: Stale approved action blocks new Golden SLA cycle
@pytest.mark.asyncio
async def test_regression_stale_approved_action_blocks_new_golden_sla_cycle():
    repo = init_db(":memory:")
    client = TestClient(app)
    obligation_id = "clauserunner-obligation-acme-sla"

    # 1. seed Golden SLA - The seed_demo_data or default setup includes Acme SLA
    from backend.repositories.seed import seed_demo_data
    seed_demo_data(repo)

    # 2. complete one full cycle
    # Run the investigation
    res1 = await run_mock_investigation(obligation_id)
    assert "error" not in res1
    
    # Verify we transitioned to APPROVAL_REQUIRED
    assert repo.get_obligation(obligation_id).status == ObligationStatus.APPROVAL_REQUIRED
    
    # Get the proposed action & approval request
    actions_cycle1 = repo.list_proposed_actions(obligation_id)
    assert len(actions_cycle1) == 1
    action_1 = actions_cycle1[0]
    
    approvals_cycle1 = repo.list_approval_requests()
    assert len(approvals_cycle1) == 1
    approval_1 = approvals_cycle1[0]
    assert approval_1.status == ApprovalStatus.PENDING

    # Approve it
    approve_response = client.post(
        f"/api/approvals/{approval_1.id}/approve",
        json={"approved_by": "Test Manager", "comments": "Approved"},
    )
    assert approve_response.status_code == 200
    
    # 3. leave historical APPROVED approval records intact
    # We approved it, so the approval status is APPROVED.
    # Set the obligation status to COMPLETED directly to simulate a completed cycle.
    ob = repo.get_obligation(obligation_id)
    ob.status = ObligationStatus.COMPLETED
    repo.save_obligation(ob)
    
    # Verify preconditions:
    # - Acme SLA is COMPLETED
    # - ProposedAction is in APPROVED status
    # - ApprovalRequest is in APPROVED status
    assert repo.get_obligation(obligation_id).status == ObligationStatus.COMPLETED
    assert repo.get_proposed_action(action_1.id).status == ActionStatus.APPROVED
    assert repo.list_approval_requests()[0].status == ApprovalStatus.APPROVED

    # 5. trigger investigation again
    res2 = client.post(f"/api/obligations/{obligation_id}/investigate")
    
    # 6. verify HTTP 200
    assert res2.status_code == 200
    
    # 7. verify NEW proposed action is created
    actions_cycle2 = repo.list_proposed_actions(obligation_id)
    # Total actions should be 2 now (historical APPROVED action + new DRAFT action)
    assert len(actions_cycle2) == 2
    
    # Find the new action
    new_action = next(a for a in actions_cycle2 if a.id != action_1.id)
    assert new_action.status == ActionStatus.DRAFT
    
    # 8. verify NEW PENDING approval is created
    # 9. verify historical APPROVED approvals remain
    approvals_all = repo.list_approval_requests()
    assert len(approvals_all) == 2
    
    hist_approval = next(a for a in approvals_all if a.id == approval_1.id)
    new_approval = next(a for a in approvals_all if a.id != approval_1.id)
    
    assert hist_approval.status == ApprovalStatus.APPROVED
    assert new_approval.status == ApprovalStatus.PENDING
    assert new_approval.proposed_action_id == new_action.id
    
    # 10. verify exactly one pending approval for the new cycle
    pending_approvals = [a for a in approvals_all if a.status == ApprovalStatus.PENDING]
    assert len(pending_approvals) == 1
    
    # 11. verify second immediate trigger reuses ONLY the new current-cycle pending action
    res3 = client.post(f"/api/obligations/{obligation_id}/investigate")
    assert res3.status_code == 200
    
    # Total proposed actions should still be 2 (no duplicate action created)
    actions_cycle3 = repo.list_proposed_actions(obligation_id)
    assert len(actions_cycle3) == 2
    
    # Total approval requests should still be 2
    approvals_cycle3 = repo.list_approval_requests()
    assert len(approvals_cycle3) == 2
    
    # 12. verify no duplicate pending approvals
    pending_approvals_3 = [a for a in approvals_cycle3 if a.status == ApprovalStatus.PENDING]
    assert len(pending_approvals_3) == 1



