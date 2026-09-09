import React, { useEffect, useState } from 'react';
import { Shield, Play, ArrowRight, CheckCircle2 } from 'lucide-react';
import { fetchObligation, fetchEvidence, attachEvidence, triggerInvestigation, fetchProposedActions, fetchAuditEvents, triggerActionExecution } from '../api';

export default function ObligationDetail({ obligationId, onNavigate }: { obligationId: string; onNavigate: (v: string, d?: any) => void }) {
  const [ob, setOb] = useState<any>(null);
  const [evList, setEvList] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [audits, setAudits] = useState<any[]>([]);
  const [investigating, setInvestigating] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    try {
      const [obData, evData, actData, auditData] = await Promise.all([
        fetchObligation(obligationId), fetchEvidence(obligationId),
        fetchProposedActions(obligationId), fetchAuditEvents(obligationId)
      ]);
      setOb(obData); setEvList(evData); setActions(actData); setAudits(auditData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, [obligationId]);

  const handleUploadMarch = async () => {
    setLoading(true);
    await attachEvidence(obligationId, {
      name: "Acme March 2026 Availability Report",
      content_type: "application/json",
      file_path_or_url: "/s3/evidence/acme_march_2026.json",
      raw_data_summary: { measured_uptime: 99.4, downtime_minutes: 268 }
    });
    await loadAll();
  };

  const handleInvestigate = async () => {
    setInvestigating(true);
    await triggerInvestigation(obligationId);
    await loadAll();
    setInvestigating(false);
  };

  const handleExecute = async (actionId: string) => {
    setLoading(true);
    const r = await triggerActionExecution(actionId, "System Operator");
    if (r.error) alert(r.error);
    await loadAll();
  };
  return (
    <div className="h-full flex divide-x divide-slate-100 overflow-hidden">
      {/* Left Panel */}
      <div className="w-1/2 overflow-y-auto h-full p-6 space-y-5 bg-slate-50">
        <div>
          <button onClick={() => onNavigate('contracts')} className="text-xs text-brand-600 font-bold hover:underline mb-2 block">&larr; Back to Agreements</button>
          <span className="text-[8px] font-bold px-1.5 py-0.5 bg-brand-50 text-brand-700 border rounded uppercase">{ob.status}</span>
          <h1 className="text-lg font-bold text-slate-800 mt-1">{ob.title}</h1>
          <p className="text-xs text-slate-500 mt-1">{ob.description}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border space-y-1.5 text-xs">
          <h3 className="font-bold text-slate-800">Operational Policy Criteria</h3>
          <div className="grid grid-cols-2 gap-3 text-[10px] pt-1">
            <div><span className="text-slate-400 font-semibold block">Commitment Threshold</span><span className="font-bold text-slate-700">{ob.threshold}</span></div>
            <div><span className="text-slate-400 font-semibold block">Contract Remedy</span><span className="font-bold text-brand-600">{ob.remedy}</span></div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border space-y-3">
          <div className="flex justify-between items-center"><h3 className="text-xs font-bold text-slate-800">Attached Evidence Artifacts</h3>
            {ob.status === 'evidence_required' && evList.length === 0 && (
              <button onClick={handleUploadMarch} className="text-[9px] font-bold text-brand-600 bg-brand-50 hover:bg-brand-100 px-2 py-1 rounded">Load March Logs</button>
            )}
          </div>
          {evList.length === 0 ? <p className="text-[10px] text-slate-400 italic">No evidence attached yet.</p> : (
            <div className="space-y-1.5">
              {evList.map(e => (
                <div key={e.id} className="p-2.5 bg-slate-50 rounded border flex justify-between items-center text-xs">
                  <div><p className="font-bold text-slate-700">{e.name}</p><p className="text-[9px] text-slate-400">Path: {e.file_path_or_url}</p></div>
                  <span className={`text-[8px] font-bold px-1 py-0.25 border rounded uppercase ${e.status === 'verified' ? 'bg-green-50 text-green-700 border-green-100' : 'bg-amber-50 text-amber-700 border-amber-100'}`}>{e.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-slate-900 text-white p-4 rounded-xl space-y-3 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-300 flex items-center"><Shield size={14} className="mr-1 text-brand-500" /> Strands Investigation Agent</h3>
            <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">Autonomous analysis loop. Inspects contract clauses, calculates SLA logs, and drafts remedy actions under code policy.</p>
          </div>
          <button onClick={handleInvestigate} disabled={evList.length === 0 || investigating} className="w-full py-2 bg-brand-500 hover:bg-brand-600 text-white disabled:bg-slate-800 disabled:text-slate-600 rounded-lg text-xs font-bold flex items-center justify-center">
            {investigating ? 'Running agent...' : 'Trigger Strands Investigation'} <Play size={10} className="ml-1 fill-white" />
          </button>
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex-1 overflow-y-auto h-full p-6 space-y-5 bg-white">
        <h2 className="text-xs font-bold text-slate-400 uppercase font-bold tracking-wider">Action & Audit Center</h2>

        {actions.length > 0 && (
          <div className="p-4 bg-slate-50 rounded-xl border space-y-3 border-brand-100">
            <h3 className="text-xs font-bold text-brand-800">Proposed Remedy Claim Draft</h3>
            {actions.map(a => (
              <div key={a.id} className="space-y-2 text-xs">
                <div className="bg-white p-3 rounded border text-[10px] space-y-1">
                  <p><span className="text-slate-400 font-semibold">Recipient:</span> <span className="text-slate-800">{a.draft_payload?.recipient}</span></p>
                  <p><span className="text-slate-400 font-semibold">Subject:</span> <span className="text-slate-800">{a.draft_payload?.subject}</span></p>
                  <p className="text-slate-500 mt-2 border-t pt-1.5 italic">"{a.draft_payload?.body}"</p>
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded border uppercase ${a.status === 'executed' ? 'bg-green-50 text-green-700 border-green-100' : 'bg-rose-50 text-rose-700 border-rose-100'}`}>{a.status}</span>
                  {a.status === 'draft' && <span className="text-[9px] text-rose-600 font-bold">Human Approval Queue</span>}
                  {a.status === 'approved' && <button onClick={() => handleExecute(a.id)} className="py-1 px-2.5 bg-brand-500 hover:bg-brand-600 text-white rounded text-[10px] font-bold">Execute Claim</button>}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-800 font-bold">Visual Operations Audit Trail</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {audits.map(e => (
              <div key={e.id} className="flex items-start space-x-2 text-xs p-2 rounded border border-slate-50 bg-slate-50/50">
                <div className="p-1 bg-brand-50 text-brand-600 rounded mt-0.5"><CheckCircle2 size={10} /></div>
                <div>
                  <p className="font-semibold text-slate-700">{e.description}</p>
                  <p className="text-[9px] text-slate-400">{new Date(e.timestamp).toLocaleString()} &bull; By: {e.user_or_system}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
