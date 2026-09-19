import React, { useState } from 'react';

export interface QACitationItem {
  citation_index: number;
  clause_id?: string;
  quote: string;
  page_start: number;
  char_start?: number;
  char_end?: number;
}

export interface QAMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  answer_status?: 'answered' | 'partially_answered' | 'not_found' | 'out_of_scope' | 'needs_clarification' | 'unavailable';
  route?: string;
  confidence?: number;
  confidence_breakdown?: any;
  answer_payload?: {
    answer_text?: string;
    scope_line?: string;
    claims?: any[];
    citations?: QACitationItem[];
    suggestions?: string[];
  };
  suggested_followups?: string[];
}

interface ChatMessageProps {
  message: QAMessageItem;
  onHighlightQuote: (start: number, end: number, page: number) => void;
  onSelectSuggestion?: (question: string) => void;
  onFeedback?: (messageId: string, rating: 'up' | 'down') => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onHighlightQuote,
  onSelectSuggestion,
  onFeedback,
}) => {
  const [feedbackGiven, setFeedbackGiven] = useState<'up' | 'down' | null>(null);

  if (message.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] bg-indigo-600 text-white rounded-2xl px-4 py-2.5 shadow-sm text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  const status = message.answer_status || 'answered';
  const citations = message.answer_payload?.citations || [];
  const suggestions = message.answer_payload?.suggestions || message.suggested_followups || [];

  const handleFeedback = (rating: 'up' | 'down') => {
    setFeedbackGiven(rating);
    if (onFeedback) onFeedback(message.id, rating);
  };

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[92%] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm text-sm text-slate-800 dark:text-slate-200">
        {/* Header badges */}
        <div className="flex items-center justify-between mb-3 text-xs border-b border-slate-100 dark:border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
              ✨ ContractLens AI
            </span>
            {message.route && (
              <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono text-[10px] capitalize">
                {message.route.replace('_', ' ')}
              </span>
            )}
          </div>

          {message.confidence !== undefined && (
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                message.confidence >= 0.8
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                  : message.confidence >= 0.5
                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                  : 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
              }`}
            >
              {Math.round(message.confidence * 100)}% Confidence
            </span>
          )}
        </div>

        {/* Content rendering based on status */}
        {status === 'not_found' ? (
          <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200/80 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-medium">
            <div className="text-slate-900 dark:text-slate-100 font-bold mb-1">
              Not found in the contract.
            </div>
            {message.answer_payload?.scope_line && (
              <div className="text-xs text-slate-400 font-normal">
                {message.answer_payload.scope_line}
              </div>
            )}
          </div>
        ) : status === 'out_of_scope' ? (
          <div className="p-3 bg-amber-50/70 dark:bg-amber-950/30 rounded-xl border border-amber-200/80 dark:border-amber-900/50 text-amber-900 dark:text-amber-200">
            {message.content}
          </div>
        ) : (
          <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
        )}

        {/* Sources list */}
        {citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Verified Sources ({citations.length})
            </span>
            <div className="space-y-2">
              {citations.map((cit, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    if (cit.char_start !== undefined && cit.char_end !== undefined) {
                      onHighlightQuote(cit.char_start, cit.char_end, cit.page_start || 1);
                    }
                  }}
                  className="p-2.5 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50 hover:border-indigo-300 dark:hover:border-indigo-700 cursor-pointer transition-colors text-xs"
                >
                  <div className="flex items-center justify-between text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-bold mb-1">
                    <span>[{cit.citation_index || idx + 1}] PAGE {cit.page_start || 1}</span>
                    <span>Click to Highlight ↗</span>
                  </div>
                  <p className="italic text-slate-700 dark:text-slate-300 line-clamp-2">
                    "{cit.quote}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggestions chips */}
        {suggestions.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {suggestions.map((s, sIdx) => (
              <button
                key={sIdx}
                onClick={() => onSelectSuggestion && onSelectSuggestion(s)}
                className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950 hover:text-indigo-600 dark:hover:text-indigo-300 text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Feedback footer */}
        <div className="mt-3 pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 dark:border-slate-800/60">
          <span>Assists review; not legal advice.</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleFeedback('up')}
              className={`p-1 hover:text-indigo-600 ${feedbackGiven === 'up' ? 'text-emerald-600 font-bold' : ''}`}
            >
              👍 Helpful
            </button>
            <button
              onClick={() => handleFeedback('down')}
              className={`p-1 hover:text-red-600 ${feedbackGiven === 'down' ? 'text-red-600 font-bold' : ''}`}
            >
              👎 Not helpful
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
