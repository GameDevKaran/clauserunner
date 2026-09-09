import React, { useEffect, useState } from 'react';
import { Shield, Home, FileText, CheckSquare, List, Activity, Settings, Cpu } from 'lucide-react';
import { fetchHealth } from './api';

import Dashboard from './views/Dashboard';
import Contracts from './views/Contracts';
import ObligationDetail from './views/ObligationDetail';
import Approvals from './views/Approvals';
import AuditTrail from './views/AuditTrail';

export default function App() {
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    async function loadHealth() {
      try {
        const data = await fetchHealth();
        setHealth(data);
      } catch (e) {
        console.error("Health check failed:", e);
      }
    }
    loadHealth();
  }, [currentView]);

  const handleNavigate = (view: string, data?: any) => {
    setCurrentView(view);
    if (data) {
      setSelectedId(data);
    }
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'contracts':
        return <Contracts onNavigate={handleNavigate} />;
      case 'obligation_detail':
        return <ObligationDetail obligationId={selectedId!} onNavigate={handleNavigate} />;
      case 'approvals':
        return <Approvals />;
      case 'audit_trail':
        return <AuditTrail />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="h-full flex overflow-hidden font-sans bg-slate-50 text-slate-700">
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between border-r border-slate-800">
        <div>
          {/* Logo */}
          <div className="p-6 border-b border-slate-800 flex items-center space-x-3 text-white">
            <Shield className="text-brand-500 fill-brand-500/20" size={24} />
            <span className="font-extrabold text-sm uppercase tracking-widest">ClauseRunner</span>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: <Home size={16} /> },
              { id: 'contracts', label: 'Agreements', icon: <FileText size={16} /> },
              { id: 'approvals', label: 'Approval Queue', icon: <CheckSquare size={16} /> },
              { id: 'audit_trail', label: 'Audit Ledger', icon: <List size={16} /> }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => handleNavigate(item.id)}
                className={`w-full p-3 rounded-lg flex items-center space-x-3 text-xs transition-colors font-semibold ${
                  currentView === item.id || (item.id === 'contracts' && currentView === 'obligation_detail')
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'hover:bg-slate-800 hover:text-slate-100 text-slate-400'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Footer / Health indicator */}
        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-slate-500 uppercase font-bold flex items-center"><Activity size={10} className="mr-1 text-green-500 animate-pulse" /> Status</span>
              <span className="text-[9px] bg-green-500/10 text-green-400 px-1.5 py-0.25 rounded font-extrabold uppercase">Online</span>
            </div>
            {health ? (
              <p className="text-[10px] text-slate-400 font-semibold truncate flex items-center">
                <Cpu size={10} className="mr-1" /> {health.agent_mode === 'strands_live_bedrock' ? 'AWS Bedrock Live' : 'Deterministic Mock'}
              </p>
            ) : (
              <p className="text-[10px] text-slate-500">Checking system status...</p>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden h-full">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-100 flex items-center justify-between px-6 shrink-0 shadow-sm">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-slate-800 capitalize">{currentView.replace('_', ' ')}</h2>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            {health?.bedrock_configured ? (
              <span className="bg-green-50 text-green-700 border border-green-200 px-2 py-1 rounded font-bold uppercase text-[9px] flex items-center shadow-sm">
                AWS BEDROCK LIVE
              </span>
            ) : (
              <span className="bg-amber-50 text-amber-700 border border-amber-200 px-2 py-1 rounded font-bold uppercase text-[9px] flex items-center shadow-sm">
                LOCAL MOCK MODE
              </span>
            )}
            <span className="text-slate-400">|</span>
            <span className="text-slate-500 font-semibold">User: Manager</span>
          </div>
        </header>

        {/* View Frame */}
        <main className="flex-1 overflow-hidden min-h-0 bg-slate-50">
          {renderView()}
        </main>
      </div>
    </div>
  );
}
