"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ArrowRight, BookOpen, AlertCircle } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  currentDraft: any;
  publishedReport: any;
}

export function FDDVersionDiffModal({ isOpen, onClose, currentDraft, publishedReport }: Props) {
  if (!currentDraft || !publishedReport) return null;

  const compareSections = () => {
    const diffs: { title: string; old: string; new: string }[] = [];

    // Compare Executive Summary
    if (currentDraft.executive_summary?.content !== publishedReport.executive_summary) {
      diffs.push({
        title: "Executive Summary",
        old: publishedReport.executive_summary || "",
        new: currentDraft.executive_summary?.content || ""
      });
    }

    // Compare Sections
    const publishedSections = JSON.parse(publishedReport.sections_json || "{}");
    const currentSections = currentDraft.sections || {};

    const allKeys = new Set([
      ...Object.keys(publishedSections),
      ...Object.keys(currentSections)
    ]);

    allKeys.forEach(key => {
      const oldContent = publishedSections[key]?.content || "";
      const newContent = currentSections[key]?.content || "";
      if (oldContent !== newContent) {
        diffs.push({
          title: currentSections[key]?.title || publishedSections[key]?.title || key,
          old: oldContent,
          new: newContent
        });
      }
    });

    return diffs;
  };

  const sectionDiffs = compareSections();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />
          
          <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-5xl bg-[#161616] border border-[#333333] rounded-xl shadow-2xl pointer-events-auto overflow-hidden flex flex-col h-[85vh]"
            >
              {/* Header */}
              <div className="px-6 py-5 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-500/20 p-2 rounded-lg text-blue-400">
                    <BookOpen size={20} />
                  </div>
                  <div>
                    <h2 className="text-white font-medium text-lg">Version Comparison</h2>
                    <p className="text-xs text-[#888888]">Comparing Current Draft vs. Published Version ({publishedReport.version})</p>
                  </div>
                </div>
                <button onClick={onClose} className="text-[#666666] hover:text-white transition-colors">
                  <X size={24} />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-[#111111]">
                {sectionDiffs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-20 text-[#666666]">
                    <AlertCircle size={48} className="mb-4 opacity-20" />
                    <p>No changes detected between current draft and published version.</p>
                  </div>
                ) : (
                  sectionDiffs.map((diff, idx) => (
                    <div key={idx} className="space-y-3">
                      <h3 className="text-sm font-bold text-[#AAAAAA] uppercase tracking-wider">{diff.title}</h3>
                      <div className="grid grid-cols-2 gap-4 h-[300px]">
                        <div className="flex flex-col">
                          <span className="text-[10px] text-[#555555] mb-2 uppercase font-bold">Published Version</span>
                          <div className="flex-1 bg-[#1A1A1A] border border-[#222222] rounded-lg p-4 text-xs text-[#888888] overflow-y-auto leading-relaxed font-mono whitespace-pre-wrap">
                            {diff.old || <span className="italic opacity-30">Section was empty or did not exist.</span>}
                          </div>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[10px] text-emerald-500/70 mb-2 uppercase font-bold">Current Draft</span>
                          <div className="flex-1 bg-[#1A1A1A] border border-emerald-500/20 rounded-lg p-4 text-xs text-[#CCCCCC] overflow-y-auto leading-relaxed font-mono whitespace-pre-wrap">
                            {diff.new || <span className="italic opacity-30">Section is empty.</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-[#2A2A2A] bg-[#1A1A1A] flex justify-end">
                <button 
                  onClick={onClose}
                  className="px-6 py-2 rounded-lg text-sm font-medium bg-[#333333] hover:bg-[#444444] text-white transition-colors"
                >
                  Close Comparison
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
