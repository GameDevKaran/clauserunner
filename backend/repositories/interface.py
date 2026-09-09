from typing import List, Optional
from backend.domain.models import (
    Contract, Clause, Obligation, EvidenceArtifact, Investigation, 
    ProposedAction, ApprovalRequest, ActionExecution, AuditEvent
)

class StorageInterface:
    """Interface for ClauseRunner persistence layer."""
    def save_contract(self, contract: Contract) -> None: raise NotImplementedError
    def get_contract(self, contract_id: str) -> Optional[Contract]: raise NotImplementedError
    def list_contracts(self) -> List[Contract]: raise NotImplementedError
    
    def save_clause(self, clause: Clause) -> None: raise NotImplementedError
    def get_clause(self, clause_id: str) -> Optional[Clause]: raise NotImplementedError
    def list_contract_clauses(self, contract_id: str) -> List[Clause]: raise NotImplementedError
    
    def save_obligation(self, obligation: Obligation) -> None: raise NotImplementedError
    def get_obligation(self, obligation_id: str) -> Optional[Obligation]: raise NotImplementedError
    def list_obligations(self, contract_id: Optional[str] = None) -> List[Obligation]: raise NotImplementedError
    
    def save_evidence(self, evidence: EvidenceArtifact) -> None: raise NotImplementedError
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceArtifact]: raise NotImplementedError
    def list_evidence(self, obligation_id: Optional[str] = None) -> List[EvidenceArtifact]: raise NotImplementedError
    
    def save_investigation(self, investigation: Investigation) -> None: raise NotImplementedError
    def get_investigation(self, investigation_id: str) -> Optional[Investigation]: raise NotImplementedError
    
    def save_proposed_action(self, action: ProposedAction) -> None: raise NotImplementedError
    def get_proposed_action(self, action_id: str) -> Optional[ProposedAction]: raise NotImplementedError
    def list_proposed_actions(self, obligation_id: Optional[str] = None) -> List[ProposedAction]: raise NotImplementedError
    
    def save_approval_request(self, request: ApprovalRequest) -> None: raise NotImplementedError
    def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]: raise NotImplementedError
    def list_approval_requests(self) -> List[ApprovalRequest]: raise NotImplementedError
    
    def save_action_execution(self, execution: ActionExecution) -> None: raise NotImplementedError
    def get_action_execution(self, execution_id: str) -> Optional[ActionExecution]: raise NotImplementedError
    
    def save_audit_event(self, event: AuditEvent) -> None: raise NotImplementedError
    def list_audit_events(self, obligation_id: Optional[str] = None) -> List[AuditEvent]: raise NotImplementedError
