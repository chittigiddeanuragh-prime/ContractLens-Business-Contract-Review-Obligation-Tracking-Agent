import React, { useState, useEffect } from 'react';

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
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50 dark:bg-slate-950">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Analyzing contract risks & market anomalies...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50 dark:bg-slate-950">
        <div className="p-3 bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400 rounded-full mb-3">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-1">
          Risk Analysis Unavailable
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mb-4">
          {error || 'Could not load risk assessment data.'}
        </p>
        <button
          onClick={fetchRisks}
          className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-md hover:bg-indigo-700 transition"
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

  const getScoreColor = (score: number) => {
    if (score >= 60) return 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30';
    if (score >= 30) return 'text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/30';
    return 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/30';
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 border border-red-200 dark:border-red-800">Critical</span>;
      case 'high':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 border border-orange-200 dark:border-orange-800">High</span>;
      case 'medium':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-200 dark:border-amber-800">Medium</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-800">Low</span>;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* Risk Score Summary Banner */}
      <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Risk & Market Anomaly Analysis
              <span className="text-xs font-medium px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full border border-slate-200 dark:border-slate-700">
                Phase 8 Engine
              </span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Detects high-risk terms, non-standard terms, and uncapped liabilities with verified citations.
            </p>
          </div>

          <div className={`px-4 py-2 rounded-lg border flex items-center gap-3 ${getScoreColor(data.overall_risk_score)}`}>
            <div className="text-right">
              <div className="text-xs font-medium uppercase tracking-wider opacity-80">Overall Risk Score</div>
              <div className="text-2xl font-black">{data.overall_risk_score} / 100</div>
            </div>
          </div>
        </div>

        {/* Severity Metrics Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
          <span className="font-semibold text-slate-500 dark:text-slate-400 mr-1">Metrics:</span>
          <span className="px-2.5 py-1 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 rounded-md font-medium border border-red-200 dark:border-red-900">
            {data.critical_count} Critical
          </span>
          <span className="px-2.5 py-1 bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300 rounded-md font-medium border border-orange-200 dark:border-orange-900">
            {data.high_count} High
          </span>
          <span className="px-2.5 py-1 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 rounded-md font-medium border border-amber-200 dark:border-amber-900">
            {data.medium_count} Medium
          </span>
          <span className="px-2.5 py-1 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 rounded-md font-medium border border-blue-200 dark:border-blue-900">
            {data.low_count} Low
          </span>
          <span className="px-2.5 py-1 bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 rounded-md font-medium border border-purple-200 dark:border-purple-900">
            ⚡ {data.anomaly_count} Market Anomalies
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="px-4 py-2 bg-slate-100 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 font-medium">
            <span>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>

          <label className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 font-medium">
            <span>Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              <option value="all">All Categories</option>
              <option value="liability">Liability</option>
              <option value="termination">Termination</option>
              <option value="indemnification">Indemnification</option>
              <option value="payment_terms">Payment Terms</option>
              <option value="compliance">Compliance</option>
            </select>
          </label>
        </div>

        <label className="flex items-center gap-2 cursor-pointer text-slate-700 dark:text-slate-300 font-medium select-none">
          <input
            type="checkbox"
            checked={onlyAnomalies}
            onChange={(e) => setOnlyAnomalies(e.target.checked)}
            className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
          />
          <span>Show Only Market Anomalies</span>
        </label>
      </div>

      {/* Risk Items List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredItems.length === 0 ? (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400 text-sm">
            No risk items match the selected filter criteria.
          </div>
        ) : (
          filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 shadow-sm hover:shadow transition"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  {getSeverityBadge(item.severity)}
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wide">
                    {item.category}
                  </span>
                  {item.is_anomaly && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                      ⚡ Market Anomaly
                    </span>
                  )}
                  {item.status === 'verified' && (
                    <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-0.5">
                      ✓ Verified Citation
                    </span>
                  )}
                </div>

                <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
                  Severity Score: {item.score}/10
                </span>
              </div>

              <h4 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-1">
                {item.title}
              </h4>

              <p className="text-xs text-slate-600 dark:text-slate-300 mb-3 leading-relaxed">
                {item.description}
              </p>

              {item.recommendation && (
                <div className="mb-3 p-2.5 bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/60 rounded-md text-xs text-indigo-900 dark:text-indigo-200">
                  <span className="font-semibold text-indigo-700 dark:text-indigo-300 mr-1">Recommendation:</span>
                  {item.recommendation}
                </div>
              )}

              {item.quote && (
                <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Contract Citation Quote
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
                        className="inline-flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 font-semibold transition"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        Highlight in PDF (Pg {item.page_start || 1})
                      </button>
                    )}
                  </div>
                  <blockquote className="text-xs italic text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950 p-2 rounded border-l-2 border-indigo-500 font-mono">
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
