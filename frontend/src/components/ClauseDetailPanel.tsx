import React, { useEffect, useState } from 'react';
import { X, FileText, Link2, BookOpen } from 'lucide-react';
import { ClauseNode } from './ClauseSidebar';

interface ClauseDetailPanelProps {
  contractId: string;
  versionId: string;
  clause: ClauseNode | null;
  onClose: () => void;
  onSelectClauseId: (clauseId: string) => void;
}

interface ClauseDetailData {
  id: string;
  number: string;
  heading: string | null;
  text: string;
  page_start: number;
  page_end: number;
  level: number;
  clause_type: string | null;
  char_start: number;
  char_end: number;
  segmentation_method: string;
  confidence: number;
  sub_clauses: Array<{ id: string; number: string; heading: string | null }>;
  references: Array<{ ref_text: string; to_number: string; resolved_clause_id: string | null }>;
  defined_terms: Array<{ term: string; definition: string }>;
}

export const ClauseDetailPanel: React.FC<ClauseDetailPanelProps> = ({
  contractId,
  versionId,
  clause,
  onClose,
  onSelectClauseId,
}) => {
  const [detail, setDetail] = useState<ClauseDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!clause) {
      setDetail(null);
      return;
    }
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/clauses/${clause.id}`);
        if (res.ok) {
          const data = await res.json();
          setDetail(data);
        }
      } catch (err) {
        console.error('Failed to fetch clause detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [contractId, versionId, clause]);

  if (!clause) return null;

  return (
    <div className="w-96 h-full bg-slate-900 border-l border-slate-800 flex flex-col shadow-2xl relative z-30">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-400" />
          <h4 className="text-sm font-bold text-white">Clause Inspector</h4>
        </div>
        <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {loading || !detail ? (
          <div className="text-xs text-slate-400 text-center py-8">Loading clause metadata...</div>
        ) : (
          <>
            {/* Title & Badge */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-base font-bold text-white">{detail.number}</span>
                {detail.clause_type && (
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 capitalize">
                    {detail.clause_type}
                  </span>
                )}
              </div>
              {detail.heading && (
                <div className="text-xs font-semibold text-slate-300">{detail.heading}</div>
              )}
              <div className="flex items-center gap-3 text-[11px] text-slate-400 pt-1">
                <span>Page {detail.page_start} - {detail.page_end}</span>
                <span>•</span>
                <span>Method: {detail.segmentation_method}</span>
                <span>•</span>
                <span>Conf: {(detail.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Exact Canonical Text Slice */}
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Exact Clause Text</div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap select-text">
                {detail.text}
              </div>
              <div className="text-[10px] text-slate-500">
                Canonical Offsets: [{detail.char_start}, {detail.char_end}] ({detail.text.length} chars)
              </div>
            </div>

            {/* Cross References */}
            {detail.references && detail.references.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Link2 className="w-3.5 h-3.5 text-blue-400" />
                  Cross References
                </div>
                <div className="space-y-1.5">
                  {detail.references.map((r, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs flex items-center justify-between"
                    >
                      <span className="text-slate-300 font-medium">{r.ref_text}</span>
                      {r.resolved_clause_id ? (
                        <button
                          onClick={() => onSelectClauseId(r.resolved_clause_id!)}
                          className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 text-[10px] font-semibold"
                        >
                          Jump to Clause
                        </button>
                      ) : (
                        <span className="text-[10px] text-slate-500 italic">Unresolved</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Defined Terms */}
            {detail.defined_terms && detail.defined_terms.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
                  Defined Terms
                </div>
                <div className="space-y-2">
                  {detail.defined_terms.map((dt, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs space-y-1">
                      <div className="font-semibold text-emerald-300">"{dt.term}"</div>
                      <div className="text-[11px] text-slate-400 leading-snug">{dt.definition}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
