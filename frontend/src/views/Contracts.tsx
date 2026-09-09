import React, { useEffect, useState } from 'react';
import { FileText, Shield, User, Calendar, ArrowRight, BookOpen } from 'lucide-react';
import { fetchContracts, fetchContractClauses, fetchObligations } from '../api';

export default function Contracts({ onNavigate }: { onNavigate: (v: string, d?: any) => void }) {
  const [contracts, setContracts] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [clauses, setClauses] = useState<any[]>([]);
  const [obligations, setObligations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContracts() {
      const data = await fetchContracts();
      setContracts(data);
      if (data.length > 0) setSelectedId(data[0].id);
      setLoading(false);
    }
    loadContracts().catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    async function loadDetails() {
      const [cData, oData] = await Promise.all([
        fetchContractClauses(selectedId!), fetchObligations(selectedId!)
      ]);
      setClauses(cData);
      setObligations(oData);
    }
    loadDetails().catch(console.error);
  }, [selectedId]);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div></div>;
  const active = contracts.find(c => c.id === selectedId);

  return (
    <div className="h-full flex divide-x divide-slate-100 overflow-hidden">
      <div className="w-64 bg-white h-full overflow-y-auto p-4 space-y-3">
        <h2 className="text-[10px] font-bold text-slate-400 uppercase">Agreements</h2>
        <div className="space-y-1">
          {contracts.map(c => (
            <button key={c.id} onClick={() => setSelectedId(c.id)} className={`w-full p-2.5 text-left rounded-lg flex items-center space-x-2 text-xs truncate ${c.id === selectedId ? 'bg-brand-50 text-brand-700 font-bold' : 'hover:bg-slate-50 text-slate-600'}`}>
              <FileText size={14} /><span className="truncate">{c.name}</span>
            </button>
          ))}
        </div>
      </div>

      {active && (
        <div className="flex-1 bg-slate-50 h-full overflow-y-auto p-6 space-y-6">
          <div>
            <span className="text-[8px] font-bold px-1.5 py-0.5 bg-green-50 text-green-700 border border-green-100 rounded-full uppercase">Active</span>
            <h1 className="text-lg font-bold text-slate-900 mt-1">{active.name}</h1>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Counterparty', val: active.counterparty, icon: <User size={14} /> },
              { label: 'Signed At', val: new Date(active.signed_at).toLocaleDateString(), icon: <Calendar size={14} /> },
              { label: 'Effective Date', val: new Date(active.effective_date).toLocaleDateString(), icon: <Shield size={14} /> }
            ].map((d, i) => (
              <div key={i} className="bg-white p-3 rounded-lg border border-slate-100 flex items-center space-x-2 text-xs">
                <div className="text-slate-400">{d.icon}</div>
                <div>
                  <p className="text-[8px] text-slate-400 uppercase">{d.label}</p>
                  <p className="font-bold text-slate-800">{d.val}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-lg border space-y-3">
              <h2 className="text-xs font-bold text-slate-900 flex items-center"><BookOpen size={14} className="mr-1.5 text-brand-500" /> Clauses</h2>
              <div className="space-y-2.5 overflow-y-auto max-h-80 pr-1">
                {clauses.map(c => (
                  <div key={c.id} className="p-2.5 bg-slate-50 rounded border text-[10px]">
                    <div className="flex justify-between font-bold text-brand-700 mb-1"><span>{c.number} {c.title}</span></div>
                    <p className="text-slate-500 italic">"{c.text}"</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-5 rounded-lg border space-y-3">
              <h2 className="text-xs font-bold text-slate-900 flex items-center"><Shield size={14} className="mr-1.5 text-brand-500" /> Obligations</h2>
              <div className="space-y-2 overflow-y-auto max-h-80 pr-1">
                {obligations.map(o => (
                  <div key={o.id} className="p-2.5 bg-slate-50 rounded border flex items-center justify-between text-xs">
                    <div>
                      <h4 className="font-bold text-slate-800 text-[11px]">{o.title}</h4>
                      <div className="flex space-x-1.5 items-center mt-1">
                        <span className="text-[8px] font-bold px-1 bg-brand-50 text-brand-700 rounded uppercase">{o.status}</span>
                        <span className="text-[9px] text-slate-400">Deadline: {o.deadline ? new Date(o.deadline).toLocaleDateString() : 'N/A'}</span>
                      </div>
                    </div>
                    <button onClick={() => onNavigate('obligation_detail', o.id)} className="p-1.5 bg-brand-50 hover:bg-brand-100 text-brand-600 rounded">
                      <ArrowRight size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
