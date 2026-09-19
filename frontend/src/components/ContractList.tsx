import React, { useEffect, useState } from 'react';
import { FileText, Plus, Search, CheckCircle2, Clock, AlertCircle, RefreshCw, Eye, Sparkles } from 'lucide-react';

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
}

export const ContractList: React.FC<ContractListProps> = ({ onSelectContract, onOpenUpload }) => {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');

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
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    (c.counterparty && c.counterparty.toLowerCase().includes(search.toLowerCase())) ||
    c.filename.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
      case 'ready_with_warnings':
      case 'parsed':
      case 'segmented':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            Ready
          </span>
        );
      case 'extracting':
      case 'segmenting':
      case 'parsing':
      case 'uploaded':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 animate-pulse">
            <Clock className="w-3.5 h-3.5 text-indigo-500" />
            Processing ({status})
          </span>
        );
      case 'scanned_unsupported':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
            Scanned PDF
          </span>
        );
      case 'failed':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-200 dark:border-red-800">
            <AlertCircle className="w-3.5 h-3.5 text-red-500" />
            Failed
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            Contract Intelligence Repository
            <Sparkles className="w-5 h-5 text-indigo-500" />
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Uploaded contracts, clause structure trees, verified citations, and risk assessment benchmarks
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchContracts}
            className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-700 transition-all shadow-sm"
            title="Refresh contract list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onOpenUpload}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            Upload Contract PDF
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-4 top-3.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search contracts by title, counterparty, or filename..."
          className="w-full pl-11 pr-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all shadow-sm"
        />
      </div>

      {/* Contracts Table */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-slate-500 dark:text-slate-400 text-sm flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
            Loading repository contracts...
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="p-3 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 rounded-full w-12 h-12 flex items-center justify-center mx-auto border border-indigo-100 dark:border-indigo-900">
              <FileText className="w-6 h-6" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-200">No contracts found</div>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
              Upload a business contract PDF or sample agreement to start analyzing clauses, obligations, and risk factors.
            </p>
            <button
              onClick={onOpenUpload}
              className="mt-2 px-3.5 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-500 transition-all inline-flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              Upload First Contract
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[11px] border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Contract Title</th>
                  <th className="py-3.5 px-4">Counterparty</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Page Count</th>
                  <th className="py-3.5 px-4">Uploaded Date</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                {filteredContracts.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 dark:text-slate-100 font-bold flex items-center gap-2.5">
                      <div className="p-2 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-lg border border-indigo-100 dark:border-indigo-900 shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <span className="truncate max-w-xs">{c.title}</span>
                    </td>
                    <td className="py-4 px-4 text-slate-600 dark:text-slate-300">{c.counterparty || '—'}</td>
                    <td className="py-4 px-4">{getStatusBadge(c.status)}</td>
                    <td className="py-4 px-4 text-slate-500 dark:text-slate-400">{c.page_count} pages</td>
                    <td className="py-4 px-4 text-slate-500 dark:text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="py-4 px-4 text-right">
                      {c.latest_version_id && (
                        <button
                          onClick={() => onSelectContract(c.id, c.latest_version_id!)}
                          className="px-3.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 border border-indigo-200 dark:border-indigo-800 font-bold flex items-center gap-1.5 ml-auto transition-all active:scale-95"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          View Contract
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
