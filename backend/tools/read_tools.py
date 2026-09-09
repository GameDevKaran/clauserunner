import uuid
from typing import Dict, Any, List, Optional
from strands import tool

from backend.domain.models import ObligationStatus, ActionStatus, ApprovalStatus
from backend.repositories.db import get_repo

@tool(description="Retrieves a contract by its ID.")
def get_contract(contract_id: str) -> Dict[str, Any]:
    repo = get_repo()
    contract = repo.get_contract(contract_id)
    if not contract:
        return {"error": f"Contract with ID '{contract_id}' not found."}
    return contract.dict()

@tool(description="Retrieves a specific clause by its ID.")
def get_clause(clause_id: str) -> Dict[str, Any]:
    repo = get_repo()
    clause = repo.get_clause(clause_id)
    if not clause:
        return {"error": f"Clause with ID '{clause_id}' not found."}
    return clause.dict()

@tool(description="Lists all clauses associated with a specific contract.")
def list_contract_clauses(contract_id: str) -> List[Dict[str, Any]]:
    repo = get_repo()
    clauses = repo.list_contract_clauses(contract_id)
    return [c.dict() for c in clauses]

@tool(description="Lists obligations, optionally filtered by contract ID.")
def list_obligations(contract_id: Optional[str] = None) -> List[Dict[str, Any]]:
    repo = get_repo()
    obligations = repo.list_obligations(contract_id)
    return [o.dict() for o in obligations]

@tool(description="Retrieves a specific obligation by its ID.")
def get_obligation(obligation_id: str) -> Dict[str, Any]:
    repo = get_repo()
    obligation = repo.get_obligation(obligation_id)
    if not obligation:
        return {"error": f"Obligation with ID '{obligation_id}' not found."}
    return obligation.dict()

@tool(description="Lists all evidence artifacts, optionally filtered by obligation ID.")
def list_evidence(obligation_id: Optional[str] = None) -> List[Dict[str, Any]]:
    repo = get_repo()
    evidence = repo.list_evidence(obligation_id)
    return [e.dict() for e in evidence]

@tool(description="Retrieves a specific evidence artifact by its ID.")
def get_evidence(evidence_id: str) -> Dict[str, Any]:
    repo = get_repo()
    ev = repo.get_evidence(evidence_id)
    if not ev:
        return {"error": f"Evidence with ID '{evidence_id}' not found."}
    return ev.dict()

@tool(description="Retrieves the full historical audit trail for an obligation.")
def get_obligation_history(obligation_id: str) -> List[Dict[str, Any]]:
    repo = get_repo()
    events = repo.list_audit_events(obligation_id)
    return [e.dict() for e in events]

@tool(description="Retrieves a specific approval request by its ID.")
def get_approval(approval_request_id: str) -> Dict[str, Any]:
    repo = get_repo()
    req = repo.get_approval_request(approval_request_id)
    if not req:
        return {"error": f"Approval request with ID '{approval_request_id}' not found."}
    return req.dict()
