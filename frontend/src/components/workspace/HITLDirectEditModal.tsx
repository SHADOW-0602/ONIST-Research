"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, Tag } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (dimension: string, fieldPath: string, claimText: string, source: string) => void;
}

const DIMENSIONS = [
  "identity", "sector", "business_mechanics", "business_segments",
  "business_strategy", "management_comp", "management_bios", "dossier", "footprint"
];

export function HITLDirectEditModal({ isOpen, onClose, onConfirm }: Props) {
  const [dimension, setDimension] = useState(DIMENSIONS[0]);
  const [fieldPath, setFieldPath] = useState("");
  const [claimText, setClaimText] = useState("");
  const [source, setSource] = useState("Private Management Meeting");

  const canSubmit = fieldPath.trim() && claimText.trim();

  const handleSubmit = () => {
    if (!canSubmit) return;
    onConfirm(dimension, fieldPath, claimText, source);
    onClose();
    setFieldPath("");
    setClaimText("");
    setSource("Private Management Meeting");
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-lg bg-[#161616] border border-[#333333] rounded-xl shadow-2xl pointer-events-auto overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="px-5 py-4 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
                <div className="flex items-center gap-3">
                  <div className="bg-emerald-500/20 p-2 rounded-lg text-emerald-400">
                    <Plus size={18} />
                  </div>
                  <div>
                    <h2 className="text-white font-medium">Manual Data Injection</h2>
                    <p className="text-xs text-[#888888]">Add an analyst-sourced claim directly to the Notebook.</p>
                  </div>
                </div>
                <button onClick={onClose} className="text-[#666666] hover:text-white transition-colors">
                  <X size={20} />
                </button>
              </div>

              {/* Body */}
              <div className="p-5 space-y-4">
                {/* Dimension selector */}
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-1.5">Dimension</label>
                  <select
                    value={dimension}
                    onChange={e => setDimension(e.target.value)}
                    className="w-full bg-[#111111] border border-[#333333] rounded-lg px-3 py-2 text-sm text-[#EAEAEA] focus:outline-none focus:border-emerald-500 capitalize"
                  >
                    {DIMENSIONS.map(d => (
                      <option key={d} value={d}>{d.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                </div>

                {/* Field path */}
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-1.5">Field Path</label>
                  <input
                    type="text"
                    value={fieldPath}
                    onChange={e => setFieldPath(e.target.value)}
                    placeholder="e.g. ceo_succession_plan, board_composition.independent"
                    className="w-full bg-[#111111] border border-[#333333] rounded-lg px-3 py-2 text-sm text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>

                {/* Claim text */}
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-1.5">Claim</label>
                  <textarea
                    value={claimText}
                    onChange={e => setClaimText(e.target.value)}
                    rows={4}
                    placeholder="Enter the claim exactly as it should appear in the Notebook. It will be tagged as [Analyst injection]."
                    className="w-full bg-[#111111] border border-[#333333] rounded-lg px-3 py-2 text-sm text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-emerald-500 resize-none"
                  />
                </div>

                {/* Source */}
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-1.5">
                    <Tag size={10} className="inline mr-1" />Source
                  </label>
                  <input
                    type="text"
                    value={source}
                    onChange={e => setSource(e.target.value)}
                    placeholder="e.g. Private Management Meeting, Expert Network Call"
                    className="w-full bg-[#111111] border border-[#333333] rounded-lg px-3 py-2 text-sm text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-emerald-500"
                  />
                </div>

                {/* Audit notice */}
                <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <div className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-500 mt-1" />
                  <p className="text-[11px] text-amber-300/70 leading-relaxed">
                    This claim will be tagged <strong className="text-amber-400">[Analyst injection]</strong> and bypasses agent verification gates. It will appear in the FDD report with full audit attribution.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="px-5 py-4 border-t border-[#2A2A2A] bg-[#1A1A1A] flex justify-end gap-3">
                <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-[#888888] hover:text-white transition-colors">
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors flex items-center gap-2 shadow-lg shadow-emerald-900/20"
                >
                  <Plus size={14} />
                  Inject into Notebook
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
