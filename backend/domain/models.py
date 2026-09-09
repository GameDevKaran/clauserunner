from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ObligationStatus(str, Enum):
    PENDING = "pending"
    MONITORING = "monitoring"
    EVIDENCE_REQUIRED = "evidence_required"
    INVESTIGATING = "investigating"
    ACTION_REQUIRED = "action_required"
    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"

class ObligationType(str, Enum):
    SLA = "sla"
    RENEWAL = "renewal"
    COMPLIANCE = "compliance"
    OTHER = "other"

class EvidenceStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"

class ActionType(str, Enum):
    SERVICE_CREDIT_CLAIM = "service_credit_claim"
    RENEWAL_NOTICE = "renewal_notice"
    TERMINATION_NOTICE = "termination_notice"
    COMPLIANCE_SUBMISSION = "compliance_submission"
    INTERNAL_ALERT = "internal_alert"

class ActionStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Contract(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    counterparty: str
    signed_at: datetime
    effective_date: datetime
    status: str
    raw_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Clause(BaseModel):
    id: str
    contract_id: str
    number: str
    title: str
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Obligation(BaseModel):
    id: str
    contract_id: str
    source_clause_id: str
    title: str
    description: str
    obligation_type: ObligationType
    responsible_party: str
    counterparty: str
    effective_from: datetime
    effective_until: datetime
    trigger: Optional[str] = None
    deadline: Optional[datetime] = None
    measurement_period: Optional[str] = None  # e.g., "monthly", "annually"
    evidence_requirements: str
    threshold: Optional[str] = None  # e.g., "99.9" for uptime, or "30 days"
    remedy: Optional[str] = None
    approval_policy: bool = True  # True if financial/external, requiring human signoff
    status: ObligationStatus = ObligationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EvidenceArtifact(BaseModel):
    id: str
    obligation_id: str
    name: str
    content_type: str
    file_path_or_url: str
    raw_data_summary: Dict[str, Any] = Field(default_factory=dict)  # e.g. {"uptime_percentage": 99.4}
    status: EvidenceStatus = EvidenceStatus.UNVERIFIED
    upload_date: datetime = Field(default_factory=datetime.utcnow)

class ToolExecution(BaseModel):
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Investigation(BaseModel):
    id: str
    obligation_id: str
    status: str  # "ongoing", "completed", "failed"
    steps: List[ToolExecution] = Field(default_factory=list)
    findings: Optional[str] = None
    confidence: float = 1.0
    proposed_action_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ProposedAction(BaseModel):
    id: str
    obligation_id: str
    investigation_id: str
    title: str
    description: str
    action_type: ActionType
    cost_or_impact: Optional[str] = None  # e.g., "$500 service credit"
    requires_approval: bool = True
    draft_payload: Dict[str, Any] = Field(default_factory=dict)  # e.g. {"recipient": "vendor@abc.com", "subject": "Claim...", "body": "..."}
    status: ActionStatus = ActionStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ApprovalRequest(BaseModel):
    id: str
    proposed_action_id: str
    requested_by: str
    approved_by: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None

class ActionExecution(BaseModel):
    id: str
    proposed_action_id: str
    executed_by: str
    status: str  # "success", "failed"
    result_artifact: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.utcnow)

class AuditEvent(BaseModel):
    id: str
    contract_id: str
    obligation_id: Optional[str] = None
    action_type: str  # e.g. "obligation_created", "investigation_started", "approval_granted"
    description: str
    user_or_system: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
