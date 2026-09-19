import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, FileText, CheckCircle2, XCircle, Upload, Sun, Moon } from 'lucide-react';
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

  // Dark / Light Theme State
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('contractlens-theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('contractlens-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  };

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
    <div className="min-h-screen flex flex-col justify-between p-4 md:p-8 max-w-7xl mx-auto space-y-6 bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Navigation Header */}
      <header className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setView('list')}
        >
          <div className="p-2.5 bg-indigo-600/10 dark:bg-indigo-600/20 text-indigo-600 dark:text-indigo-400 rounded-xl border border-indigo-500/30 group-hover:border-indigo-500 transition-colors">
            <FileText className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              ContractLens
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 uppercase font-bold tracking-wider">
                Enterprise AI
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Agentic Contract Intelligence & Risk Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Theme Switcher Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all shadow-sm flex items-center gap-1.5 text-xs font-semibold"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Theme`}
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-indigo-600" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>

          <button
            onClick={() => setUploadOpen(true)}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all active:scale-95"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload PDF
          </button>

          {/* Health Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm">
            <Activity className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">API:</span>
            {loading ? (
              <span className="text-xs text-amber-500 animate-pulse font-medium">Connecting...</span>
            ) : isHealthy ? (
              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Healthy</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400 font-semibold">
                <XCircle className="w-3.5 h-3.5 text-red-500" />
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

      {/* Mandatory Legal Disclaimer Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 pt-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-4">
        <div className="flex items-center gap-2 bg-amber-50 dark:bg-amber-950/40 px-3 py-1.5 rounded-lg border border-amber-200 dark:border-amber-900/60">
          <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
          <span className="text-amber-900 dark:text-amber-200">
            <strong className="text-amber-700 dark:text-amber-300">Mandatory Notice:</strong> AI decision assist tool; not formal legal advice.
          </span>
        </div>
        <div className="text-slate-500 dark:text-slate-500 font-medium">ContractLens • Agentic AI Hackathon '26</div>
      </footer>
    </div>
  );
}
