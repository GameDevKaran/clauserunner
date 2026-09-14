const API_BASE = window.location.port === '5173' ? 'http://localhost:8000/api' : '/api';

async function requestJson(url: string, options?: RequestInit) {
  const r = await fetch(url, options);
  if (r.status === 204) {
    return null;
  }
  const contentType = (r.headers && typeof r.headers.get === 'function') ? r.headers.get("content-type") || "" : "";
  let data: any = null;
  if (contentType.includes("application/json") || (!r.headers && typeof r.json === 'function')) {
    try {
      data = await r.json();
    } catch (e) {}
  }
  const isOk = r.ok !== undefined ? r.ok : true;
  if (!isOk) {
    let errMsg = `HTTP ${r.status || 500}`;
    if (data) {
      if (data.detail) {
        errMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } else if (data.error) {
        errMsg = data.error;
      }
    } else {
      try {
        if (typeof r.text === 'function') {
          const txt = await r.text();
          if (txt && txt.length < 200) {
            errMsg = txt;
          }
        }
      } catch (e) {}
    }
    throw new Error(errMsg);
  }
  return data;
}

export async function fetchHealth() {
  return requestJson(`${API_BASE}/health`);
}

export async function fetchContracts() {
  return requestJson(`${API_BASE}/contracts`);
}

export async function fetchContract(id: string) {
  return requestJson(`${API_BASE}/contracts/${id}`);
}

export async function fetchContractClauses(id: string) {
  return requestJson(`${API_BASE}/contracts/${id}/clauses`);
}

export async function fetchObligations(contractId?: string) {
  const url = contractId ? `${API_BASE}/obligations?contract_id=${contractId}` : `${API_BASE}/obligations`;
  return requestJson(url);
}

export async function fetchObligation(id: string) {
  return requestJson(`${API_BASE}/obligations/${id}`);
}

export async function fetchEvidence(obligationId: string) {
  return requestJson(`${API_BASE}/obligations/${obligationId}/evidence`);
}

export async function attachEvidence(obligationId: string, payload: { name: string; content_type: string; file_path_or_url: string; raw_data_summary: any }) {
  return requestJson(`${API_BASE}/obligations/${obligationId}/evidence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

export async function fetchAuditEvents(obligationId?: string, limit?: number, offset = 0) {
  const baseUrl = obligationId ? `${API_BASE}/obligations/${obligationId}/audit` : `${API_BASE}/audit`;
  const query = [
    limit !== undefined ? `limit=${limit}` : '',
    offset > 0 ? `offset=${offset}` : ''
  ].filter(Boolean).join('&');
  const url = query ? `${baseUrl}?${query}` : baseUrl;
  return requestJson(url);
}

export async function triggerInvestigation(obligationId: string) {
  return requestJson(`${API_BASE}/obligations/${obligationId}/investigate`, {
    method: 'POST'
  });
}

export async function fetchApprovals() {
  return requestJson(`${API_BASE}/approvals`);
}

export async function approveRequest(approvalId: string, approvedBy: string, comments?: string) {
  return requestJson(`${API_BASE}/approvals/${approvalId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy, comments })
  });
}

export async function rejectRequest(approvalId: string, approvedBy: string, comments?: string) {
  return requestJson(`${API_BASE}/approvals/${approvalId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy, comments })
  });
}

export async function fetchProposedActions(obligationId?: string) {
  const url = obligationId ? `${API_BASE}/actions?obligation_id=${obligationId}` : `${API_BASE}/actions`;
  return requestJson(url);
}

export async function triggerActionExecution(actionId: string, executedBy: string) {
  return requestJson(`${API_BASE}/actions/${actionId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ executed_by: executedBy })
  });
}
