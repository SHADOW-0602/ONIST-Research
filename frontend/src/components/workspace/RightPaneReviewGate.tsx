"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  MessageSquare, 
  Edit, 
  RefreshCcw, 
  ThumbsUp, 
  Lock,
  Target,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  BookOpen,
  History,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Edit3,
  Database,
  Trash2,
  PlayCircle,
  Zap,
  Info,
  GitCompare,
  ShieldAlert
} from "lucide-react";
import { IntelligenceDeltaModal } from "./IntelligenceDeltaModal";
import { HITLRegenerateModal } from "./HITLRegenerateModal";
import { HITLDirectEditModal } from "./HITLDirectEditModal";
import { HITLApprovalModal } from "./HITLApprovalModal";
import { FDDSectionEditModal } from "./FDDSectionEditModal";
import { FDDVersionDiffModal } from "./FDDVersionDiffModal";
import { AnalystReviewPanel } from "./AnalystReviewPanel";
import type { ReviewItem } from "../../hooks/usePipeline";

interface Props {
  graphState: any;
  status: string;
  analystReviewItems?: ReviewItem[];
  onApprove: (approve?: boolean, feedback?: string) => void;
  onInject: (text: string) => void;
  onDirectEdit: (text: string) => void;
  onInjectClaim: (dimension: string, fieldPath: string, claimText: string, source: string) => void;
  onEditSection: (sectionId: string, newContent: string) => void;
  onAdjudicate: (action: 'accept_bull' | 'accept_bear' | 'neutral') => void;
  onRegenerateSection: (sectionId: string, feedback: string) => void;
  onPublish: () => Promise<string | null>;
  onSchedule: (reportId: string, timestamp: string) => void;
  onRetract: (reportId: string) => void;
  onResolveReviewItem?: (index: number) => void;
  onDismissReviewItem?: (index: number) => void;
  onClearResolvedItems?: () => void;
  onOptimize?: () => Promise<boolean>;
  publishedReport?: any;
}

export function RightPaneReviewGate({ 
  graphState, 
  status,
  analystReviewItems = [],
  onApprove, 
  onInject, 
  onDirectEdit, 
  onInjectClaim,
  onEditSection,
  onAdjudicate,
  onRegenerateSection,
  onPublish,
  onSchedule,
  onRetract,
  onResolveReviewItem,
  onDismissReviewItem,
  onClearResolvedItems,
  onOptimize,
  publishedReport
}: Props) {
  const [isRegenerateOpen, setIsRegenerateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [isSectionEditOpen, setIsSectionEditOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  // ── Derive state from real graphState ──────────────────────────────────────
  const isPendingReview = status === "Pending Analyst Review";
  const isCompleted = status === "Completed" || status === "Completed (Published)";
  const isLoading = !isPendingReview && !isCompleted && status !== "Idle" && !status.startsWith("Error");
  const isError = status.startsWith("Error");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isDeltaOpen, setIsDeltaOpen] = useState(false);
  const [optimizeSuccess, setOptimizeSuccess] = useState(false);

  // Derive sections for the edit modal
  const reportDraft = graphState?.fdd_report_draft || {};
  const sectionList = [];
  if (reportDraft.executive_summary) {
    sectionList.push({ id: "executive_summary", title: "Executive Summary", content: reportDraft.executive_summary.content });
  }
  if (reportDraft.sections) {
    Object.entries(reportDraft.sections).forEach(([id, data]: [string, any]) => {
      if (!data || typeof data !== "object") return; // skip null/non-object sections
      sectionList.push({ id, title: data.title || id, content: data.content ?? "" });
    });
  }

  // Bull / Bear conflict data from Layer 5
  const bullThesis = graphState?.bull_thesis;
  const bearThesis = graphState?.bear_thesis;
  const conflictResolution = graphState?.conflict_resolution;
  const hasDebate = Boolean(bullThesis && bearThesis);
  const hasConflict = graphState?.conflict_detected ||
    (conflictResolution?.analyst_review_items?.length > 0) ||
    (bullThesis && bearThesis && !conflictResolution);

  // Use the prop-driven analystReviewItems (sourced from top-level graphState)
  const pendingCount = analystReviewItems.filter((i) => i.status === "PENDING").length;

  // DB persistence indicator
  const hasDraftPersisted = Boolean(graphState?.publication_id) || 
    Boolean(graphState?.fdd_report_draft && Object.keys(graphState.fdd_report_draft).length > 0);

  const [thesisActionTaken, setThesisActionTaken] = useState<string | null>(null);

  const handleAdjudicate = (action: 'accept_bull' | 'accept_bear') => {
    onAdjudicate(action);
    setThesisActionTaken(action);
  };

  return (
    <div className="flex flex-col h-full bg-[#161616]">
      {/* Header */}
      <div className="p-4 border-b border-[#2A2A2A] shrink-0 bg-[#1A1A1A]">
        <h2 className="text-xs font-semibold tracking-widest text-[#888888] uppercase mb-1">Human-in-the-Loop</h2>
        <div className="flex justify-between items-center">
          <h1 className="text-lg font-medium text-white tracking-tight">Review Hub</h1>
          {isPendingReview && (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
          )}
          {isCompleted && <CheckCircle size={16} className="text-emerald-500" />}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">

        {/* Pipeline loading state */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center h-48 gap-3 text-[#555555]">
            <Loader2 size={24} className="animate-spin text-blue-500" />
            <p className="text-xs text-center text-[#666666]">{status}</p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex flex-col items-center gap-2 p-3 rounded-lg bg-red-950/20 border border-red-500/20">
            <AlertTriangle size={18} className="text-red-500" />
            <p className="text-xs text-red-400 text-center">{status}</p>
          </div>
        )}

        {/* Idle / empty state */}
        {status === "Idle" && (
          <div className="flex flex-col items-center justify-center h-48 gap-2 text-[#555555]">
            <p className="text-xs text-center">Awaiting pipeline run.<br />Start one to unlock review actions.</p>
          </div>
        )}

        {/* ── Bull / Bear Debate Card ─────────────────────────────────────── */}
        {hasDebate && (
          <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg overflow-hidden">
            <div className={`px-3 py-2 border-b flex items-center justify-between ${hasConflict ? "bg-amber-500/10 border-amber-500/20" : "bg-[#222222] border-[#333333]"}`}>
              <div className="flex items-center gap-2">
                <AlertTriangle size={13} className={hasConflict ? "text-amber-500" : "text-[#666666]"} />
                <span className={`text-xs font-semibold uppercase tracking-widest ${hasConflict ? "text-amber-500" : "text-[#888888]"}`}>
                  {hasConflict ? "Active Debate Conflict" : "Bull / Bear Debate"}
                </span>
              </div>
              {thesisActionTaken && (
                <span className="text-[10px] text-emerald-400 font-bold uppercase">Adjudicated</span>
              )}
            </div>

            <div className="p-3 space-y-3">
              {/* Bull side */}
              <div>
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-500 uppercase mb-1">
                  <TrendingUp size={11} /> Bull Thesis
                </div>
                <div className="text-xs text-[#CCCCCC] leading-relaxed">
                  {bullThesis?.bull_thesis_summary ||
                   bullThesis?.thesis_statement ||
                   (typeof bullThesis === "string" ? bullThesis : "Bull thesis generated.")}
                </div>
              </div>

              <div className="h-px bg-[#333333] w-full" />

              {/* Bear side */}
              <div>
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-500 uppercase mb-1">
                  <TrendingDown size={11} /> Bear Thesis
                </div>
                <div className="text-xs text-[#CCCCCC] leading-relaxed">
                  {bearThesis?.bear_thesis_summary ||
                   bearThesis?.thesis_statement ||
                   (typeof bearThesis === "string" ? bearThesis : "Bear thesis generated.")}
                </div>
              </div>

              {/* Resolution */}
              {conflictResolution && (
                <>
                  <div className="h-px bg-[#333333] w-full" />
                  <div>
                    <div className="text-[10px] font-bold text-blue-400 uppercase mb-1">Conflict Resolution</div>
                    <div className="text-xs text-[#CCCCCC] leading-relaxed">
                      {conflictResolution?.resolution_summary ||
                       conflictResolution?.verdict ||
                       "Resolution complete."}
                    </div>
                  </div>
                </>
              )}
            </div>

            {hasConflict && isPendingReview && !thesisActionTaken && (
              <div className="bg-[#1A1A1A] border-t border-[#2A2A2A] p-2 flex gap-2">
                <button
                  onClick={() => handleAdjudicate('accept_bull')}
                  className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 text-xs py-1.5 rounded font-medium transition-colors border border-emerald-500/20"
                >
                  Accept Bull
                </button>
                <button
                  onClick={() => handleAdjudicate('accept_bear')}
                  className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-xs py-1.5 rounded font-medium transition-colors border border-red-500/20"
                >
                  Accept Bear
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Quality & Analyst Review Flags (from backend analyst_review_node) ── */}
        {isPendingReview && (
          <div>
            {/* DB persistence indicator */}
            {hasDraftPersisted && (
              <div className="flex items-center gap-2 mb-3 p-2 rounded bg-emerald-950/20 border border-emerald-500/20">
                <Database size={12} className="text-emerald-500" />
                <p className="text-[11px] text-emerald-400">Draft persisted to CockroachDB</p>
              </div>
            )}
            {/* [NEW] Layer 7 — Automated Trading Signal */}
            {graphState?.trading_signal && (
              <div className={`mt-4 p-4 rounded-xl border-2 shadow-lg animate-in fade-in slide-in-from-bottom-2 duration-500 ${
                graphState.trading_signal.action === 'BUY' 
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-400' 
                  : graphState.trading_signal.action === 'SELL'
                    ? 'bg-red-950/20 border-red-500/40 text-red-400'
                    : 'bg-[#1A1A1A] border-[#333333] text-[#AAAAAA]'
              }`}>
                <div className="flex items-center justify-between mb-3">
                   <div className="flex items-center gap-2">
                     <div className={`p-1.5 rounded-lg ${
                       graphState.trading_signal.action === 'BUY' ? 'bg-emerald-500/20' : 'bg-red-500/20'
                     }`}>
                       <PlayCircle size={18} />
                     </div>
                     <span className="text-sm font-bold uppercase tracking-widest">Institutional Signal</span>
                   </div>
                   <div className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-black/40 border border-white/10 uppercase tracking-tighter">
                     {graphState.trading_signal.execution_priority} PRIORITY
                   </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-[10px] opacity-60 font-medium mb-1">RECOMMENDED ACTION</div>
                    <div className="text-2xl font-black italic tracking-tighter">{graphState.trading_signal.action}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] opacity-60 font-medium mb-1">CONVICTION</div>
                    <div className="text-2xl font-black italic tracking-tighter">{graphState.trading_signal.confidence_level}</div>
                  </div>
                </div>

                <div className="space-y-2 pt-3 border-t border-white/5">
                   <div className="flex justify-between text-[11px]">
                     <span className="opacity-50">Sizing</span>
                     <span className="font-bold">{graphState.trading_signal.sizing}</span>
                   </div>
                   <div className="flex justify-between text-[11px]">
                     <span className="opacity-50">Risk/Reward</span>
                     <span className="font-bold">{graphState.trading_signal.risk_reward}</span>
                   </div>
                   <div className="mt-2 text-[10px] bg-black/40 p-2 rounded border border-white/5 leading-relaxed italic">
                     <span className="text-red-400 font-bold not-italic">STOP LOSS: </span>
                     {graphState.trading_signal.stop_loss_trigger}
                   </div>
                </div>
              </div>
            )}

            {/* [NEW] Layer 7 — Investment Committee Minutes */}
            {graphState?.investment_committee_minutes && (
              <div className="mt-4 p-3 rounded-lg bg-indigo-950/10 border border-indigo-500/20">
                <div className="flex items-center gap-2 mb-2 text-indigo-400">
                  <ShieldAlert size={14} />
                  <span className="text-[11px] font-bold uppercase tracking-wider">Layer 7 — Investment Committee</span>
                </div>
                <div className="space-y-2">
                  <div className="p-2 rounded bg-black/40 border border-red-500/10">
                    <div className="text-[10px] text-red-400 font-bold mb-1">THE SKEPTIC</div>
                    <p className="text-[11px] text-[#AAAAAA] leading-relaxed italic line-clamp-2">
                      {graphState.investment_committee_minutes.skeptic_critique?.skeptical_conclusion}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-black/40 border border-emerald-500/10">
                    <div className="text-[10px] text-emerald-400 font-bold mb-1">THE OPTIMIST</div>
                    <p className="text-[11px] text-[#AAAAAA] leading-relaxed italic line-clamp-2">
                      {graphState.investment_committee_minutes.optimist_defense?.optimistic_conclusion}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-indigo-500/10 border border-indigo-500/30">
                    <div className="text-[10px] text-indigo-400 font-bold mb-1">CIO VERDICT: {graphState.investment_committee_minutes.cio_verdict?.committee_consensus}</div>
                    <p className="text-[11px] text-[#EAEAEA] leading-relaxed font-medium">
                      {graphState.investment_committee_minutes.cio_verdict?.guidance_to_analyst}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* [NEW] Layer 7 — Systemic Risk (Contagion) */}
            {graphState?.systemic_risks && graphState.systemic_risks.length > 0 && (
              <div className="mt-4 p-3 rounded-lg bg-red-950/10 border border-red-500/20">
                <div className="flex items-center gap-2 mb-2 text-red-400">
                  <GitCompare size={14} />
                  <span className="text-[11px] font-bold uppercase tracking-wider">Layer 7 — Systemic Risk (Contagion)</span>
                </div>
                <div className="space-y-1.5">
                  {graphState.systemic_risks.map((risk: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-1.5 rounded bg-black/30 border border-white/5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white bg-red-900/40 px-1.5 py-0.5 rounded">{risk.ticker}</span>
                        <span className="text-[10px] text-[#AAAAAA]">{risk.reason}</span>
                      </div>
                      <span className={`text-[9px] font-bold uppercase ${risk.severity === 'High' ? 'text-red-500' : 'text-amber-500'}`}>
                        {risk.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <AnalystReviewPanel
              reviewItems={analystReviewItems}
              onResolve={onResolveReviewItem}
              onDismiss={onDismissReviewItem}
            />
            {/* Clear button */}
            {analystReviewItems.some((i) => i.status !== "PENDING") && onClearResolvedItems && (
              <button
                onClick={onClearResolvedItems}
                className="mt-2 flex items-center gap-1.5 text-[11px] text-[#666666] hover:text-red-400 transition-colors"
              >
                <Trash2 size={11} /> Clear resolved/dismissed
              </button>
            )}
          </div>
        )}

        {/* ── Analyst Actions ─────────────────────────────────────────────── */}
        {(isPendingReview || isCompleted) && (
          <div>
            <h3 className="text-xs font-semibold text-[#888888] uppercase tracking-widest mb-3">Analyst Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => setIsRegenerateOpen(true)}
                disabled={!isPendingReview}
                className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#222222] hover:bg-[#2A2A2A] disabled:opacity-40 disabled:cursor-not-allowed border border-[#333333] rounded-lg text-sm text-[#EAEAEA] font-medium transition-colors"
              >
                <RotateCcw size={16} className="text-blue-400" />
                Regenerate Sections
              </button>
              <button
                onClick={() => setIsEditOpen(true)}
                disabled={!isPendingReview}
                className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#222222] hover:bg-[#2A2A2A] disabled:opacity-40 disabled:cursor-not-allowed border border-[#333333] rounded-lg text-sm text-[#EAEAEA] font-medium transition-colors"
              >
                <Edit3 size={16} className="text-emerald-400" />
                Manual Data Injection
              </button>
              <button
                onClick={() => setIsSectionEditOpen(true)}
                disabled={!isPendingReview}
                className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#222222] hover:bg-[#2A2A2A] disabled:opacity-40 disabled:cursor-not-allowed border border-[#333333] rounded-lg text-sm text-[#EAEAEA] font-medium transition-colors"
              >
                <BookOpen size={16} className="text-amber-400" />
                Edit FDD Sections
              </button>

              {publishedReport && (
                <button
                  onClick={() => setIsCompareOpen(true)}
                  disabled={!isPendingReview}
                  className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#222222] hover:bg-[#2A2A2A] disabled:opacity-40 disabled:cursor-not-allowed border border-[#333333] rounded-lg text-sm text-[#EAEAEA] font-medium transition-colors"
                >
                  <History size={16} className="text-blue-400" />
                  Compare with Published
                </button>
              )}

              <div className="pt-2">
                <button
                  onClick={async () => {
                    if (!onOptimize) return;
                    setIsOptimizing(true);
                    const success = await onOptimize();
                    setIsOptimizing(false);
                    if (success) {
                      setOptimizeSuccess(true);
                      setTimeout(() => setOptimizeSuccess(false), 3000);
                    }
                  }}
                  disabled={isOptimizing || !hasDraftPersisted}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border ${
                    optimizeSuccess 
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-[#222222] hover:bg-[#2A2A2A] border-[#333333] text-[#EAEAEA]"
                  } disabled:opacity-40 disabled:cursor-not-allowed`}
                >
                  {isOptimizing ? (
                    <Loader2 size={16} className="animate-spin text-amber-400" />
                  ) : (
                    <Zap size={16} className={optimizeSuccess ? "text-emerald-400" : "text-amber-400"} />
                  )}
                  {optimizeSuccess ? "Intelligence Optimized" : "Optimize Intelligence"}
                </button>
                <button
                  onClick={() => setIsDeltaOpen(true)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#1A1A1A] hover:bg-[#222222] border border-amber-500/20 rounded-lg text-sm text-[#AAAAAA] font-medium transition-colors mb-2"
                >
                  <History size={16} className="text-amber-500" />
                  View Intelligence History
                </button>
                <p className="text-[10px] text-[#555555] mt-1.5 px-1 leading-relaxed">
                  Refines research prompts based on your edits. Run after publishing to improve future accuracy.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <IntelligenceDeltaModal isOpen={isDeltaOpen} onClose={() => setIsDeltaOpen(false)} />

      {/* Footer Publishing Action */}
      <div className="p-4 border-t border-[#2A2A2A] shrink-0 bg-[#1A1A1A]">
        {/* Pending flags warning */}
        {pendingCount > 0 && isPendingReview && (
          <div className="flex items-center gap-2 mb-2 p-2 rounded bg-amber-950/20 border border-amber-500/20">
            <AlertTriangle size={12} className="text-amber-500 shrink-0" />
            <p className="text-[11px] text-amber-400">
              {pendingCount} unresolved flag{pendingCount > 1 ? "s" : ""} — review before publishing
            </p>
          </div>
        )}
        <button
          onClick={() => setIsApprovalOpen(true)}
          disabled={!isPendingReview}
          className={`w-full font-semibold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
            isPendingReview
              ? "bg-white text-black hover:bg-gray-200"
              : isCompleted
                ? "bg-emerald-900/40 text-emerald-400 border border-emerald-500/30"
                : "bg-[#333333] text-[#666666] cursor-not-allowed"
          }`}
        >
          <ThumbsUp size={16} />
          {isCompleted ? "Report Published" : isPendingReview ? "Approve & Publish FDD" : "Waiting for Pipeline…"}
        </button>
      </div>

      {/* Modals */}
      <HITLRegenerateModal
        isOpen={isRegenerateOpen}
        onClose={() => setIsRegenerateOpen(false)}
        onConfirm={onInject}
        onRegenerateSection={onRegenerateSection}
        sections={graphState?.fdd_report_draft?.sections ? Object.keys(graphState.fdd_report_draft.sections) : []}
      />
      <HITLDirectEditModal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        onConfirm={onInjectClaim}
      />
      <HITLApprovalModal
        isOpen={isApprovalOpen}
        onClose={() => setIsApprovalOpen(false)}
        onConfirm={onApprove}
        onPublish={onPublish}
        onSchedule={onSchedule}
      />
      <FDDSectionEditModal
        isOpen={isSectionEditOpen}
        onClose={() => setIsSectionEditOpen(false)}
        onConfirm={onEditSection}
        sections={sectionList}
      />
      <FDDVersionDiffModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        currentDraft={graphState?.fdd_report_draft}
        publishedReport={publishedReport}
      />
    </div>
  );
}
