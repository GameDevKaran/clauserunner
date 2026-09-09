# Devpost Evidence Tracker

This document maps the major ClauseRunner product features and technical claims directly to verified code implementations and tests in our workspace, providing bulletproof evidence for Devpost judging.

---

## 1. Hackathon Claims Map

### Claim: "Uses Strands Agents SDK"
- **Technical Proof**:
  - `requirements.txt` installs `strands-agents>=1.55.1`.
  - `backend/agent/strands_agent.py` imports `Agent` and `BedrockModel` from `strands` to orchestrate our post-signature contract operations.
  - `backend/tools/read_tools.py` and `backend/tools/write_tools.py` register our operational tools using `@strands.tool`.

---

### Claim: "Uses Amazon Bedrock"
- **Technical Proof**:
  - `backend/agent/strands_agent.py` instantiates `strands.models.BedrockModel` using the unpacked model configuration (`model_id` / Claude 3.5 Sonnet on AWS Bedrock).
  - Uses `boto3` client checks (`client = boto3.client("bedrock", region_name=region)`) inside `is_bedrock_available()` to verify live access.

---

### Claim: "Human approval controls consequential actions"
- **Technical Proof**:
  - **Policy-in-Code**: `backend/tools/write_tools.py` under `propose_action` evaluates the proposed action type. If it is `service_credit_claim` or `termination_notice`, `requires_approval = True` is hard-coded into the model.
  - **Execution Guard**: `backend/tools/write_tools.py` under `execute_approved_action` queries the `ApprovalRequest` list to verify if a manager has marked it `APPROVED`. If not, it rejects execution immediately with `"EXECUTION BLOCKED"`.
  - **Automated Test Coverage**: `backend/tests/test_backend.py` under `test_approval_policy_boundary` asserts that executing an unapproved credit claim fails with an execution block, and succeeds after a manager approves it.

---

### Claim: "Deterministic state machine and business calculations"
- **Technical Proof**:
  - **Uptime calculation**: `backend/services/engine.py` under `calculate_sla_remedy` calculates credit compliance and tiers (10% vs 20% credits) deterministically, without delegating numbers to Bedrock.
  - **State Machine rules**: `backend/domain/state_machine.py` defines the valid transition set and enforces it. Any violation throws an `InvalidStateTransition` exception. Tested in `backend/tests/test_backend.py` under `test_state_machine`.

---

### Claim: "Immutable audit trail"
- **Technical Proof**:
  - **Events logging**: Every state-changing tool call (evidence attached, action proposed, approval, execution) automatically commits an `AuditEvent` payload into the SQLite/DynamoDB table.
  - **UI Visualization**: `frontend/src/views/AuditTrail.tsx` fetches and renders the unified timeline showing every single step with a timestamp.
