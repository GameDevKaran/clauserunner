const API_BASE = 'http://localhost:8000/api';

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}

export async function fetchContracts() {
  const r = await fetch(`${API_BASE}/contracts`);
  return r.json();
}

export async function fetchContract(id: string) {
  const r = await fetch(`${API_BASE}/contracts/${id}`);
  return r.json();
}

export async function fetchContractClauses(id: string) {
  const r = await fetch(`${API_BASE}/contracts/${id}/clauses`);
  return r.json();
}

export async function fetchObligations(contractId?: string) {
  const url = contractId ? `${API_BASE}/obligations?contract_id=${contractId}` : `${API_BASE}/obligations`;
  const r = await fetch(url);
  return r.json();
}

export async function fetchObligation(id: string) {
  const r = await fetch(`${API_BASE}/obligations/${id}`);
  return r.json();
}

export async function fetchEvidence(obligationId: string) {
  const r = await fetch(`${API_BASE}/obligations/${obligationId}/evidence`);
  return r.json();
}

export async function attachEvidence(obligationId: string, payload: { name: string; content_type: string; file_path_or_url: string; raw_data_summary: any }) {
  const r = await fetch(`${API_BASE}/obligations/${obligationId}/evidence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return r.json();
}

export async function fetchAuditEvents(obligationId: string) {
  const r = await fetch(`${API_BASE}/obligations/${obligationId}/audit`);
  return r.json();
}

export async function triggerInvestigation(obligationId: string) {
  const r = await fetch(`${API_BASE}/obligations/${obligationId}/investigate`, {
    method: 'POST'
  });
  return r.json();
}

export async function fetchApprovals() {
  const r = await fetch(`${API_BASE}/approvals`);
  return r.json();
}

export async function approveRequest(approvalId: string, approvedBy: string, comments?: string) {
  const r = await fetch(`${API_BASE}/approvals/${approvalId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy, comments })
  });
  return r.json();
}

export async function rejectRequest(approvalId: string, approvedBy: string, comments?: string) {
  const r = await fetch(`${API_BASE}/approvals/${approvalId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy, comments })
  });
  return r.json();
}

export async function fetchProposedActions(obligationId?: string) {
  const url = obligationId ? `${API_BASE}/actions?obligation_id=${obligationId}` : `${API_BASE}/actions`;
  const r = await fetch(url);
  return r.json();
}

export async function triggerActionExecution(actionId: string, executedBy: string) {
  const r = await fetch(`${API_BASE}/actions/${actionId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ executed_by: executedBy })
  });
  return r.json();
}
