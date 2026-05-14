"use client";

import React, { useState } from "react";
import { FileText, ShieldCheck, ShieldAlert, CheckCircle2, Loader2, WifiOff } from "lucide-react";
import { SourceViewModal } from "./SourceViewModal";

interface Props {
  graphState: any;
  status: string;
}

// Derive a flat source list from the verification_handoffs structure in graphState
function deriveSourcesFromState(graphState: any): Array<{
  id: string;
  title: string;
  fullTitle: string;
  dimension: string;
  tier: string;
  verified: boolean;
  date: string;
  text: string;
  sourceType: string;
  provider: string;
}> {
  if (!graphState?.verification_handoffs) return [];

  const sources: any[] = [];

  for (const [dimension, handoff] of Object.entries<any>(graphState.verification_handoffs)) {
    const sourceIds: string[] = handoff?.source_documents || [];
    const tierMap: Record<string, string> = handoff?.source_tier_map || {};
    const registry = graphState?.source_registry || {};

    sourceIds.forEach((srcId: string, i: number) => {
      const tier = tierMap[srcId] || "Unknown";
      const entry = registry[srcId];
      const text = typeof entry === 'string' ? entry : (entry?.text || "No content available.");
      const metadata = typeof entry === 'string' ? {} : (entry?.metadata || {});
      
      const isVerified = tier === "Tier1" || tier === "Tier2";
      sources.push({
        id: `${dimension}-${i}`,
        title: srcId.length > 50 ? srcId.slice(0, 50) + "…" : srcId,
        fullTitle: srcId,
        dimension,
        tier,
        verified: isVerified,
        date: graphState?.run_date || "—",
        text,
        sourceType: metadata.source_type || (tier === "tier_1" ? "Official Filing" : "Supporting Doc"),
        provider: metadata.provider || "System"
      });
    });
  }

  return sources;
}

const TIER_LABEL: Record<string, string> = {
  Tier1: "SEC Filing",
  Tier2: "News / Research",
  Tier3: "Unverified Web",
  Unknown: "Unknown",
};

export function LeftPaneSourceLibrary({ graphState, status }: Props) {
  const [selectedSource, setSelectedSource] = useState<any | null>(null);
  const sources = deriveSourcesFromState(graphState);
  const isLoading = status !== "Idle" && status !== "Completed" && !status.startsWith("Error") && sources.length === 0;
  const isError = status.startsWith("Error");

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-[#2A2A2A] shrink-0">
        <h2 className="text-xs font-semibold tracking-widest text-[#888888] uppercase mb-1">Layer 0</h2>
        <h1 className="text-lg font-medium text-white tracking-tight">Source Library</h1>
        {sources.length > 0 && (
          <p className="text-xs text-[#666666] mt-0.5">{sources.length} sources indexed</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center h-40 gap-3 text-[#555555]">
            <Loader2 size={22} className="animate-spin text-blue-500" />
            <p className="text-xs">Indexing sources…</p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex flex-col items-center justify-center h-40 gap-3 text-[#555555]">
            <WifiOff size={22} className="text-red-500/60" />
            <p className="text-xs text-red-400/70">Pipeline error — check backend logs.</p>
          </div>
        )}

        {/* Idle / empty state */}
        {!isLoading && !isError && sources.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 gap-2 text-[#555555]">
            <FileText size={22} />
            <p className="text-xs text-center">No sources yet.<br />Start a pipeline run to index documents.</p>
          </div>
        )}

        {/* Real source cards */}
        {sources.map((source) => (
          <div
            key={source.id}
            onClick={() => setSelectedSource({
              title: source.fullTitle || source.title,
              text: source.text,
              tier: TIER_LABEL[source.tier] || source.tier,
              dimension: source.dimension,
              sourceType: source.sourceType,
              provider: source.provider
            })}
            className="group relative bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-3 hover:border-blue-500/50 hover:bg-[#252525] transition-all cursor-pointer"
          >
            <div className="flex items-start gap-2 mb-2">
              <FileText size={14} className="text-[#666666] mt-0.5 shrink-0" />
              <span className="text-sm font-medium text-[#EAEAEA] leading-snug break-words">{source.title}</span>
            </div>

            <div className="flex items-center justify-between text-xs mt-2">
              <span className="text-[#666666] font-mono capitalize">{source.dimension.replace(/_/g, " ")}</span>

              <div className="flex items-center gap-1">
                {source.verified ? (
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium">
                    <ShieldCheck size={11} />
                    <span>{TIER_LABEL[source.tier] || source.tier}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-medium">
                    <ShieldAlert size={11} />
                    <span>{TIER_LABEL[source.tier] || source.tier}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-[#2A2A2A] shrink-0 bg-[#1A1A1A]">
        <div className="flex items-center justify-between text-xs text-[#888888]">
          <span>Gate 2 Source Auditor</span>
          <div className={`flex items-center gap-1 ${sources.length > 0 ? "text-emerald-500" : "text-[#555555]"}`}>
            <CheckCircle2 size={12} />
            <span>{sources.length > 0 ? "Active" : "Standby"}</span>
          </div>
        </div>
      </div>

      <SourceViewModal
        isOpen={!!selectedSource}
        onClose={() => setSelectedSource(null)}
        source={selectedSource}
      />
    </div>
  );
}
