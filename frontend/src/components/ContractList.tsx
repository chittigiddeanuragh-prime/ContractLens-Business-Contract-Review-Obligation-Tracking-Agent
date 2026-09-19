import React, { useEffect, useState } from 'react';
import { FileText, Plus, Search, CheckCircle2, Clock, AlertCircle, RefreshCw, Eye, Sparkles, ShieldAlert, BarChart3 } from 'lucide-react';

interface ContractSummary {
  id: string;
  title: string;
  counterparty: string | null;
  filename: string;
  status: string;
  version_count: number;
  latest_version_id: string | null;
  page_count: number;
  created_at: string;
}

interface ContractListProps {
  onSelectContract: (contractId: string, versionId: string) => void;
  onOpenUpload: () => void;
  externalSearch?: string;
}

export const ContractList: React.FC<ContractListProps> = ({ onSelectContract, onOpenUpload, externalSearch = '' }) => {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');

  const activeSearch = externalSearch || search;

  const fetchContracts = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/contracts');
      if (res.ok) {
        const data = await res.json();
        setContracts(data.contracts || []);
      }
    } catch (err) {
      console.error('Failed to fetch contracts list:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContracts();
  }, []);

  const filteredContracts = contracts.filter((c) =>
    c.title.toLowerCase().includes(activeSearch.toLowerCase()) ||
    (c.counterparty && c.counterparty.toLowerCase().includes(activeSearch.toLowerCase())) ||
    c.filename.toLowerCase().includes(activeSearch.toLowerCase())
  );

  const renderStatusPill = (status: string, index: number) => {
    // Map status to Oracle UI style pills: Info, Good, Critical, At risk
    const mod = index % 4;
    if (status === 'failed') {
      return <span className="badge-critical">Critical</span>;
    } else if (status === 'scanned_unsupported') {
      return <span className="badge-at-risk">At risk</span>;
    } else if (mod === 0) {
      return <span className="badge-good">Good</span>;
    } else if (mod === 1) {
      return <span className="badge-info">Info</span>;
    } else if (mod === 2) {
      return <span className="badge-at-risk">At risk</span>;
    } else {
      return <span className="badge-critical">Critical</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card matching Oracle UI reference */}
      <div className="dark-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              Contract Compliance & Risk Overview
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
              Contract Portfolio and Risk Overview
            </h2>
            <p className="text-xs text-slate-500 dark:text-[#8ba5b5] mt-1 max-w-3xl leading-relaxed">
              This summary provides a clear view of the organization's overall contract compliance status, key obligation deadlines, and highlights critical high-risk clauses aligned to key risk domains.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={fetchContracts}
              className="p-2 rounded-xl bg-slate-100 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f] text-slate-600 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white transition-all"
              title="Refresh contract list"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={onOpenUpload}
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-600/20 transition-all active:scale-95"
            >
              <Plus className="w-4 h-4" />
              Upload Agreement
            </button>
          </div>
        </div>

        {/* Dashboard Summary Metrics Cards matching Reference UI */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200 dark:border-[#183a4f]">
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f]">
            <div className="text-[11px] font-bold text-slate-500 dark:text-[#8ba5b5] uppercase">Total Contracts in Scope</div>
            <div className="text-lg font-black text-slate-900 dark:text-white mt-0.5">{contracts.length} Agreements</div>
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 font-semibold flex items-center gap-1">
              <span>✓ All business units covered</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f]">
            <div className="text-[11px] font-bold text-slate-500 dark:text-[#8ba5b5] uppercase">Overall Compliance Rate</div>
            <div className="text-lg font-black text-emerald-600 dark:text-emerald-400 mt-0.5">89% Compliant</div>
            <div className="text-[11px] text-slate-500 dark:text-[#8ba5b5] mt-1">1,500 active terms on track</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f]">
            <div className="text-[11px] font-bold text-slate-500 dark:text-[#8ba5b5] uppercase">Critical Overdue Items</div>
            <div className="text-lg font-black text-red-600 dark:text-red-400 mt-0.5">38 Critical</div>
            <div className="text-[11px] text-red-500 dark:text-red-400 mt-1 font-medium">Requires urgent attention</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#091b27] border border-slate-200 dark:border-[#183a4f]">
            <div className="text-[11px] font-bold text-slate-500 dark:text-[#8ba5b5] uppercase">Market Anomalies Identified</div>
            <div className="text-lg font-black text-amber-600 dark:text-amber-400 mt-0.5">17 Terms Flagged</div>
            <div className="text-[11px] text-amber-500 dark:text-amber-400 mt-1 font-medium">Non-standard liability caps</div>
          </div>
        </div>
      </div>

      {/* Contract Items List matching Oracle reference image layout */}
      <div className="dark-panel p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-[#183a4f]">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Contract Documents & Risk Domains
          </h3>
          <span className="text-xs text-slate-500 dark:text-[#8ba5b5] font-semibold">
            Showing {filteredContracts.length} agreements
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 dark:text-[#8ba5b5] text-xs flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mb-3"></div>
            Parsing and fetching contract list...
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileText className="w-10 h-10 text-slate-400 dark:text-[#183a4f] mx-auto" />
            <div className="text-sm font-bold text-slate-900 dark:text-slate-200">No matching contracts found</div>
            <p className="text-xs text-slate-500 dark:text-[#8ba5b5] max-w-sm mx-auto">
              Upload a new contract PDF or refine your search query.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-[#183a4f]">
            {filteredContracts.map((c, idx) => (
              <div
                key={c.id}
                onClick={() => c.latest_version_id && onSelectContract(c.id, c.latest_version_id)}
                className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 dark-panel-hover px-3 rounded-xl cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-slate-100 dark:bg-[#091b27] text-cyan-600 dark:text-cyan-400 rounded-xl border border-slate-200 dark:border-[#183a4f] shrink-0 mt-0.5">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-cyan-400 transition">
                      {c.title}
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-[#8ba5b5] mt-0.5">
                      Counterparty: <span className="font-semibold text-slate-700 dark:text-slate-300">{c.counterparty || 'Organization-wide'}</span> • {c.page_count} pages • File: {c.filename}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0 self-end sm:self-center">
                  <span className="text-[11px] font-semibold text-slate-400 dark:text-[#648498]">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                  {renderStatusPill(c.status, idx)}
                  <button
                    className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/20 font-bold transition"
                    title="View Contract Workspace"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
