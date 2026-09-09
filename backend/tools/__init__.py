from backend.tools.read_tools import (
    get_contract,
    get_clause,
    list_contract_clauses,
    list_obligations,
    get_obligation,
    list_evidence,
    get_evidence,
    get_obligation_history,
    get_approval
)
from backend.tools.write_tools import (
    attach_evidence,
    calculate_deadline,
    evaluate_numeric_threshold,
    propose_action,
    request_approval,
    execute_approved_action,
    record_audit_event
)

ALL_TOOLS = [
    get_contract,
    get_clause,
    list_contract_clauses,
    list_obligations,
    get_obligation,
    list_evidence,
    get_evidence,
    get_obligation_history,
    get_approval,
    attach_evidence,
    calculate_deadline,
    evaluate_numeric_threshold,
    propose_action,
    request_approval,
    execute_approved_action,
    record_audit_event
]
