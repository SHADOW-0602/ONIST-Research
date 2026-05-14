"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LeftPaneSourceLibrary } from "./LeftPaneSourceLibrary";
import { CenterPaneResearchCanvas } from "./CenterPaneResearchCanvas";
import { RightPaneReviewGate } from "./RightPaneReviewGate";
import { Menu, X, Book, FileText, CheckCircle, Play, Download } from "lucide-react";
import { usePipeline } from "../../hooks/usePipeline";
import { useReactToPrint } from "react-to-print";
import { FDDReportTemplate } from "./FDDReportTemplate";
import { useRef } from "react";

import { Header } from "../common/Header";
import { RefreshCw, Zap } from "lucide-react";

export function WorkspaceLayout({ ticker }: { ticker?: string }) {
  const [isMobile, setIsMobile] = useState(false);
  const [activeTab, setActiveTab] = useState<"library" | "canvas" | "review">("canvas");
  
  const { taskId, status, graphState, diff, notebookEntries, publishedReport, analystReviewItems, startPipeline, approveSynthesis, injectGuidance, directEdit, triggerRefresh, fetchDiff, annotateClaim, overrideClaim, suppressClaim, injectClaim, editFDDSection, adjudicateThesis, regenerateFDDSection, publishFDD, schedulePublication, retractReport, fetchFDDHistory, fetchNotebookEntries, resolveReviewItem, dismissReviewItem, clearResolvedItems, optimizePrompts } = usePipeline();

  const printRef = useRef<HTMLDivElement>(null);
  
  const handlePrint = useReactToPrint({
    contentRef: printRef,
    documentTitle: `ONIST_FDD_Report_${graphState?.ticker || ticker || 'Draft'}`,
  });

  useEffect(() => {
    if (ticker && status === "Idle") {
      // Start pipeline, but api will check for existing report
      startPipeline(ticker, `In-depth research for ${ticker}`);
    }
  }, [ticker, status, startPipeline]);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  if (isMobile) {
    // ... (rest of mobile code unchanged, but wrap in div with header)
  }

  const isExistingReport = status === "Completed" && !taskId; // Simple heuristic for now

  // Desktop Architecture: Three-Pane Layout
  return (
    <div className="h-screen w-full bg-[#111111] text-[#EAEAEA] font-sans flex flex-col overflow-hidden">
      <Header />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Source Library (Fixed Width) */}
        <div className="w-[300px] border-r border-[#2A2A2A] bg-[#161616] flex flex-col h-full overflow-hidden shrink-0 relative">
          <div className="absolute top-4 right-4 z-10 flex flex-col gap-2 items-end">
            {graphState?.fdd_report_draft && (
              <button 
                onClick={() => handlePrint()}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded text-xs font-medium transition-colors shadow-lg"
              >
                <Download size={12} />
                Export PDF
              </button>
            )}
            
            <div className="flex gap-2">
               {status === "Completed" && (
                 <button 
                  onClick={() => startPipeline(ticker || "AAPL", `Regenerating research for ${ticker}`, true)}
                  className="flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-white px-3 py-1.5 rounded text-xs font-medium transition-colors"
                >
                  <RefreshCw size={12} />
                  Refresh
                </button>
               )}
               <button 
                onClick={() => startPipeline(ticker || "AAPL", `Forced re-run for ${ticker || "AAPL"}`, true)}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded text-xs font-medium transition-colors"
              >
                <Zap size={12} />
                {status === "Idle" ? "Start Run" : "Re-Run"}
              </button>
            </div>
          </div>
          <LeftPaneSourceLibrary graphState={graphState} status={status} />
        </div>

        {/* Center Pane: Dynamic Research Canvas (Fluid Width) */}
        <div className="flex-1 bg-[#111111] h-full overflow-hidden relative">
          <CenterPaneResearchCanvas
              graphState={graphState}
              status={status}
              diff={diff}
              notebookEntries={notebookEntries}
              onFetchDiff={fetchDiff}
              onRefresh={triggerRefresh}
              onAnnotate={annotateClaim}
              onOverride={overrideClaim}
              onSuppress={suppressClaim}
            />
        </div>

        {/* Right Pane: Review Gate & Analyst Hub (Fixed Width) */}
        <div className="w-[380px] border-l border-[#2A2A2A] bg-[#161616] flex flex-col h-full overflow-hidden shrink-0">
          <RightPaneReviewGate
            graphState={graphState}
            status={status}
            analystReviewItems={analystReviewItems}
            onApprove={approveSynthesis}
            onInject={injectGuidance}
            onDirectEdit={directEdit}
            onInjectClaim={(dim, fp, text) => injectClaim(graphState?.resolved_identity?.ticker || graphState?.ticker || '', dim, fp, text)}
            onEditSection={editFDDSection}
            onAdjudicate={adjudicateThesis}
            onRegenerateSection={regenerateFDDSection}
            onPublish={publishFDD}
            onSchedule={schedulePublication}
            onRetract={retractReport}
            onResolveReviewItem={resolveReviewItem}
            onDismissReviewItem={dismissReviewItem}
            onClearResolvedItems={clearResolvedItems}
            onOptimize={optimizePrompts}
            publishedReport={publishedReport}
          />
        </div>
      </div>

      {/* Hidden Print Template */}
      <div className="hidden print:block">
        <FDDReportTemplate ref={printRef} fddDraft={graphState?.fdd_report_draft} />
      </div>
    </div>
  );
}
