import React, { useEffect, useState } from 'react';
import { CheckCircle2, Shield, Calendar, Terminal, Clock } from 'lucide-react';
import { fetchAuditEvents } from '../api';

export default function AuditTrail() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadEvents() {
      try {
        // Fetch global audit log (passing no obligation_id returns all events)
        const data = await fetchAuditEvents('');
        setEvents(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div></div>;

  return (
    <div className="p-6 overflow-y-auto h-full space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Immutable Audit Ledger</h1>
        <p className="text-xs text-slate-500 mt-1">Immutable, chronological ledger of all autonomous investigations, calculations, human decisions, and action executions.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 max-w-4xl divide-y divide-slate-100 overflow-hidden">
        {events.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs italic">No audit records in ledger.</div>
        ) : (
          events.map(e => (
            <div key={e.id} className="p-4 hover:bg-slate-50/50 flex items-start space-x-4 transition-colors">
              <div className="p-2 bg-brand-50 text-brand-600 rounded-lg mt-0.5">
                <Terminal size={14} />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-800 leading-relaxed">{e.description}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 items-center text-[10px] text-slate-400">
                  <span className="flex items-center"><Clock size={10} className="mr-1" /> {new Date(e.timestamp).toLocaleString()}</span>
                  <span className="font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.25 rounded uppercase">By: {e.user_or_system}</span>
                  <span className="text-slate-300">|</span>
                  <span>ID: {e.id}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
