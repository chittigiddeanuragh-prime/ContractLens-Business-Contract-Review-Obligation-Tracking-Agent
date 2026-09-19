import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, FileText, CheckCircle2, XCircle, Upload, Sun, Moon, Search, Mic, Paperclip, Sparkles } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Default to Dark Mode matching reference design
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('contractlens-theme');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
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
    <div className="min-h-screen flex flex-col justify-between p-4 md:p-6 max-w-[1600px] mx-auto space-y-5 bg-slate-100 dark:bg-[#081621] text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Header Bar with Ask ContractLens floating search bar matching Oracle reference design */}
      <header className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-200 dark:border-[#183a4f] pb-4">
        {/* Logo & Brand */}
        <div
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setView('list')}
        >
          <div className="p-2.5 bg-cyan-500/10 dark:bg-[#0e2636] text-cyan-600 dark:text-cyan-400 rounded-xl border border-cyan-500/30 group-hover:border-cyan-400 transition-all shadow-sm">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              ContractLens AI
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/30 uppercase font-bold tracking-wider">
                Enterprise Risk Platform
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-[#8ba5b5]">Agentic AI Contract Intelligence Engine</p>
          </div>
        </div>

        {/* Floating Top Search Bar ("Ask ContractLens") */}
        <div className="w-full md:w-[480px] relative flex items-center">
          <Search className="w-4 h-4 text-slate-400 dark:text-[#8ba5b5] absolute left-4" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Ask ContractLens AI or search agreements..."
            className="w-full pl-11 pr-16 py-2.5 search-pill text-xs font-medium"
          />
          <div className="absolute right-3 flex items-center gap-1.5 text-slate-400 dark:text-[#8ba5b5]">
            <button className="p-1 hover:text-cyan-400 transition" title="Voice Search">
              <Mic className="w-3.5 h-3.5" />
            </button>
            <button className="p-1 hover:text-cyan-400 transition" title="Attach Document">
              <Paperclip className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Controls: Theme Switcher, Upload Button, Health Pill */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-xl bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-[#133044] transition-all shadow-sm flex items-center gap-1.5 text-xs font-bold"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>

          <button
            onClick={() => setUploadOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-600/20 transition-all active:scale-95"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload PDF
          </button>

          {/* Health Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border bg-white dark:bg-[#0e2636] border-slate-200 dark:border-[#183a4f] shadow-sm">
            <Activity className="w-3.5 h-3.5 text-slate-400 dark:text-[#8ba5b5]" />
            <span className="text-xs font-semibold text-slate-600 dark:text-[#8ba5b5]">API:</span>
            {loading ? (
              <span className="text-xs text-amber-500 animate-pulse font-medium">Connecting...</span>
            ) : isHealthy ? (
              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Healthy</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400 font-bold">
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
            externalSearch={searchQuery}
          />
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-[#183a4f] pt-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 dark:text-[#8ba5b5] gap-4">
        <div className="flex items-center gap-2 bg-amber-50 dark:bg-[#453014]/50 px-3 py-1.5 rounded-lg border border-amber-200 dark:border-amber-900/60">
          <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
          <span className="text-amber-900 dark:text-amber-200">
            <strong className="text-amber-700 dark:text-amber-300">Mandatory Notice:</strong> AI decision support system; does not constitute formal legal counsel.
          </span>
        </div>
        <div className="text-slate-500 dark:text-[#8ba5b5] font-semibold">ContractLens • Agentic AI Hackathon '26</div>
      </footer>
    </div>
  );
}
