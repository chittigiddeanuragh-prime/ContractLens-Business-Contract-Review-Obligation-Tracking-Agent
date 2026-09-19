import React from 'react';
import { ExtractedFieldItem } from './FieldCard';

interface FieldInspectorProps {
  field: ExtractedFieldItem | null;
  onClose: () => void;
  onHighlightQuote: (start: number, end: number, page: number) => void;
}

export const FieldInspector: React.FC<FieldInspectorProps> = ({
  field,
  onClose,
  onHighlightQuote,
}) => {
  if (!field) return null;

  const breakdown = typeof field.confidence_breakdown === 'string'
    ? JSON.parse(field.confidence_breakdown || '{}')
    : field.confidence_breakdown || {};

  const normalized = typeof field.value_normalized === 'string'
    ? JSON.parse(field.value_normalized || '{}')
    : field.value_normalized || {};

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl p-6 z-40 overflow-y-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Field Inspector
          </span>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {field.display_label}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg"
        >
          ✕
        </button>
      </div>

      <div className="mt-6 space-y-6">
        {/* Value */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase">Extracted Value</label>
          <div className="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100 p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200/60 dark:border-slate-800">
            {field.value_raw || <span className="italic text-slate-400">Not found</span>}
          </div>
        </div>

        {/* Normalized info */}
        {Object.keys(normalized).length > 0 && (
          <div>
            <label className="text-xs font-medium text-slate-500 uppercase">Code Normalization</label>
            <pre className="mt-1 text-xs font-mono p-3 bg-slate-900 text-slate-200 rounded-lg overflow-x-auto">
              {JSON.stringify(normalized, null, 2)}
            </pre>
          </div>
        )}

        {/* Verified Quote Citation */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase">Verified Quote Citation</label>
          {field.quote ? (
            <div className="mt-1 p-3 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-lg">
              <p className="text-xs italic text-slate-800 dark:text-slate-200 font-serif">
                "{field.quote}"
              </p>
              <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-500">
                <span>Page {field.page_start || 1} • Offsets [{field.char_start}, {field.char_end}]</span>
                {field.char_start !== null && field.char_end !== null && (
                  <button
                    onClick={() => onHighlightQuote(field.char_start!, field.char_end!, field.page_start || 1)}
                    className="text-indigo-600 dark:text-indigo-400 font-sans font-semibold hover:underline"
                  >
                    View in PDF ↗
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-xs text-slate-400 italic p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border">
              No citation quote associated
            </div>
          )}
        </div>

        {/* Confidence Breakdown Engine */}
        <div>
          <label className="text-xs font-medium text-slate-500 uppercase">Confidence Score Breakdown</label>
          <div className="mt-2 space-y-2 text-xs">
            <div className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-950 rounded">
              <span>Quote Match ({field.verification_status})</span>
              <span className="font-mono font-bold">+{breakdown.quote_match || 0.0}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-950 rounded">
              <span>Clause Category Match</span>
              <span className="font-mono font-bold">+{breakdown.clause_type_match || 0.0}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-950 rounded">
              <span>Normalization Succeeded</span>
              <span className="font-mono font-bold">+{breakdown.normalized_success || 0.0}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-50 dark:bg-slate-950 rounded">
              <span>Regex Baseline Cross-Check</span>
              <span className="font-mono font-bold">+{breakdown.regex_match || 0.0}</span>
            </div>

            {breakdown.penalties && breakdown.penalties.length > 0 && (
              <div className="p-2 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 rounded border border-red-200">
                <span className="font-semibold">Penalties:</span>
                <ul className="list-disc list-inside mt-1 space-y-1 text-[11px]">
                  {breakdown.penalties.map((p: string, idx: number) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex justify-between items-center p-2 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-900 dark:text-indigo-200 font-semibold rounded">
              <span>Final Confidence</span>
              <span className="font-mono text-sm">{Math.round(field.confidence * 100)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
