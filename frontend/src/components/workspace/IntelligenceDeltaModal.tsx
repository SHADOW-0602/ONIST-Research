"use client";

import React, { useState, useEffect } from "react";
import { X, Zap, ChevronRight, History, GitPullRequest, Search } from "lucide-react";

interface PromptDiff {
  dimension: string;
  prompt_name: string;
  baseline: string;
  optimized: string;
  last_updated: string;
}

export function IntelligenceDeltaModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [history, setHistory] = useState<PromptDiff[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptDiff | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetch("/api/v1/prompts/history")
        .then(res => res.json())
        .then(data => {
          setHistory(data.history || []);
          setLoading(false);
          if (data.history?.length > 0) setSelectedPrompt(data.history[0]);
        })
        .catch(err => console.error(err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-8">
      <div className="bg-[#111111] border border-[#333333] rounded-2xl w-full max-w-6xl h-full flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-[#222222] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Zap className="text-amber-400" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Intelligence Evolution Dashboard</h2>
              <p className="text-xs text-[#666666] mt-0.5">Visualizing the delta between baseline templates and Analyst-Optimized instructions.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[#222222] rounded-full transition-colors">
            <X size={20} className="text-[#555555]" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <div className="w-80 border-r border-[#222222] overflow-y-auto bg-black/20">
            <div className="p-4 space-y-2">
              {loading ? (
                <div className="text-center py-10 text-[#444444] text-sm italic">Loading history...</div>
              ) : history.length === 0 ? (
                <div className="text-center py-10 text-[#444444] text-sm italic">No optimized prompts yet. Run an optimization cycle to see results.</div>
              ) : (
                history.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedPrompt(p)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedPrompt?.prompt_name === p.prompt_name 
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-400" 
                        : "bg-[#161616] border-[#222222] text-[#AAAAAA] hover:border-[#333333]"
                    }`}
                  >
                    <div className="text-[10px] font-bold uppercase tracking-widest opacity-50 mb-1">{p.dimension}</div>
                    <div className="text-xs font-semibold truncate">{p.prompt_name}</div>
                    <div className="text-[10px] opacity-40 mt-1 flex items-center gap-1">
                      <History size={10} />
                      {new Date(p.last_updated).toLocaleDateString()}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Diff Content */}
          <div className="flex-1 overflow-y-auto bg-[#0A0A0A] p-6">
            {selectedPrompt ? (
              <div className="space-y-6">
                <div className="flex items-center gap-4 text-[#555555]">
                   <div className="h-[1px] flex-1 bg-[#222222]"></div>
                   <span className="text-[10px] font-bold uppercase tracking-widest">Instructional Mutation Analysis</span>
                   <div className="h-[1px] flex-1 bg-[#222222]"></div>
                </div>

                <div className="grid grid-cols-2 gap-6 h-full min-h-[600px]">
                  {/* Baseline */}
                  <div className="flex flex-col">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-[10px] font-bold text-[#666666] uppercase tracking-widest px-2 py-1 bg-black/40 rounded">Baseline Template</span>
                    </div>
                    <div className="flex-1 bg-black/40 rounded-xl border border-[#222222] p-4 font-mono text-[11px] text-[#555555] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                      {selectedPrompt.baseline || "(Baseline not found)"}
                    </div>
                  </div>

                  {/* Optimized */}
                  <div className="flex flex-col">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest px-2 py-1 bg-amber-500/10 rounded">Optimized Version</span>
                      <span className="text-[10px] text-amber-500/50 flex items-center gap-1">
                         <GitPullRequest size={10} />
                         Layer 6 Mutation Applied
                      </span>
                    </div>
                    <div className="flex-1 bg-[#161616] rounded-xl border border-amber-500/20 p-4 font-mono text-[11px] text-[#AAAAAA] overflow-y-auto whitespace-pre-wrap leading-relaxed shadow-inner">
                      {selectedPrompt.optimized}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-[#444444] text-sm italic">
                Select a prompt from the sidebar to visualize its evolution.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
