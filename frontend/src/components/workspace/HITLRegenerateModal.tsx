"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Bot, Layers } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (text: string) => void;
  onRegenerateSection?: (sectionId: string, feedback: string) => void;
  sections?: string[];
}

export function HITLRegenerateModal({ isOpen, onClose, onConfirm, onRegenerateSection, sections = [] }: Props) {
  const [prompt, setPrompt] = useState("");
  const [selectedSection, setSelectedSection] = useState<string>("global");

  const handleConfirm = () => {
    if (!prompt.trim()) return;
    
    if (selectedSection === "global") {
      onConfirm(prompt);
    } else if (onRegenerateSection) {
      onRegenerateSection(selectedSection, prompt);
    }
    
    onClose();
    setPrompt("");
  };

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
              className="w-full max-w-lg bg-[#161616] border border-[#333333] rounded-xl shadow-2xl pointer-events-auto overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="px-5 py-4 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-500/20 p-2 rounded-lg text-blue-400">
                    <Bot size={18} />
                  </div>
                  <div>
                    <h2 className="text-white font-medium">Analyst Override & Regenerate</h2>
                    <p className="text-xs text-[#888888]">Direct Layer 5 Synthesis with custom context.</p>
                  </div>
                </div>
                <button onClick={onClose} className="text-[#666666] hover:text-white transition-colors">
                  <X size={20} />
                </button>
              </div>

              {/* Body */}
              <div className="p-5 space-y-4">
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-2 flex items-center gap-2">
                    <Layers size={12} /> Target Scope
                  </label>
                  <select
                    value={selectedSection}
                    onChange={(e) => setSelectedSection(e.target.value)}
                    className="w-full bg-[#111111] border border-[#333333] rounded-lg p-2.5 text-sm text-[#EAEAEA] focus:outline-none focus:border-blue-500"
                  >
                    <option value="global">Global (Full Report Re-synthesis)</option>
                    {sections.map(sec => (
                      <option key={sec} value={sec}>
                        Section: {sec.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-2">
                    Guidance Prompt
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={selectedSection === 'global' ? "e.g., Focus more on the TSMC delay implications..." : "Provide feedback for this specific section..."}
                    className="w-full h-32 bg-[#111111] border border-[#333333] rounded-lg p-3 text-sm text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none transition-all"
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="px-5 py-4 border-t border-[#2A2A2A] bg-[#1A1A1A] flex justify-end gap-3">
                <button 
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-[#888888] hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleConfirm}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors flex items-center gap-2 shadow-lg shadow-blue-900/20"
                >
                  <Send size={14} />
                  {selectedSection === 'global' ? 'Inject Guidance' : 'Regenerate Section'}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
