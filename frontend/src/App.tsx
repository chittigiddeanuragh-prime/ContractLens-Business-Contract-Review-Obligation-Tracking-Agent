import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, FileText, CheckCircle2, XCircle, Upload } from 'lucide-react';
import { ContractList } from './components/ContractList';
import { ContractViewer } from './components/ContractViewer';
import { UploadModal } from './components/UploadModal';

interface HealthData {
  status: string;
  version: string;
  db: string;
  llm_providers: string[];
}

export default function App() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [view, setView] = useState<'list' | 'viewer'>('list');
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState<boolean>(false);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.error('Health check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'ok' && health?.db === 'ok';

  const handleSelectContract = (contractId: string, versionId: string) => {
    setSelectedContractId(contractId);
    setSelectedVersionId(versionId);
    setView('viewer');
  };

  const handleUploadSuccess = (contractId: string, versionId: string) => {
    setSelectedContractId(contractId);
    setSelectedVersionId(versionId);
    setView('viewer');
  };

  return (
    <div className="min-h-screen flex flex-col justify-between p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Navigation Header */}
      <header className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setView('list')}
        >
          <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30 group-hover:border-blue-400 transition-colors">
            <FileText className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              ContractLens
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase font-bold">
                Phase 3 Active
              </span>
            </h1>
            <p className="text-xs text-slate-400">Agentic AI Contract Intelligence Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setUploadOpen(true)}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-blue-600/20 transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload PDF
          </button>

          {/* Health Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border bg-slate-800/80 border-slate-700">
            <Activity className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-medium text-slate-300">API:</span>
            {loading ? (
              <span className="text-xs text-amber-400 animate-pulse">Connecting...</span>
            ) : isHealthy ? (
              <div className="flex items-center gap-1 text-xs text-emerald-400 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Healthy</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs text-red-400 font-semibold">
                <XCircle className="w-3.5 h-3.5" />
                <span>Offline</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1">
        {view === 'viewer' && selectedContractId && selectedVersionId ? (
          <ContractViewer
            contractId={selectedContractId}
            versionId={selectedVersionId}
            onBack={() => setView('list')}
          />
        ) : (
          <ContractList
            onSelectContract={handleSelectContract}
            onOpenUpload={() => setUploadOpen(true)}
          />
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Mandatory Legal Disclaimer Footer (Non-Negotiable Rule #7) */}
      <footer className="border-t border-slate-800 pt-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-400 gap-4">
        <div className="flex items-center gap-2 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-amber-200/90">
            <strong className="text-amber-300">Mandatory Notice:</strong> Assists review; not legal advice.
          </span>
        </div>
        <div className="text-slate-500">ContractLens • Agentic AI Hackathon '26</div>
      </footer>
    </div>
  );
}
