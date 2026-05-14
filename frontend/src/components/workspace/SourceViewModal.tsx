"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, FileText, Copy, Check } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  source: {
    title: string;
    text: string;
    tier: string;
    dimension: string;
    sourceType: string;
    provider: string;
  } | null;
}

export function SourceViewModal({ isOpen, onClose, source }: Props) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    if (source?.text) {
      navigator.clipboard.writeText(source.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const cleanText = (text: string) => {
    if (!text) return "";
    // Remove SGML headers and tags
    let clean = text.replace(/<SEC-HEADER>[\s\S]*?<\/SEC-HEADER>/g, "");
    clean = clean.replace(/<[^>]*>?/gm, "");
    // Unescape common HTML entities
    clean = clean.replace(/&nbsp;/g, " ")
                 .replace(/&#160;/g, " ")
                 .replace(/&amp;/g, "&")
                 .replace(/&lt;/g, "<")
                 .replace(/&gt;/g, ">");
    // Normalize whitespace
    clean = clean.replace(/\n\s*\n/g, "\n\n").trim();
    return clean;
  };

  if (!source) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-4xl max-h-[85vh] bg-[#161616] border border-[#2A2A2A] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
                  <FileText size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight leading-none mb-2">
                    Source Document Viewer
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[9px] font-bold uppercase tracking-wider border border-blue-500/20">
                      {source.sourceType}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 text-[9px] font-bold uppercase tracking-wider border border-purple-500/20">
                      via {source.provider}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest ml-1">
                      {source.tier}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                </button>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 bg-[#0F0F0F] custom-scrollbar">
              <div className="mb-6">
                <h4 className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.2em] mb-2">Reference Title</h4>
                <div className="text-sm font-medium text-gray-300 break-all bg-white/5 p-3 rounded-lg border border-white/5 font-mono">
                  {source.title}
                </div>
              </div>

              <div>
                <h4 className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.2em] mb-2">Extracted Content</h4>
                <div className="text-[15px] text-gray-300 leading-relaxed font-sans whitespace-pre-wrap bg-white/[0.01] p-6 rounded-xl border border-white/5 shadow-inner">
                  {cleanText(source.text)}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 bg-[#1A1A1A] border-t border-[#2A2A2A] flex justify-end">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-bold text-white transition-all uppercase tracking-widest"
              >
                Done
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
