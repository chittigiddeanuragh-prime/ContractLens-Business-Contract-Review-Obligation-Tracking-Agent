import React, { useState } from 'react';
import { FieldCard, ExtractedFieldItem } from './FieldCard';
import { FieldInspector } from './FieldInspector';

interface FieldDashboardProps {
  fields: ExtractedFieldItem[];
  onHighlightQuote: (start: number, end: number, page: number) => void;
  onReExtract?: () => void;
  isLoading?: boolean;
}

export const FieldDashboard: React.FC<FieldDashboardProps> = ({
  fields,
  onHighlightQuote,
  onReExtract,
  isLoading = false,
}) => {
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedField, setSelectedField] = useState<ExtractedFieldItem | null>(null);

  const groups = [
    { id: 'all', label: 'All Fields' },
    { id: 'A', label: 'Parties & Dates' },
    { id: 'B', label: 'Renewal & Termination' },
    { id: 'C', label: 'Commercial & Liability' },
    { id: 'D', label: 'Governing Law' },
  ];

  const filteredFields = fields.filter((f) => {
    const matchesGroup = selectedGroup === 'all' || f.group_name === selectedGroup;
    const matchesStatus =
      statusFilter === 'all'
        ? true
        : statusFilter === 'verified'
        ? f.review_status === 'verified' || f.review_status === 'approved'
        : statusFilter === 'needs_review'
        ? f.review_status === 'needs_review' || f.review_status === 'low_confidence'
        : f.review_status === 'not_found';
    return matchesGroup && matchesStatus;
  });

  const verifiedCount = fields.filter((f) => f.review_status === 'verified' || f.review_status === 'approved').length;
  const reviewCount = fields.filter((f) => f.review_status === 'needs_review' || f.review_status === 'low_confidence').length;
  const notFoundCount = fields.filter((f) => f.review_status === 'not_found').length;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-slate-950 overflow-hidden relative">
      {/* Header bar & metrics */}
      <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Key-Field Extraction & Verified Citations
              <span className="text-xs font-normal px-2 py-0.5 bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 rounded-full border border-indigo-200 dark:border-indigo-800">
                13 Fields Target
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Every value is code-verified in canonical text with exact offset citations.
            </p>
          </div>

          {onReExtract && (
            <button
              onClick={onReExtract}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors shadow-sm disabled:opacity-50"
            >
              {isLoading ? 'Extracting...' : '⚡ Re-Run Field Extraction'}
            </button>
          )}
        </div>

        {/* Status Metrics Bar */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="p-2.5 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200/80 dark:border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400">Total Fields</span>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100">{fields.length}</div>
          </div>
          <div className="p-2.5 bg-emerald-50/60 dark:bg-emerald-950/30 rounded-lg border border-emerald-200/80 dark:border-emerald-900/50">
            <span className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400">Verified Citations</span>
            <div className="text-lg font-bold text-emerald-700 dark:text-emerald-300">{verifiedCount}</div>
          </div>
          <div className="p-2.5 bg-amber-50/60 dark:bg-amber-950/30 rounded-lg border border-amber-200/80 dark:border-amber-900/50">
            <span className="text-[10px] uppercase font-bold text-amber-600 dark:text-amber-400">Needs Review</span>
            <div className="text-lg font-bold text-amber-700 dark:text-amber-300">{reviewCount}</div>
          </div>
          <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400">Not Found</span>
            <div className="text-lg font-bold text-slate-600 dark:text-slate-300">{notFoundCount}</div>
          </div>
        </div>

        {/* Group Tabs & Filter */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800/80">
          <div className="flex gap-1 overflow-x-auto">
            {groups.map((g) => (
              <button
                key={g.id}
                onClick={() => setSelectedGroup(g.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedGroup === g.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {g.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Filter:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-2.5 py-1 text-slate-700 dark:text-slate-300 text-xs font-medium"
            >
              <option value="all">All Statuses</option>
              <option value="verified">Verified Only</option>
              <option value="needs_review">Needs Review Only</option>
              <option value="not_found">Not Found Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 p-6 overflow-y-auto">
        {filteredFields.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <div className="text-4xl mb-2">🔍</div>
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              No fields match the selected filter criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFields.map((field) => (
              <FieldCard
                key={field.id}
                field={field}
                isSelected={selectedField?.id === field.id}
                onSelectField={(f) => setSelectedField(f)}
                onHighlightQuote={onHighlightQuote}
              />
            ))}
          </div>
        )}
      </div>

      {/* Side Inspector Drawer */}
      <FieldInspector
        field={selectedField}
        onClose={() => setSelectedField(null)}
        onHighlightQuote={onHighlightQuote}
      />
    </div>
  );
};
