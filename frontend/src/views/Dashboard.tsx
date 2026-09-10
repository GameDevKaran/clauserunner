import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, Play, FileText, ArrowRight } from 'lucide-react';
import { fetchContracts, fetchObligations, fetchApprovals, fetchProposedActions } from '../api';

export default function Dashboard({ onNavigate }: { onNavigate: (v: string, d?: any) => void }) {
  const [stats, setStats] = useState({ contracts: 0, pending: 0, approvals: 0, actions: 0 });
  const [urgent, setUrgent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [contracts, obligations, approvals, actions] = await Promise.all([
          fetchContracts(), fetchObligations(), fetchApprovals(), fetchProposedActions()
        ]);
        setStats({
          contracts: contracts.length,
          pending: obligations.filter((o: any) => o.status !== 'completed').length,
          approvals: approvals.filter((a: any) => a.status === 'pending').length,
          actions: actions.length
        });
        setUrgent(obligations.filter((o: any) => ['evidence_required', 'approval_required', 'action_required'].includes(o.status)));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div></div>;

  return (
    <div className="p-6 overflow-y-auto h-full space-y-6">
      <div className="bg-gradient-to-r from-brand-900 via-slate-900 to-slate-950 text-white p-6 rounded-2xl relative overflow-hidden border border-slate-800 shadow-lg">
        <div className="relative z-10 space-y-2">
          <div className="flex items-center space-x-2">
            <span className="bg-brand-500 text-white font-extrabold uppercase text-[9px] px-2 py-0.5 rounded tracking-widest">Active Demo</span>
            <span className="text-slate-500 font-bold text-[9px]">|</span>
            <span className="text-slate-400 text-[10px] font-semibold">Post-Signature Contract Operations Agent</span>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">ClauseRunner</h1>
          <p className="text-sm font-bold text-brand-100 max-w-2xl leading-relaxed">
            Autonomous contract operations with human-controlled execution.
          </p>
          <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
            Signed contracts become actively monitored obligations. ClauseRunner investigates compliance evidence, proposes remedies, and keeps consequential executions (like claiming SLA credits) behind human authorization.
          </p>
          <div className="pt-2 flex items-center space-x-2 text-xs">
            <span className="text-slate-400">👋 Welcome Judge!</span>
            <span className="text-slate-500">•</span>
            <button onClick={() => onNavigate('obligation_detail', 'clauserunner-obligation-acme-sla')} className="text-brand-300 font-bold hover:underline flex items-center">
              Click "Launch Golden SLA" below to start the demo <ArrowRight size={10} className="ml-1" />
            </button>
          </div>
        </div>
        <Shield size={120} className="absolute right-[-20px] top-[-20px] text-brand-500/10 fill-brand-500/5 rotate-12 pointer-events-none" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {[
          { label: 'Contracts', val: stats.contracts, icon: <FileText size={18} />, bg: 'bg-blue-50 text-blue-600' },
          { label: 'Obligations', val: stats.pending, icon: <AlertTriangle size={18} />, bg: 'bg-amber-50 text-amber-600' },
          { label: 'Approvals', val: stats.approvals, icon: <Clock size={18} />, bg: 'bg-rose-50 text-rose-600' },
          { label: 'Actions', val: stats.actions, icon: <CheckCircle size={18} />, bg: 'bg-green-50 text-green-600' }
        ].map((m, i) => (
          <div key={i} className="bg-white p-4 rounded-xl border border-slate-100 flex items-center space-x-3">
            <div className={`p-2.5 rounded-lg ${m.bg}`}>{m.icon}</div>
            <div>
              <p className="text-[10px] text-slate-400 font-semibold uppercase">{m.label}</p>
              <h3 className="text-lg font-bold text-slate-800">{m.val}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-100 lg:col-span-2 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center"><AlertTriangle size={14} className="mr-2 text-amber-500" /> Action Required</h2>
          {urgent.length === 0 ? (
            <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed text-xs text-slate-500">All Operations Clear</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {urgent.map((o: any) => (
                <div key={o.id} className="py-3 first:pt-0 last:pb-0 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <h4 className="text-xs font-bold text-slate-800">{o.title}</h4>
                    <p className="text-[10px] text-slate-400 truncate max-w-xs">{o.description}</p>
                    <div className="flex space-x-2 pt-0.5 items-center">
                      <span className="text-[8px] font-bold px-1.5 py-0.25 bg-amber-50 text-amber-700 rounded uppercase">{o.status}</span>
                      <span className="text-[9px] text-slate-400">Responsible: {o.responsible_party}</span>
                    </div>
                  </div>
                  <button onClick={() => onNavigate('obligation_detail', o.id)} className="text-xs font-bold text-brand-600 bg-brand-50 hover:bg-brand-100 px-3 py-1.5 rounded-lg flex items-center">
                    Open <ArrowRight size={12} className="ml-1" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-100 flex flex-col justify-between space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center"><Play size={14} className="mr-2 text-brand-500" /> Golden SLA Demo</h2>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Checks monthly server log evidence against 99.9% commitment.
            </p>
            <div className="bg-slate-50 p-4 rounded-xl border mt-3 space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-500"><span>Contract</span><span className="font-semibold text-slate-800">Acme SaaS SLA</span></div>
              <div className="flex justify-between text-slate-500"><span>Evidence</span><span className="font-semibold text-rose-600">March 99.4% (Breach)</span></div>
              <div className="flex justify-between text-slate-500"><span>Remedy</span><span className="font-semibold text-slate-800">10% Credit ($500)</span></div>
            </div>
          </div>
          <button onClick={() => onNavigate('obligation_detail', 'clauserunner-obligation-acme-sla')} className="w-full py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-bold text-xs flex items-center justify-center shadow-sm">
            Launch Golden SLA <Play size={10} className="ml-1 fill-white" />
          </button>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center text-[10px] text-slate-400 font-semibold space-y-2 sm:space-y-0">
        <div>
          Built with <span className="text-slate-600 font-bold">Strands Agents SDK</span> &amp; <span className="text-slate-600 font-bold">Amazon Web Services (AWS)</span>
        </div>
        <div className="flex space-x-3">
          <span>S3: <span className="text-green-600 font-bold">Active</span></span>
          <span>DynamoDB: <span className="text-green-600 font-bold">Active</span></span>
          <span>EventBridge: <span className="text-green-600 font-bold">Active</span></span>
          <span>AWS Bedrock: <span className="text-amber-600 font-bold">Pending Auth</span></span>
        </div>
      </div>
    </div>
  );
}
