"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Save, Edit3, Lock } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (sectionId: string, content: string) => void;
  sections: { id: string; title: string; content: string }[];
}

export function FDDSectionEditModal({ isOpen, onClose, onConfirm, sections }: Props) {
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    if (sections.length > 0 && !selectedSectionId) {
      setSelectedSectionId(sections[0].id);
      setContent(sections[0].content);
    }
  }, [sections, selectedSectionId]);

  const handleSectionChange = (id: string) => {
    setSelectedSectionId(id);
    const section = sections.find(s => s.id === id);
    if (section) setContent(section.content);
  };

  const handleSave = () => {
    if (selectedSectionId && content) {
      onConfirm(selectedSectionId, content);
      onClose();
    }
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
              className="w-full max-w-2xl bg-[#161616] border border-[#333333] rounded-xl shadow-2xl pointer-events-auto overflow-hidden flex flex-col h-[80vh]"
            >
              {/* Header */}
              <div className="px-5 py-4 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
                <div className="flex items-center gap-3">
                  <div className="bg-emerald-500/20 p-2 rounded-lg text-emerald-400">
                    <Edit3 size={18} />
                  </div>
                  <div>
                    <h2 className="text-white font-medium">Override FDD Section</h2>
                    <p className="text-xs text-[#888888]">Manually edit section content. This will lock the section from auto-regeneration.</p>
                  </div>
                </div>
                <button onClick={onClose} className="text-[#666666] hover:text-white transition-colors">
                  <X size={20} />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 flex flex-col min-h-0">
                <div className="p-4 border-b border-[#2A2A2A] bg-[#111111]">
                  <select
                    value={selectedSectionId}
                    onChange={(e) => handleSectionChange(e.target.value)}
                    className="w-full bg-transparent border-none text-white font-medium focus:ring-0 cursor-pointer"
                  >
                    {sections.map(s => (
                      <option key={s.id} value={s.id} className="bg-[#161616]">{s.title}</option>
                    ))}
                  </select>
                </div>

                <div className="flex-1 p-5 min-h-0">
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-full bg-[#111111] border border-[#333333] rounded-lg p-4 text-sm text-[#CCCCCC] leading-relaxed placeholder:text-[#444444] focus:outline-none focus:border-emerald-500 transition-all font-mono"
                    spellCheck={false}
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="px-5 py-4 border-t border-[#2A2A2A] bg-[#1A1A1A] flex justify-between items-center">
                <div className="flex items-center gap-2 text-[#666666] text-xs">
                  <Lock size={12} />
                  Analyst Override Mode
                </div>
                <div className="flex gap-3">
                  <button 
                    onClick={onClose}
                    className="px-4 py-2 rounded-lg text-sm font-medium text-[#888888] hover:text-white transition-colors"
                  >
                    Discard Changes
                  </button>
                  <button 
                    onClick={handleSave}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center gap-2 shadow-lg shadow-emerald-900/20"
                  >
                    <Save size={14} />
                    Save & Lock Section
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
