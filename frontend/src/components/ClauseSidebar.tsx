import React, { useState } from 'react';
import { Search, ChevronDown, ChevronRight, FileText, Tag, Hash } from 'lucide-react';

export interface ClauseNode {
  id: string;
  number: string;
  heading: string | null;
  text: string;
  page_start: number;
  page_end: number;
  page: number;
  parent_id: string | null;
  level: number;
  order_index: number;
  clause_type: string | null;
  char_start: number;
  char_end: number;
  segmentation_method: string;
  confidence: number;
  children?: ClauseNode[];
}

interface ClauseSidebarProps {
  clauses: ClauseNode[];
  selectedClauseId: string | null;
  onSelectClause: (clause: ClauseNode) => void;
}

export const ClauseSidebar: React.FC<ClauseSidebarProps> = ({
  clauses,
  selectedClauseId,
  onSelectClause,
}) => {
  const [search, setSearch] = useState<string>('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const toggleCollapse = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const matchesSearch = (node: ClauseNode): boolean => {
    const query = search.toLowerCase();
    const numMatch = node.number.toLowerCase().includes(query);
    const headMatch = node.heading ? node.heading.toLowerCase().includes(query) : false;
    const typeMatch = node.clause_type ? node.clause_type.toLowerCase().includes(query) : false;
    const childMatch = node.children ? node.children.some(matchesSearch) : false;
    return numMatch || headMatch || typeMatch || childMatch;
  };

  const renderNode = (node: ClauseNode) => {
    if (search && !matchesSearch(node)) return null;

    const hasChildren = node.children && node.children.length > 0;
    const isCollapsed = collapsed[node.id];
    const isSelected = selectedClauseId === node.id;

    return (
      <div key={node.id} className="space-y-1">
        <div
          onClick={() => onSelectClause(node)}
          className={`flex items-center justify-between p-2 rounded-lg cursor-pointer text-xs transition-colors ${
            isSelected
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/50'
              : 'hover:bg-slate-800/60 text-slate-300'
          }`}
          style={{ paddingLeft: `${(node.level - 1) * 12 + 8}px` }}
        >
          <div className="flex items-center gap-1.5 min-w-0">
            {hasChildren ? (
              <button
                onClick={(e) => toggleCollapse(node.id, e)}
                className="p-0.5 rounded hover:bg-slate-700 text-slate-400 shrink-0"
              >
                {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            ) : (
              <span className="w-3.5 h-3.5 shrink-0" />
            )}

            <span className="font-semibold text-white shrink-0">{node.number}</span>
            <span className="truncate text-slate-400 font-normal">
              {node.heading || node.text.slice(0, 30)}
            </span>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {node.clause_type && node.clause_type !== 'other' && (
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-indigo-300 border border-indigo-500/30 font-medium capitalize">
                {node.clause_type}
              </span>
            )}
            <span className="text-[10px] text-slate-500 font-medium">p.{node.page_start}</span>
          </div>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="space-y-1">
            {node.children!.map((child) => renderNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-80 h-full bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Search Header */}
      <div className="p-3 border-b border-slate-800 space-y-2">
        <div className="text-xs font-bold text-white flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Hash className="w-4 h-4 text-blue-400" />
            Clause Outline
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
            {clauses.length} Clauses
          </span>
        </div>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter outline..."
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 border border-slate-700"
          />
        </div>
      </div>

      {/* Tree View Scroll Area */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {clauses.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">No clauses segmented yet</div>
        ) : (
          clauses.map((node) => renderNode(node))
        )}
      </div>
    </div>
  );
};
