import React, { useEffect, useState } from 'react';
import { Clock, Shield, CheckCircle, XCircle, ArrowUpRight, AlertTriangle } from 'lucide-react';
import { fetchApprovals, approveRequest, rejectRequest, fetchProposedActions } from '../api';

export default function Approvals() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [appData, actData] = await Promise.all([fetchApprovals(), fetchProposedActions()]);
      setApprovals(appData);
      setActions(actData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleDecision = async (id: string, approve: boolean) => {
    setLoading(true);
    const comment = approve ? "Approved. SLA Breach verified against server logs." : "Rejected. Insufficient logs.";
    if (approve) {
      await approveRequest(id, "Human Operations Manager", comment);
    } else {
      await rejectRequest(id, "Human Operations Manager", comment);
    }
    await loadData();
  };

  if (loading) return <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div></div>;

  return (
    <div className="p-6 overflow-y-auto h-full space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Human Approval Queue</h1>
        <p className="text-xs text-slate-500 mt-1">Consequential operational and financial actions requiring explicit human authorization.</p>
      </div>

      {approvals.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-2xl border max-w-lg mx-auto">
          <CheckCircle size={40} className="mx-auto text-green-500 mb-3" />
          <h3 className="text-sm font-bold text-slate-800">Approvals Queue Clear</h3>
          <p className="text-xs text-slate-400 mt-1">No pending contractual actions require human verification at this time.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 max-w-4xl">
          {approvals.map(req => {
            const act = actions.find(a => a.id === req.proposed_action_id);
            if (!act) return null;
            return (
              <div key={req.id} className="bg-white p-5 rounded-xl border border-slate-100 flex flex-col justify-between md:flex-row md:items-center gap-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border uppercase ${
                      req.status === 'pending' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                      req.status === 'approved' ? 'bg-green-50 text-green-700 border-green-100' :
                      'bg-rose-50 text-rose-700 border-rose-100'
                    }`}>{req.status}</span>
                    <span className="text-[9px] text-slate-400">Request: {req.id}</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">{act.title}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{act.description}</p>
                  </div>
                  <div className="text-[11px] bg-slate-50 p-3 rounded-lg space-y-1 text-slate-600">
                    <p><span className="text-slate-400 font-bold">Action Type:</span> {act.action_type}</p>
                    <p><span className="text-slate-400 font-bold">Financial Impact:</span> <span className="font-bold text-slate-700">{act.cost_or_impact}</span></p>
                    {req.comments && <p><span className="text-slate-400 font-bold">Comments:</span> "{req.comments}"</p>}
                  </div>
                </div>

                {req.status === 'pending' && (
                  <div className="flex md:flex-col gap-2 justify-end">
                    <button onClick={() => handleDecision(req.id, true)} className="flex-1 md:w-28 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-xs font-bold flex items-center justify-center shadow-sm">
                      <CheckCircle size={12} className="mr-1" /> Approve
                    </button>
                    <button onClick={() => handleDecision(req.id, false)} className="flex-1 md:w-28 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-bold flex items-center justify-center border border-rose-200">
                      <XCircle size={12} className="mr-1" /> Reject
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
