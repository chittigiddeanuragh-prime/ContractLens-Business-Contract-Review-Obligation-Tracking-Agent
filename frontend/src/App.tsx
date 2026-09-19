import { useEffect, useState } from 'react';
import {
  Activity,
  FileText,
  CheckCircle2,
  XCircle,
  Upload,
  Search,
  Mic,
  Paperclip,
  LayoutDashboard,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { ContractList } from './components/ContractList';
import { ContractViewer } from './components/ContractViewer';
import { UploadModal } from './components/UploadModal';
import { ThemeToggle } from './components/ui/ThemeToggle';
import { StatCard } from './components/ui/StatCard';
import { DonutChart } from './components/ui/DonutChart';
import { Card } from './components/ui/Card';
import { Badge } from './components/ui/Badge';

interface HealthData {
  status: string;
  version: string;
  db: string;
  llm_providers: string[];
}

export default function App() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'contracts' | 'obligations' | 'risk'>('dashboard');
  const [view, setView] = useState<'list' | 'viewer'>('list');
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

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
      setLoadingHealth(false);
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

  const riskChartData = [
    { label: 'Critical Risk', value: 12, color: '#ef4444' },
    { label: 'Moderate Risk', value: 25, color: '#f59e0b' },
    { label: 'Compliant / Good', value: 58, color: '#10b981' },
    { label: 'Info / Standard', value: 18, color: '#0ea5e9' },
  ];

  return (
    <div className="min-h-screen flex bg-slate-100 dark:bg-[#081621] text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Sidebar Navigation matching Oracle AI Compliance Portal */}
      <aside className="w-64 hidden md:flex flex-col justify-between border-r border-slate-200 dark:border-[#183a4f] bg-white dark:bg-[#091b27] p-4 shrink-0">
        <div className="space-y-6">
          {/* Logo & Platform Title */}
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => { setView('list'); setActiveTab('dashboard'); }}
          >
            <div className="p-2.5 bg-cyan-500/10 dark:bg-[#0e2636] text-cyan-600 dark:text-cyan-400 rounded-xl border border-cyan-500/30 group-hover:border-cyan-400 transition-all shadow-sm">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
                ContractLens
                <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/30 uppercase font-bold">
                  AI 2.0
                </span>
              </h1>
              <p className="text-[11px] text-slate-500 dark:text-[#8ba5b5]">Enterprise Risk Engine</p>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="space-y-1">
            <button
              onClick={() => { setActiveTab('dashboard'); setView('list'); }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'dashboard' && view === 'list'
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-600 dark:text-[#8ba5b5] hover:bg-slate-100 dark:hover:bg-[#0e2636] hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Executive Dashboard</span>
            </button>

            <button
              onClick={() => { setActiveTab('contracts'); setView('list'); }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'contracts' && view === 'list'
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-600 dark:text-[#8ba5b5] hover:bg-slate-100 dark:hover:bg-[#0e2636] hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Contract Portfolio</span>
            </button>

            <button
              onClick={() => { setActiveTab('obligations'); setView('list'); }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'obligations' && view === 'list'
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-600 dark:text-[#8ba5b5] hover:bg-slate-100 dark:hover:bg-[#0e2636] hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>Obligations & Deadlines</span>
            </button>

            <button
              onClick={() => { setActiveTab('risk'); setView('list'); }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeTab === 'risk' && view === 'list'
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                  : 'text-slate-600 dark:text-[#8ba5b5] hover:bg-slate-100 dark:hover:bg-[#0e2636] hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Risk & Anomalies</span>
            </button>
          </nav>
        </div>

        {/* System Health Status in Sidebar Footer */}
        <div className="pt-4 border-t border-slate-200 dark:border-[#183a4f] space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 dark:text-[#8ba5b5] font-semibold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> Backend Engine
            </span>
            {loadingHealth ? (
              <span className="text-[11px] text-amber-500 animate-pulse font-bold">Checking...</span>
            ) : isHealthy ? (
              <span className="text-[11px] text-emerald-500 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Online
              </span>
            ) : (
              <span className="text-[11px] text-red-500 font-bold flex items-center gap-1">
                <XCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-[#648498] text-center">
            ContractLens v1.0 • Grounded Citation QA
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-white/80 dark:bg-[#081621]/80 backdrop-blur-md border-b border-slate-200 dark:border-[#183a4f] px-4 md:px-6 py-3 flex items-center justify-between gap-4">
          {/* Ask ContractLens Floating Search Bar */}
          <div className="flex-1 max-w-xl relative flex items-center">
            <Search className="w-4 h-4 text-slate-400 dark:text-[#8ba5b5] absolute left-4" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask ContractLens AI or search agreements, clauses, risk terms..."
              className="w-full pl-11 pr-16 py-2 search-pill text-xs font-medium"
            />
            <div className="absolute right-3 flex items-center gap-1 text-slate-400 dark:text-[#8ba5b5]">
              <button className="p-1 hover:text-cyan-400 transition" title="Voice Search">
                <Mic className="w-3.5 h-3.5" />
              </button>
              <button className="p-1 hover:text-cyan-400 transition" title="Attach Document">
                <Paperclip className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-3">
            <ThemeToggle />

            <button
              onClick={() => setUploadOpen(true)}
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-600/20 transition-all active:scale-95"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload PDF
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto w-full">
          {view === 'viewer' && selectedContractId && selectedVersionId ? (
            <ContractViewer
              contractId={selectedContractId}
              versionId={selectedVersionId}
              onBack={() => setView('list')}
            />
          ) : activeTab === 'dashboard' ? (
            <div className="space-y-6">
              {/* Executive Summary & KPI Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Total Contracts in Scope"
                  value="1,538"
                  subtitle="Across all business units"
                  icon={FileText}
                  trendText="↑ 12% vs last quarter"
                  color="cyan"
                />
                <StatCard
                  title="Overall Compliance Rate"
                  value="89%"
                  subtitle="1,368 contracts fully compliant"
                  icon={CheckCircle2}
                  trendText="✓ Standard terms verified"
                  color="emerald"
                />
                <StatCard
                  title="Critical Overdue Items"
                  value="38"
                  subtitle="Requires immediate review"
                  icon={ShieldAlert}
                  trendText="! Action needed in 7 days"
                  color="red"
                />
                <StatCard
                  title="Market Anomalies"
                  value="17"
                  subtitle="Non-standard liability terms"
                  icon={AlertTriangle}
                  trendText="⚠ High liability caps"
                  color="amber"
                />
              </div>

              {/* Chart & Attention Panel Row matching Oracle Reference Design */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Risk Distribution Donut Chart */}
                <Card className="lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-[#183a4f]">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        Risk Distribution & Category Breakdown
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-[#8ba5b5] mt-0.5">
                        Categorized liability, indemnity, and termination risk terms verified by code.
                      </p>
                    </div>
                    <Badge variant="good">Verified Engine</Badge>
                  </div>
                  <DonutChart data={riskChartData} totalLabel="Active Risk Terms" size={160} />
                </Card>

                {/* Urgent Attention Panel */}
                <Card className="space-y-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-[#183a4f]">
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-red-500" /> High-Risk Priority
                      </h3>
                      <Badge variant="critical">Action Required</Badge>
                    </div>

                    <div className="divide-y divide-slate-100 dark:divide-[#183a4f] mt-2">
                      <div className="py-3 space-y-1">
                        <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                          <span>Master Cloud Services Agreement</span>
                          <span className="text-red-500 text-[11px]">Uncapped Liability</span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-[#8ba5b5]">
                          Clause 14.2 contains unlimited consequential damages exposure for data loss.
                        </p>
                      </div>

                      <div className="py-3 space-y-1">
                        <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                          <span>SaaS Vendor SLA - Alpha Corp</span>
                          <span className="text-amber-500 text-[11px]">Auto-Renewal 30d</span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-[#8ba5b5]">
                          Notice window closes Oct 15, 2026. 15% rate escalation clause triggers automatically.
                        </p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setActiveTab('contracts')}
                    className="w-full py-2.5 rounded-xl bg-slate-100 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f] text-xs font-bold text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/10 transition flex items-center justify-center gap-1 mt-4"
                  >
                    View All Contracts <ChevronRight className="w-4 h-4" />
                  </button>
                </Card>
              </div>

              {/* Main Contracts List Component */}
              <ContractList
                onSelectContract={handleSelectContract}
                onOpenUpload={() => setUploadOpen(true)}
                externalSearch={searchQuery}
              />
            </div>
          ) : (
            <ContractList
              onSelectContract={handleSelectContract}
              onOpenUpload={() => setUploadOpen(true)}
              externalSearch={searchQuery}
            />
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 dark:border-[#183a4f] px-6 py-4 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 dark:text-[#8ba5b5] gap-4 bg-white/50 dark:bg-[#081621]/50">
          <div className="flex items-center gap-2 bg-amber-50 dark:bg-[#453014]/50 px-3 py-1.5 rounded-lg border border-amber-200 dark:border-amber-900/60">
            <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span className="text-amber-900 dark:text-amber-200">
              <strong className="text-amber-700 dark:text-amber-300">Mandatory Notice:</strong> AI decision support system; answers are grounded with verified citations.
            </span>
          </div>
          <div className="text-slate-500 dark:text-[#8ba5b5] font-semibold">ContractLens • Grounded AI Platform</div>
        </footer>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}
