import React from 'react';

export interface ExtractedFieldItem {
  id: string;
  field_name: string;
  display_label: string;
  group_name: string;
  value_type: string;
  value_raw: string | null;
  value_normalized: any;
  quote: string | null;
  char_start: number | null;
  char_end: number | null;
  page_start: number | null;
  page_end: number | null;
  clause_id: string | null;
  verification_status: 'exact' | 'fuzzy' | 'outside_clause' | 'failed' | 'not_found';
  review_status: 'verified' | 'needs_review' | 'low_confidence' | 'not_found' | 'approved' | 'edited';
  confidence: number;
  confidence_breakdown: any;
  conflict?: boolean;
  alternates?: any;
  extraction_method: string;
}

interface FieldCardProps {
  field: ExtractedFieldItem;
  isSelected?: boolean;
  onSelectField: (field: ExtractedFieldItem) => void;
  onHighlightQuote: (start: number, end: number, page: number) => void;
}

export const FieldCard: React.FC<FieldCardProps> = ({
  field,
  isSelected = false,
  onSelectField,
  onHighlightQuote,
}) => {
  const getStatusBadge = () => {
    switch (field.review_status) {
      case 'verified':
      case 'approved':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            ✓ Verified
          </span>
        );
      case 'needs_review':
      case 'low_confidence':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
            ⚠️ Needs Review
          </span>
        );
      case 'not_found':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            Not Found
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
            {field.review_status}
          </span>
        );
    }
  };

  const formattedValue = () => {
    if (!field.value_raw) return <span className="italic text-slate-400">Not present in document</span>;
    return <span className="font-semibold text-slate-900 dark:text-slate-100">{field.value_raw}</span>;
  };

  return (
    <div
      onClick={() => onSelectField(field)}
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? 'bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-500 shadow-md ring-1 ring-indigo-500'
          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {field.display_label}
        </span>
        {getStatusBadge()}
      </div>

      <div className="text-base mb-2">{formattedValue()}</div>

      {field.quote && (
        <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-950 rounded-lg text-xs text-slate-600 dark:text-slate-300 border border-slate-100 dark:border-slate-800">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1 font-mono">
            <span>CITING CANONICAL TEXT (PAGE {field.page_start || 1})</span>
            {field.char_start !== null && field.char_end !== null && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onHighlightQuote(field.char_start!, field.char_end!, field.page_start || 1);
                }}
                className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium cursor-pointer"
              >
                Highlight in PDF ↗
              </button>
            )}
          </div>
          <p className="italic line-clamp-2">"{field.quote}"</p>
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800/60">
        <span>Conf: Math.round({Math.round(field.confidence * 100)}%)</span>
        <span className="capitalize">{field.extraction_method.replace('_', ' ')}</span>
      </div>
    </div>
  );
};
