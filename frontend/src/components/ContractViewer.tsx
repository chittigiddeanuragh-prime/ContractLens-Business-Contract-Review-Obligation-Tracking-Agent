import React, { useEffect, useState, useRef } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText, AlertTriangle, PanelLeftOpen, PanelLeftClose, ShieldAlert, MessageSquare, FileSearch } from 'lucide-react';
import { HighlightLayer, PageHighlight } from './HighlightLayer';
import { ClauseSidebar, ClauseNode } from './ClauseSidebar';
import { ClauseDetailPanel } from './ClauseDetailPanel';
import { ChatPanel } from './ChatPanel';
import { RiskAnalysisPanel } from './RiskAnalysisPanel';

interface ContractViewerProps {
  contractId: string;
  versionId: string;
  onBack: () => void;
}

export const ContractViewer: React.FC<ContractViewerProps> = ({ contractId, versionId, onBack }) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [zoom, setZoom] = useState<number>(100);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [warningMessage, setWarningMessage] = useState<string | null>(null);

  // Active right panel tab: 'risk' | 'qa' | 'inspector'
  const [activeRightTab, setActiveRightTab] = useState<'risk' | 'qa' | 'inspector'>('risk');

  // Clauses & Sidebar State
  const [clauses, setClauses] = useState<ClauseNode[]>([]);
  const [selectedClause, setSelectedClause] = useState<ClauseNode | null>(null);
  const [showSidebar, setShowSidebar] = useState<boolean>(true);

  // Highlights state
  const [highlights, setHighlights] = useState<PageHighlight[]>([]);

  const containerRef = useRef<HTMLDivElement>(null);
  const pdfUrl = `/api/v1/contracts/${contractId}/versions/${versionId}/file`;

  useEffect(() => {
    const fetchVersionInfo = async () => {
      try {
        const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}`);
        if (res.ok) {
          const data = await res.json();
          setTotalPages(data.page_count || 1);
          if (data.status === 'scanned_unsupported') {
            setErrorMessage(data.error_message || 'This PDF looks scanned or image-only.');
          }
        }
      } catch (err) {
        console.error('Failed to fetch version metadata:', err);
      }
    };
    fetchVersionInfo();
  }, [contractId, versionId]);

  // Fetch Clause Tree
  const fetchClauses = async () => {
    try {
      const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/clauses?format=tree`);
      if (res.ok) {
        const data = await res.json();
        setClauses(data.clauses || []);

        if (data.clauses && data.clauses.length > 0) {
          const firstMethod = data.clauses[0].segmentation_method;
          if (firstMethod === 'llm_assisted' || firstMethod === 'paragraph_fallback') {
            setWarningMessage('Structure detected with fallback segmentation (LLM/paragraph model).');
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch clause tree:', err);
    }
  };

  useEffect(() => {
    fetchClauses();
  }, [contractId, versionId]);

  const handleSelectClause = async (clause: ClauseNode) => {
    setSelectedClause(clause);
    setCurrentPage(clause.page_start);

    try {
      const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/highlights?start=${clause.char_start}&end=${clause.char_end}`);
      if (res.ok) {
        const data = await res.json();
        setHighlights(data.highlights || []);
      }
    } catch (err) {
      console.error('Failed to fetch clause highlights:', err);
    }
  };

  const handleSelectClauseIdById = (clauseId: string) => {
    const findNode = (nodes: ClauseNode[]): ClauseNode | null => {
      for (const n of nodes) {
        if (n.id === clauseId) return n;
        if (n.children) {
          const res = findNode(n.children);
          if (res) return res;
        }
      }
      return null;
    };
    const target = findNode(clauses);
    if (target) {
      handleSelectClause(target);
    }
  };

  const handleHighlightQuote = async (start: number, end: number, page: number) => {
    setCurrentPage(page);
    try {
      const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}/highlights?start=${start}&end=${end}`);
      if (res.ok) {
        const data = await res.json();
        setHighlights(data.highlights || []);
      }
    } catch (err) {
      console.error('Failed to fetch quote highlights:', err);
    }
  };

  const handleSelectClauseWithTab = (clause: ClauseNode) => {
    setActiveRightTab('inspector');
    handleSelectClause(clause);
  };

  const renderedWidth = (612 * zoom) / 100;
  const renderedHeight = (792 * zoom) / 100;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white dark:bg-[#0e2636] rounded-2xl border border-slate-200 dark:border-[#183a4f] overflow-hidden shadow-lg transition-colors">
      {/* Header Controls Bar */}
      <div className="flex flex-wrap items-center justify-between p-3 border-b border-slate-200 dark:border-[#183a4f] bg-slate-50 dark:bg-[#081621] gap-4 z-30">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#133044] transition-all shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 rounded-xl bg-white dark:bg-[#0e2636] border border-slate-200 dark:border-[#183a4f] text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#133044] transition-all shadow-sm flex items-center gap-1.5 text-xs font-bold"
          >
            {showSidebar ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
            {showSidebar ? 'Hide Outline' : 'Show Outline'}
          </button>
          <div>
            <div className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
              Contract Workspace
            </div>
            <div className="text-xs text-slate-500 dark:text-[#8ba5b5] font-medium">Clause Tree • Risk Analysis • Grounded Q&A</div>
          </div>
        </div>

        {/* Right Panel Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-[#091b27] p-1 rounded-xl border border-slate-300/80 dark:border-[#183a4f] text-xs font-bold">
          <button
            onClick={() => setActiveRightTab('risk')}
            className={`px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeRightTab === 'risk'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-600 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Risk & Anomalies
          </button>

          <button
            onClick={() => setActiveRightTab('qa')}
            className={`px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeRightTab === 'qa'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-600 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Grounded Q&A
          </button>

          <button
            onClick={() => setActiveRightTab('inspector')}
            className={`px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              activeRightTab === 'inspector'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-600 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <FileSearch className="w-3.5 h-3.5" />
            Clause Inspector
          </button>
        </div>

        {/* Page Navigation & Zoom Controls */}
        <div className="flex items-center gap-4 bg-white dark:bg-[#0e2636] px-3 py-1.5 rounded-xl border border-slate-200 dark:border-[#183a4f] shadow-sm">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1 rounded text-slate-500 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="text-xs font-bold text-slate-700 dark:text-slate-200 px-2">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="p-1 rounded text-slate-500 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="h-4 w-px bg-slate-200 dark:bg-[#183a4f]" />

          {/* Zoom */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setZoom((z) => Math.max(50, z - 25))}
              className="p-1 rounded text-slate-500 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white"
            >
              <ZoomOut className="w-4 h-4" />
            </button>

            <span className="text-xs font-bold text-slate-700 dark:text-slate-200 w-12 text-center">
              {zoom}%
            </span>

            <button
              onClick={() => setZoom((z) => Math.min(200, z + 25))}
              className="p-1 rounded text-slate-500 dark:text-[#8ba5b5] hover:text-slate-900 dark:hover:text-white"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {warningMessage && (
        <div className="bg-amber-500/10 text-amber-800 dark:text-amber-300 text-xs px-4 py-2 border-b border-amber-200 dark:border-amber-900/60 flex items-center gap-2 font-semibold">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500" />
          <span>{warningMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 text-center bg-red-50 dark:bg-red-950/40 border-b border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs flex items-center justify-center gap-2 font-semibold">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Content Area: Sidebar + PDF Viewer + Active Right Panel */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Clause Tree */}
        {showSidebar && (
          <ClauseSidebar
            clauses={clauses}
            selectedClauseId={selectedClause?.id || null}
            onSelectClause={handleSelectClauseWithTab}
          />
        )}

        {/* Center: PDF Viewer */}
        <div className="flex-1 overflow-auto p-6 bg-slate-100 dark:bg-[#081621] flex justify-center items-start relative">
          <div
            ref={containerRef}
            className="relative bg-white rounded-xl shadow-xl overflow-hidden border border-slate-300 dark:border-[#183a4f]"
            style={{ width: renderedWidth, height: renderedHeight }}
          >
            <iframe
              src={`${pdfUrl}#page=${currentPage}`}
              title="PDF Document"
              className="w-full h-full border-none"
              style={{ width: renderedWidth, height: renderedHeight }}
            />

            {/* Highlight Overlay */}
            <HighlightLayer
              highlights={highlights}
              currentPage={currentPage}
              renderedWidth={renderedWidth}
              renderedHeight={renderedHeight}
            />
          </div>
        </div>

        {/* Right Panel Container */}
        <div className="w-[450px] border-l border-slate-200 dark:border-[#183a4f] bg-white dark:bg-[#0e2636] flex flex-col overflow-hidden shadow-inner">
          {activeRightTab === 'risk' && (
            <RiskAnalysisPanel
              contractId={contractId}
              versionId={versionId}
              onHighlightQuote={handleHighlightQuote}
            />
          )}

          {activeRightTab === 'qa' && (
            <ChatPanel
              contractId={contractId}
              versionId={versionId}
              onHighlightCitation={handleHighlightQuote}
            />
          )}

          {activeRightTab === 'inspector' && selectedClause && (
            <ClauseDetailPanel
              contractId={contractId}
              versionId={versionId}
              clause={selectedClause}
              onClose={() => setSelectedClause(null)}
              onSelectClauseId={handleSelectClauseIdById}
            />
          )}

          {activeRightTab === 'inspector' && !selectedClause && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 dark:text-[#8ba5b5] text-xs">
              <FileSearch className="w-10 h-10 mb-2 opacity-40 text-cyan-500" />
              <p className="font-bold text-slate-700 dark:text-white">No Clause Selected</p>
              <p className="mt-1 max-w-xs leading-relaxed text-slate-500 dark:text-[#8ba5b5]">
                Select a clause from the left document outline to view details, cross-references, and defined terms.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
