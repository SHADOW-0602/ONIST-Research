"use client";

import React, { useState } from "react";
import {
  Copy, Sparkles, AlertTriangle, Loader2, PlayCircle, ShieldAlert,
  MessageSquare, ShieldCheck, EyeOff, RotateCcw, ChevronDown, ChevronUp,
  Plus, GitCompare
} from "lucide-react";
import { VerificationHighlighter } from "@/components/workspace/VerificationHighlighter";
import { TickerSparkline } from "@/components/workspace/TickerSparkline";

interface Props {
  graphState: any;
  status: string;
  diff: any;
  notebookEntries?: Record<string, any[]>;
  onFetchDiff: () => void;
  onRefresh: (dimension?: string) => void;
  onAnnotate: (entryId: string, type: string, text: string) => void;
  onOverride: (entryId: string, confidence: string) => void;
  onSuppress: (entryId: string, reason: string) => void;
}

// ── Confidence tier options ─────────────────────────────────────────────────
const CONFIDENCE_TIERS = [
  { value: "primary_confirmed", label: "Primary Confirmed", color: "text-emerald-400" },
  { value: "secondary_reported", label: "Secondary Reported", color: "text-blue-400" },
  { value: "agent_inferred", label: "Agent Inferred", color: "text-amber-400" },
  { value: "unverified", label: "Unverified", color: "text-red-400" },
];

// ── Per-claim inline action toolbar ─────────────────────────────────────────
function ClaimActionBar({ entryId, dimension, onAnnotate, onOverride, onSuppress, onRefresh }: {
  entryId: string;
  dimension: string;
  onAnnotate: (id: string, type: string, text: string) => void;
  onOverride: (id: string, confidence: string) => void;
  onSuppress: (id: string, reason: string) => void;
  onRefresh: (dimension: string) => void;
}) {
  const [mode, setMode] = useState<null | "annotate" | "override" | "suppress">(null);
  const [text, setText] = useState("");
  const [selectedConf, setSelectedConf] = useState("primary_confirmed");

  const close = () => { setMode(null); setText(""); };

  const submit = () => {
    if (mode === "annotate" && text.trim()) onAnnotate(entryId, "commentary", text);
    if (mode === "override") onOverride(entryId, selectedConf);
    if (mode === "suppress" && text.trim()) onSuppress(entryId, text);
    close();
  };

  return (
    <div className="mt-3 border-t border-[#222222] pt-2">
      {/* Action buttons row */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <button
          onClick={() => setMode(mode === "annotate" ? null : "annotate")}
          className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium transition-colors ${mode === "annotate" ? "bg-blue-500/20 text-blue-400" : "bg-[#222222] text-[#777777] hover:text-[#AAAAAA]"}`}
        >
          <MessageSquare size={11} /> Annotate
        </button>
        <button
          onClick={() => setMode(mode === "override" ? null : "override")}
          className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium transition-colors ${mode === "override" ? "bg-emerald-500/20 text-emerald-400" : "bg-[#222222] text-[#777777] hover:text-[#AAAAAA]"}`}
        >
          <ShieldCheck size={11} /> Override Confidence
        </button>
        <button
          onClick={() => setMode(mode === "suppress" ? null : "suppress")}
          className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium transition-colors ${mode === "suppress" ? "bg-red-500/20 text-red-400" : "bg-[#222222] text-[#777777] hover:text-[#AAAAAA]"}`}
        >
          <EyeOff size={11} /> Suppress
        </button>
        <button
          onClick={() => onRefresh(dimension)}
          className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-[#222222] text-[#777777] hover:text-amber-400 transition-colors"
        >
          <RotateCcw size={11} /> Refresh Dimension
        </button>
      </div>

      {/* Inline forms */}
      {mode === "annotate" && (
        <div className="mt-2 flex gap-2">
          <input
            type="text"
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Add commentary, nuance, or limitation note..."
            className="flex-1 bg-[#111111] border border-[#333333] rounded px-2 py-1 text-xs text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-blue-500"
          />
          <button onClick={submit} className="px-3 py-1 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors">Save</button>
          <button onClick={close} className="px-2 py-1 text-xs text-[#666666] hover:text-white">✕</button>
        </div>
      )}

      {mode === "override" && (
        <div className="mt-2 flex gap-2 items-center">
          <select
            value={selectedConf}
            onChange={e => setSelectedConf(e.target.value)}
            className="flex-1 bg-[#111111] border border-[#333333] rounded px-2 py-1 text-xs text-[#EAEAEA] focus:outline-none focus:border-emerald-500"
          >
            {CONFIDENCE_TIERS.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button onClick={submit} className="px-3 py-1 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors">Apply</button>
          <button onClick={close} className="px-2 py-1 text-xs text-[#666666] hover:text-white">✕</button>
        </div>
      )}

      {mode === "suppress" && (
        <div className="mt-2 flex gap-2">
          <input
            type="text"
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Reason for suppression (will be retained for audit)..."
            className="flex-1 bg-[#111111] border border-[#333333] rounded px-2 py-1 text-xs text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-red-500"
          />
          <button onClick={submit} className="px-3 py-1 text-xs font-medium bg-red-700 hover:bg-red-600 text-white rounded transition-colors">Suppress</button>
          <button onClick={close} className="px-2 py-1 text-xs text-[#666666] hover:text-white">✕</button>
        </div>
      )}
    </div>
  );
}

// ── Notebook Diff Panel (A6) ─────────────────────────────────────────────────
const STATUS_STYLES: Record<string, string> = {
  new: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  updated: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  deprecated: "bg-red-500/10 text-red-400 border-red-500/20",
};

function NotebookDiffPanel({ diff, onFetchDiff }: { diff: any; onFetchDiff: () => void }) {
  const [open, setOpen] = useState(false);
  const entries = diff?.entries || [];
  const summary = diff?.summary || { new: 0, updated: 0, deprecated: 0 };

  return (
    <div className="border border-[#2A2A2A] rounded-lg overflow-hidden mb-8">
      <button
        onClick={() => { setOpen(!open); if (!open && !diff) onFetchDiff(); }}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#1A1A1A] hover:bg-[#222222] transition-colors"
      >
        <div className="flex items-center gap-3">
          <GitCompare size={15} className="text-[#888888]" />
          <span className="text-sm font-medium text-[#CCCCCC]">What Changed — Notebook Diff</span>
          {diff && (
            <div className="flex gap-2 text-[11px] font-semibold">
              {summary.new > 0 && <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">{summary.new} new</span>}
              {summary.updated > 0 && <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{summary.updated} updated</span>}
              {summary.deprecated > 0 && <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">{summary.deprecated} deprecated</span>}
            </div>
          )}
        </div>
        {open ? <ChevronUp size={14} className="text-[#666666]" /> : <ChevronDown size={14} className="text-[#666666]" />}
      </button>

      {open && (
        <div className="divide-y divide-[#1E1E1E]">
          {entries.length === 0 && (
            <div className="p-6 text-center text-[#555555] text-sm">
              {diff ? "No changes detected since last run." : "Loading diff..."}
            </div>
          )}
          {entries.map((entry: any) => (
            <div key={entry.id} className="p-4 flex flex-col sm:flex-row gap-3 items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[11px] font-semibold text-[#666666] tracking-wider uppercase capitalize">{entry.dimension.replace(/_/g, " ")}</span>
                  <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border font-bold ${STATUS_STYLES[entry.status] || ""}`}>{entry.status}</span>
                </div>
                <p className="text-sm text-[#D4D4D4] leading-relaxed">{entry.claim}</p>
                {entry.status === "updated" && (
                  <div className="mt-2 flex items-center gap-2 text-xs font-mono bg-black/30 px-2 py-1 rounded border border-white/5 inline-flex">
                    <span className="text-[#555555] line-through">{entry.previousValue?.slice(0, 60)}…</span>
                    <span className="text-[#444444]">→</span>
                    <span className="text-blue-400 font-medium">{entry.newValue?.slice(0, 60)}…</span>
                  </div>
                )}
              </div>
              <div className="text-xs text-[#555555] bg-[#1A1A1A] px-2 py-1 rounded border border-[#2A2A2A] whitespace-nowrap shrink-0">
                {entry.source}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────
export function CenterPaneResearchCanvas({ graphState, status, diff, notebookEntries, onFetchDiff, onRefresh, onAnnotate, onOverride, onSuppress }: Props) {
  const handleCopy = (content: string) => { navigator.clipboard.writeText(content); };

  const ticker: string = graphState?.resolved_identity?.ticker || graphState?.ticker || "—";
  const company: string = graphState?.resolved_identity?.company_name || graphState?.company_name_input || "ONIST Research";
  const runDate: string = graphState?.run_date || null;

  // ── Build sections from agent_outputs ──────────────────────────────────────
  const sections: Array<{ id: string; title: string; dimension: string; content: string; hasUnverified: boolean }> = [];

  const activeData = (graphState?.agent_outputs && Object.keys(graphState.agent_outputs).length > 0) 
    ? graphState.agent_outputs 
    : notebookEntries;
    
  if (activeData && Object.keys(activeData).length > 0) {
    for (const [dimension, data] of Object.entries<any>(activeData)) {
      if (!data) continue;
      let content = "";
      if (typeof data === "string") {
        content = data;
      } else if (Array.isArray(data)) {
        content = data.map((c: any) => {
          const val = c?.value;
          if (typeof val === "string") return val;
          if (val?.claim) return val.claim;
          return JSON.stringify(val);
        }).join("\n\n");
      } else if (typeof data === "object") {
        const claimArr: string[] = [];
        const items = Array.isArray(data) ? data : Object.values(data);
        for (const v of items) {
          if (Array.isArray(v)) {
            v.forEach((item: any) => {
              if (item?.value?.claim) claimArr.push(item.value.claim);
              else if (typeof item?.value === "string") claimArr.push(item.value);
            });
          } else if (typeof v === "object" && v !== null) {
              if (v.value?.claim) claimArr.push(v.value.claim);
              else if (v.claim) claimArr.push(v.claim);
          } else if (typeof v === "string") {
            claimArr.push(v);
          }
        }
        content = claimArr.join("\n\n") || JSON.stringify(data, null, 2);
      }
      sections.push({
        id: dimension,
        dimension,
        title: dimension.replace(/_/g, " "),
        content: content.trim() || "(No content extracted)",
        hasUnverified: content.includes("[Unverified"),
      });
    }
  }

  const isIdle = status === "Idle";
  const isLoading = !isIdle && status !== "Completed" && !status.startsWith("Error") && sections.length === 0;
  const isError = status.startsWith("Error");

  return (
    <div className="h-full flex flex-col bg-[#111111]">
      {/* Header */}
      <div className="px-8 py-5 border-b border-[#2A2A2A] shrink-0 flex items-center justify-between bg-[#141414]">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-semibold tracking-tight text-white">{company}</h1>
            {ticker !== "—" && (
              <span className="px-2 py-0.5 rounded text-xs font-bold tracking-wider bg-[#222222] text-[#888888] border border-[#333333]">{ticker}</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-[#666666]">
            <span className={`font-medium ${isError ? "text-red-400" : "text-blue-400"}`}>{status}</span>
            {runDate && <><span>•</span><span>Run Date: {runDate}</span></>}
            {sections.length > 0 && (
              <><span>•</span>
              <span className="text-emerald-500/80 flex items-center gap-1">
                <Sparkles size={12} /> {sections.length} dimensions indexed
              </span></>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* A5: Global refresh button */}
          {sections.length > 0 && (
            <button
              onClick={() => onRefresh()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1E1E1E] hover:bg-[#2A2A2A] border border-[#333333] rounded text-xs font-medium text-[#888888] hover:text-amber-400 transition-colors"
            >
              <RotateCcw size={13} /> Full Re-Run
            </button>
          )}
          {ticker !== "—" && <div className="w-48 h-12"><TickerSparkline ticker={ticker} /></div>}
        </div>
      </div>

      {/* Scroll Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-4xl mx-auto pb-20">

          {/* A6: Diff panel — shown if data exists or can be fetched */}
          {(diff || sections.length > 0) && (
            <NotebookDiffPanel diff={diff} onFetchDiff={onFetchDiff} />
          )}

          {/* Idle */}
          {isIdle && (
            <div className="flex flex-col items-center justify-center h-80 gap-4 text-[#444444]">
              <PlayCircle size={48} strokeWidth={1} />
              <div className="text-center">
                <p className="text-base font-medium text-[#666666]">Research Canvas is empty</p>
                <p className="text-sm mt-1">Start a pipeline run to synthesize an FDD notebook.</p>
              </div>
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-80 gap-4 text-[#444444]">
              <Loader2 size={36} strokeWidth={1.5} className="animate-spin text-blue-500" />
              <div className="text-center">
                <p className="text-sm font-medium text-[#666666]">{status}</p>
                <p className="text-xs mt-1 text-[#444444]">Agents are gathering and verifying claims…</p>
              </div>
              <div className="w-full max-w-xl mt-4 space-y-3 opacity-30">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-4 bg-[#2A2A2A] rounded animate-pulse" style={{ width: `${75 + i * 5}%` }} />
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="flex flex-col items-center justify-center h-60 gap-3">
              <ShieldAlert size={36} className="text-red-500/60" />
              <p className="text-sm text-red-400/70">{status}</p>
            </div>
          )}

          {/* Live sections with inline claim actions */}
          <div className="space-y-10">
            {sections.map((section) => (
              <section key={section.id} className="group">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-semibold tracking-widest uppercase text-[#888888] capitalize">{section.title}</h2>
                    {section.hasUnverified && <AlertTriangle size={13} className="text-amber-500" />}
                  </div>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onRefresh(section.dimension)}
                      className="flex items-center gap-1 px-2 py-1 rounded bg-[#1E1E1E] hover:bg-[#2A2A2A] text-xs text-[#666666] hover:text-amber-400 transition-colors"
                    >
                      <RotateCcw size={12} /> Refresh
                    </button>
                    <button
                      onClick={() => handleCopy(section.content)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-[#1E1E1E] hover:bg-[#2A2A2A] text-xs font-medium text-[#AAAAAA] transition-all"
                    >
                      <Copy size={14} /> Copy
                    </button>
                  </div>
                </div>

                <div className="text-[15px] leading-relaxed text-[#D4D4D4] font-medium max-w-none whitespace-pre-wrap">
                  <VerificationHighlighter content={section.content} />
                </div>

                {/* A1/A2/A3: Per-section claim action bar */}
                <ClaimActionBar
                  entryId={section.id}
                  dimension={section.dimension}
                  onAnnotate={onAnnotate}
                  onOverride={onOverride}
                  onSuppress={onSuppress}
                  onRefresh={onRefresh}
                />
              </section>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}
