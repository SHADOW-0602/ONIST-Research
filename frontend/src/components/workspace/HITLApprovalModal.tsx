"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Globe, ThumbsDown, Send, Calendar, Clock } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (approve?: boolean, feedback?: string) => void;
  onPublish?: () => Promise<string | null>;
  onSchedule?: (reportId: string, timestamp: string) => void;
}

export function HITLApprovalModal({ isOpen, onClose, onConfirm, onPublish, onSchedule }: Props) {
  const [isRejecting, setIsRejecting] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [scheduleDate, setScheduleDate] = useState("");

  const handleApprove = async () => {
    if (onPublish) await onPublish();
    onConfirm(true);
    onClose();
  };

  const handleSchedule = async () => {
    if (!scheduleDate || !onPublish || !onSchedule) return;
    const reportId = await onPublish();
    if (reportId) {
      onSchedule(reportId, scheduleDate);
    }
    onConfirm(true);
    onClose();
  };

  const handleReject = () => {
    if (!feedback.trim()) return;
    onConfirm(false, feedback);
    onClose();
    setIsRejecting(false);
    setIsScheduling(false);
    setFeedback("");
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
              className="w-full max-w-sm bg-[#161616] border border-[#333333] rounded-xl shadow-2xl pointer-events-auto overflow-hidden flex flex-col"
            >
              <div className="px-5 py-4 border-b border-[#2A2A2A] flex items-center justify-between bg-[#1A1A1A]">
                <h2 className="text-white font-medium">
                  {isRejecting ? "Reject Draft" : isScheduling ? "Schedule Publication" : "Final Gate"}
                </h2>
                <button onClick={onClose} className="text-[#666666] hover:text-white transition-colors">
                  <X size={20} />
                </button>
              </div>

              {isScheduling ? (
                <div className="p-5">
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-2">
                    Select Date & Time
                  </label>
                  <div className="relative">
                    <input
                      type="datetime-local"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      className="w-full bg-[#111111] border border-[#333333] rounded-lg p-3 text-sm text-[#EAEAEA] focus:outline-none focus:border-blue-500 transition-all [color-scheme:dark]"
                    />
                  </div>
                  <p className="mt-3 text-[10px] text-[#666666]">
                    The report will be automatically published at the selected time. You can retract it anytime before then.
                  </p>
                </div>
              ) : !isRejecting ? (
                <div className="p-5 text-center">
                  <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4 text-white">
                    <Globe size={24} />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">Publish FDD Report</h3>
                  <p className="text-sm text-[#888888]">
                    This will persist the verified FDD report to CockroachDB and mark it as the current active published version.
                  </p>
                </div>
              ) : (
                <div className="p-5">
                  <label className="block text-xs font-semibold tracking-wider text-[#888888] uppercase mb-2">
                    Rejection Feedback
                  </label>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Provide specific reasons for rejection to guide re-synthesis..."
                    className="w-full h-32 bg-[#111111] border border-[#333333] rounded-lg p-3 text-sm text-[#EAEAEA] placeholder:text-[#555555] focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 resize-none transition-all"
                  />
                </div>
              )}

              <div className="px-5 py-4 border-t border-[#2A2A2A] bg-[#1A1A1A] flex flex-col gap-2">
                {isScheduling ? (
                  <>
                    <button 
                      onClick={handleSchedule}
                      disabled={!scheduleDate}
                      className="w-full py-2.5 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-blue-900/20"
                    >
                      Confirm Schedule
                    </button>
                    <button 
                      onClick={() => setIsScheduling(false)}
                      className="w-full py-2.5 rounded-lg text-sm font-medium text-[#888888] hover:bg-[#2A2A2A] transition-colors"
                    >
                      Back
                    </button>
                  </>
                ) : !isRejecting ? (
                  <>
                    <button 
                      onClick={handleApprove}
                      className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-gray-200 transition-colors shadow-lg"
                    >
                      Confirm & Publish Now
                    </button>
                    <button 
                      onClick={() => setIsScheduling(true)}
                      className="w-full py-2.5 rounded-lg text-sm font-medium bg-[#222222] text-white hover:bg-[#2A2A2A] border border-[#333333] transition-colors flex items-center justify-center gap-2"
                    >
                      <Calendar size={14} className="text-blue-400" />
                      Schedule for Later
                    </button>
                    <button 
                      onClick={() => setIsRejecting(true)}
                      className="w-full py-2.5 rounded-lg text-sm font-medium text-red-500 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-colors flex items-center justify-center gap-2"
                    >
                      <ThumbsDown size={14} />
                      Reject Draft
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={handleReject}
                      disabled={!feedback.trim()}
                      className="w-full py-2.5 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 shadow-lg shadow-red-900/20"
                    >
                      <Send size={14} />
                      Send Feedback & Reject
                    </button>
                    <button 
                      onClick={() => setIsRejecting(false)}
                      className="w-full py-2.5 rounded-lg text-sm font-medium text-[#888888] hover:bg-[#2A2A2A] transition-colors"
                    >
                      Back
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
