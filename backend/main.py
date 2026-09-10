import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.domain.models import (
    Contract, Clause, Obligation, EvidenceArtifact, AuditEvent,
    ApprovalRequest, ApprovalStatus, ProposedAction, ActionStatus, ActionExecution
)
from backend.repositories.db import get_repo, init_db
from backend.agent.strands_agent import is_bedrock_available, run_investigation
from backend.tools.write_tools import execute_approved_action, attach_evidence
from backend.services.logger import logger

app = FastAPI(title="ClauseRunner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db("clauserunner.sqlite")
    logger.info("Initializing ClauseRunner FastAPI application server...")


class EvidenceCreate(BaseModel):
    name: str
    content_type: str
    file_path_or_url: str
    raw_data_summary: Dict[str, Any]

class ApprovalDecision(BaseModel):
    approved_by: str
    comments: Optional[str] = None

class ExecutionTrigger(BaseModel):
    executed_by: str

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    bedrock_ok = is_bedrock_available()
    logger.info("Health check endpoint called", extra={"extra_fields": {"bedrock_ok": bedrock_ok}})
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "dynamodb" if os.environ.get("CLAUSERUNNER_DYNAMODB_TABLE") else "sqlite_local",
        "agent_mode": "strands_live_bedrock" if bedrock_ok else "strands_deterministic_mock",
        "bedrock_configured": bedrock_ok,
    }



@app.get("/api/contracts", response_model=List[Contract])
def get_contracts():
    return get_repo().list_contracts()

@app.get("/api/contracts/{id}", response_model=Contract)
def get_contract(id: str):
    c = get_repo().get_contract(id)
    if not c: raise HTTPException(404, "Contract not found")
    return c

@app.get("/api/contracts/{id}/clauses", response_model=List[Clause])
def get_contract_clauses(id: str):
    return get_repo().list_contract_clauses(id)

@app.get("/api/obligations", response_model=List[Obligation])
def get_obligations(contract_id: Optional[str] = None):
    return get_repo().list_obligations(contract_id)

@app.get("/api/obligations/{id}", response_model=Obligation)
def get_obligation(id: str):
    ob = get_repo().get_obligation(id)
    if not ob: raise HTTPException(404, "Obligation not found")
    return ob

@app.get("/api/obligations/{id}/evidence", response_model=List[EvidenceArtifact])
def get_obligation_evidence(id: str):
    return get_repo().list_evidence(id)

@app.post("/api/obligations/{id}/evidence", response_model=EvidenceArtifact)
def upload_obligation_evidence(id: str, payload: EvidenceCreate):
    logger.info("Evidence upload triggered", extra={"extra_fields": {"obligation_id": id, "evidence_name": payload.name}})
    res = attach_evidence(obligation_id=id, name=payload.name, content_type=payload.content_type, file_path_or_url=payload.file_path_or_url, raw_data_summary=payload.raw_data_summary)
    if "error" in res: raise HTTPException(400, res["error"])
    return get_repo().get_evidence(res["id"])

@app.get("/api/obligations/{id}/audit", response_model=List[AuditEvent])
def get_obligation_audit(id: str):
    return get_repo().list_audit_events(id)

@app.post("/api/obligations/{id}/investigate")
async def trigger_investigation(id: str):
    logger.info("Strands Agent investigation triggered", extra={"extra_fields": {"obligation_id": id}})
    res = await run_investigation(id)
    if "error" in res: raise HTTPException(400, res["error"])
    return res

@app.get("/api/approvals", response_model=List[ApprovalRequest])
def list_approvals():
    return get_repo().list_approval_requests()

@app.post("/api/approvals/{id}/approve", response_model=ApprovalRequest)
def approve_request(id: str, decision: ApprovalDecision):
    repo = get_repo()
    req = repo.get_approval_request(id)
    if not req: raise HTTPException(404, "Approval request not found")
    req.status = ApprovalStatus.APPROVED
    req.approved_by = decision.approved_by
    req.comments = decision.comments
    req.decided_at = datetime.utcnow()
    repo.save_approval_request(req)

    action = repo.get_proposed_action(req.proposed_action_id)
    if action:
        action.status = ActionStatus.APPROVED
        action.updated_at = datetime.utcnow()
        repo.save_proposed_action(action)
        repo.save_audit_event(AuditEvent(
            id=f"audit-app-{id[:8]}", contract_id="unknown", obligation_id=action.obligation_id,
            action_type="approval_granted", description=f"Human approved action: '{action.title}'. Comments: {decision.comments or ''}",
            user_or_system=decision.approved_by
        ))
    return req

@app.post("/api/approvals/{id}/reject", response_model=ApprovalRequest)
def reject_request(id: str, decision: ApprovalDecision):
    repo = get_repo()
    req = repo.get_approval_request(id)
    if not req: raise HTTPException(404, "Approval request not found")
    req.status = ApprovalStatus.REJECTED
    req.approved_by = decision.approved_by
    req.comments = decision.comments
    req.decided_at = datetime.utcnow()
    repo.save_approval_request(req)

    action = repo.get_proposed_action(req.proposed_action_id)
    if action:
        action.status = ActionStatus.REJECTED
        action.updated_at = datetime.utcnow()
        repo.save_proposed_action(action)
        repo.save_audit_event(AuditEvent(
            id=f"audit-rej-{id[:8]}", contract_id="unknown", obligation_id=action.obligation_id,
            action_type="approval_rejected", description=f"Human rejected action: '{action.title}'. Reason: {decision.comments or ''}",
            user_or_system=decision.approved_by
        ))
    return req

@app.post("/api/actions/{id}/execute")
def trigger_action_execution(id: str, payload: ExecutionTrigger):
    res = execute_approved_action(proposed_action_id=id, executed_by=payload.executed_by)
    if "error" in res: raise HTTPException(400, res["error"])
    return res

@app.get("/api/actions", response_model=List[ProposedAction])
def list_proposed_actions(obligation_id: Optional[str] = None):
    return get_repo().list_proposed_actions(obligation_id)


from backend.services.checker import run_scheduled_check

@app.post("/api/obligations/check-all")
def trigger_scheduled_check():
    count = run_scheduled_check()
    return {"status": "success", "checked_obligations_count": count}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# SPA catch-all routing for any deep-linking page refreshes
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    if not request.url.path.startswith("/api") and os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    raise exc

# Serve pre-compiled React static assets
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


