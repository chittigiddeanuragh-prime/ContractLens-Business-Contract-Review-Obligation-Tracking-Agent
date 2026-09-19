import React, { useState, useEffect } from 'react';
import { AlertTriangle, Sparkles, ChevronRight } from 'lucide-react';

export interface RiskItemData {
  id: string;
  title: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | string;
  score: number;
  description: string;
  recommendation?: string;
  is_anomaly: boolean;
  quote?: string;
  clause_id?: string;
  char_start?: number;
  char_end?: number;
  page_start?: number;
  page_end?: number;
  status: string;
  confidence: number;
}

export interface RiskSummaryData {
  overall_risk_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  anomaly_count: number;
  risk_items: RiskItemData[];
}

interface RiskAnalysisPanelProps {
  contractId: string;
  versionId?: string;
  onHighlightQuote: (start: number, end: number, page: number) => void;
}

export const RiskAnalysisPanel: React.FC<RiskAnalysisPanelProps> = ({
  contractId,
  versionId,
  onHighlightQuote,
}) => {
  const [data, setData] = useState<RiskSummaryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [onlyAnomalies, setOnlyAnomalies] = useState<boolean>(false);

  const fetchRisks = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`/api/v1/contracts/${contractId}/risk`);
      if (!resp.ok) {
        throw new Error('Failed to fetch risk analysis');
      }
      const json = await resp.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error loading risk data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contractId) {
      fetchRisks();
    }
  }, [contractId, versionId]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50 dark:bg-[#081621]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-500 mb-4"></div>
        <p className="text-xs font-semibold text-slate-600 dark:text-[#8ba5b5]">
          Analyzing contract terms & market anomalies...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50 dark:bg-[#081621]">
        <div className="p-3 bg-red-100 dark:bg-[#451a1a] text-red-600 dark:text-red-400 rounded-full mb-3 border border-red-200 dark:border-red-900">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
          Risk Analysis Unavailable
        </h3>
        <p className="text-xs text-slate-500 dark:text-[#8ba5b5] max-w-sm mb-4">
          {error || 'Could not load risk assessment data.'}
        </p>
        <button
          onClick={fetchRisks}
          className="px-3.5 py-1.5 bg-cyan-600 text-white text-xs font-bold rounded-xl hover:bg-cyan-500 transition shadow"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  const filteredItems = data.risk_items.filter((item) => {
    if (severityFilter !== 'all' && item.severity.toLowerCase() !== severityFilter) return false;
    if (categoryFilter !== 'all' && item.category.toLowerCase() !== categoryFilter) return false;
    if (onlyAnomalies && !item.is_anomaly) return false;
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <span className="badge-critical">Critical</span>;
      case 'high':
        return <span className="badge-at-risk">At risk</span>;
      case 'medium':
        return <span className="badge-info">Info</span>;
      default:
        return <span className="badge-good">Good</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-[#081621] overflow-hidden">
      {/* Risk Score Summary Banner matching reference UI */}
      <div className="p-4 bg-white dark:bg-[#0e2636] border-b border-slate-200 dark:border-[#183a4f]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
              Risk & Market Anomaly Engine
            </div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              Risk Domain Analysis
              <Sparkles className="w-4 h-4 text-cyan-400" />
            </h2>
          </div>

          <div className="px-3 py-1.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 font-bold text-right">
            <div className="text-[10px] uppercase tracking-wider opacity-80">Risk Score</div>
            <div className="text-lg font-black">{data.overall_risk_score} / 100</div>
          </div>
        </div>

        {/* Severity Metrics Chips matching reference UI */}
        <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 dark:border-[#183a4f] text-[11px]">
          <span className="badge-critical">{data.critical_count} Critical</span>
          <span className="badge-at-risk">{data.high_count} High</span>
          <span className="badge-info">{data.medium_count} Medium</span>
          <span className="badge-good">{data.low_count} Low</span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
            ⚡ {data.anomaly_count} Anomalies
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="px-4 py-2 bg-slate-100 dark:bg-[#091b27] border-b border-slate-200 dark:border-[#183a4f] flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-white dark:bg-[#0e2636] border border-slate-300 dark:border-[#183a4f] rounded-lg px-2 py-1 text-xs text-slate-800 dark:text-slate-200 font-medium"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-white dark:bg-[#0e2636] border border-slate-300 dark:border-[#183a4f] rounded-lg px-2 py-1 text-xs text-slate-800 dark:text-slate-200 font-medium"
          >
            <option value="all">All Categories</option>
            <option value="liability">Liability</option>
            <option value="termination">Termination</option>
            <option value="indemnification">Indemnification</option>
            <option value="payment_terms">Payment Terms</option>
            <option value="compliance">Compliance</option>
          </select>
        </div>

        <label className="flex items-center gap-1.5 cursor-pointer text-slate-700 dark:text-[#8ba5b5] font-semibold text-[11px]">
          <input
            type="checkbox"
            checked={onlyAnomalies}
            onChange={(e) => setOnlyAnomalies(e.target.checked)}
            className="rounded border-slate-300 dark:border-[#183a4f] text-cyan-600 focus:ring-cyan-500"
          />
          <span>Anomalies Only</span>
        </label>
      </div>

      {/* Risk Items List matching reference UI */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredItems.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-[#8ba5b5] text-xs font-medium">
            No risk items match the filter criteria.
          </div>
        ) : (
          filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] rounded-xl p-4 shadow-sm hover:border-cyan-500/50 transition-all"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  {getSeverityBadge(item.severity)}
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-[#091b27] text-slate-600 dark:text-[#8ba5b5] uppercase tracking-wide border border-slate-200 dark:border-[#183a4f]">
                    {item.category}
                  </span>
                  {item.is_anomaly && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                      ⚡ Anomaly
                    </span>
                  )}
                </div>

                <span className="text-[11px] font-bold text-slate-400 dark:text-[#648498]">
                  Score: {item.score}/10
                </span>
              </div>

              <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                {item.title}
              </h4>

              <p className="text-xs text-slate-600 dark:text-[#8ba5b5] mb-3 leading-relaxed">
                {item.description}
              </p>

              {item.recommendation && (
                <div className="mb-3 p-2.5 bg-cyan-500/10 dark:bg-[#091b27] border border-cyan-500/30 rounded-lg text-xs text-cyan-900 dark:text-cyan-200">
                  <span className="font-bold text-cyan-700 dark:text-cyan-400 mr-1">Recommendation:</span>
                  {item.recommendation}
                </div>
              )}

              {item.quote && (
                <div className="mt-2 pt-2 border-t border-slate-100 dark:border-[#183a4f]">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[10px] font-bold text-slate-400 dark:text-[#648498] uppercase tracking-wider">
                      Verified Citation Quote
                    </span>
                    {item.char_start !== undefined && item.char_end !== undefined && (
                      <button
                        onClick={() =>
                          onHighlightQuote(
                            item.char_start || 0,
                            item.char_end || 0,
                            item.page_start || 1
                          )
                        }
                        className="inline-flex items-center gap-1 text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline font-bold"
                      >
                        Highlight in PDF (Pg {item.page_start || 1})
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                  <blockquote className="text-xs italic text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-[#091b27] p-2 rounded-lg border-l-2 border-cyan-500 font-mono">
                    "{item.quote}"
                  </blockquote>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
