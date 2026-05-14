"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ExternalLink,
  Flag,
  Loader2,
} from "lucide-react";

interface ReviewItem {
  dimension: string;
  issue: string;
  status: "PENDING" | "RESOLVED" | "DISMISSED";
}

interface Props {
  reviewItems: ReviewItem[];
  onResolve?: (index: number) => void;
  onDismiss?: (index: number) => void;
  isLoading?: boolean;
}

const DIMENSION_LABELS: Record<string, string> = {
  identity: "Corporate Identity",
  sector: "Sector & Market",
  business_mechanics: "Business Mechanics",
  business_segments: "Business Segments",
  business_strategy: "Strategy",
  management_bios: "Management Bios",
  management_comp: "Management Compensation",
  dossier: "Corporate Dossier",
  footprint: "Global Footprint",
};

const DIMENSION_COLORS: Record<string, string> = {
  identity: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  sector: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  business_mechanics: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  business_segments: "text-green-400 bg-green-500/10 border-green-500/20",
  business_strategy: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  management_bios: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  management_comp: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  dossier: "text-red-400 bg-red-500/10 border-red-500/20",
  footprint: "text-teal-400 bg-teal-500/10 border-teal-500/20",
};

function classifyIssue(issue: string): "critical" | "warning" | "info" {
  const upper = issue.toUpperCase();
  if (upper.includes("CRITICAL") || upper.includes("LITIGATION") || upper.includes("FRAUD")) return "critical";
  if (upper.includes("UNVERIFIED") || upper.includes("WARNING") || upper.includes("MISSING")) return "warning";
  return "info";
}

const SEVERITY_CONFIG = {
  critical: {
    icon: ShieldAlert,
    containerClass: "bg-red-950/30 border-red-500/30",
    iconClass: "text-red-400",
    badgeClass: "bg-red-500/10 text-red-400 border-red-500/20",
    label: "Critical",
  },
  warning: {
    icon: AlertTriangle,
    containerClass: "bg-amber-950/20 border-amber-500/20",
    iconClass: "text-amber-400",
    badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    label: "Warning",
  },
  info: {
    icon: Flag,
    containerClass: "bg-blue-950/20 border-blue-500/20",
    iconClass: "text-blue-400",
    badgeClass: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    label: "Review",
  },
};

function ReviewItemCard({
  item,
  index,
  onResolve,
  onDismiss,
}: {
  item: ReviewItem;
  index: number;
  onResolve?: (i: number) => void;
  onDismiss?: (i: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const severity = classifyIssue(item.issue);
  const cfg = SEVERITY_CONFIG[severity];
  const Icon = cfg.icon;
  const dimLabel = DIMENSION_LABELS[item.dimension] || item.dimension.replace(/_/g, " ");
  const dimColor = DIMENSION_COLORS[item.dimension] || "text-gray-400 bg-gray-500/10 border-gray-500/20";

  const isDone = item.status === "RESOLVED" || item.status === "DISMISSED";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: isDone ? 0.45 : 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
      className={`rounded-lg border overflow-hidden transition-opacity ${cfg.containerClass}`}
    >
      {/* Header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-2.5 p-3 text-left hover:brightness-110 transition-all"
      >
        <Icon size={14} className={`mt-0.5 shrink-0 ${cfg.iconClass}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded border ${cfg.badgeClass}`}>
              {cfg.label}
            </span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border capitalize ${dimColor}`}>
              {dimLabel}
            </span>
            {isDone && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                item.status === "RESOLVED"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-gray-500/10 text-gray-400 border-gray-500/20"
              }`}>
                {item.status}
              </span>
            )}
          </div>
          <p className="text-xs text-[#CCCCCC] leading-relaxed line-clamp-2">{item.issue}</p>
        </div>
        {expanded ? (
          <ChevronDown size={13} className="text-[#666666] shrink-0 mt-0.5" />
        ) : (
          <ChevronRight size={13} className="text-[#666666] shrink-0 mt-0.5" />
        )}
      </button>

      {/* Expanded body */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 border-t border-white/5 pt-2">
              <p className="text-xs text-[#AAAAAA] leading-relaxed mb-3">{item.issue}</p>
              {!isDone && (
                <div className="flex gap-2">
                  {onResolve && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onResolve(index); }}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 text-xs font-medium border border-emerald-500/20 transition-colors"
                    >
                      <CheckCircle2 size={12} /> Mark Resolved
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDismiss(index); }}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-[#222222] hover:bg-[#2A2A2A] text-[#888888] text-xs font-medium border border-[#333333] transition-colors"
                    >
                      <XCircle size={12} /> Dismiss
                    </button>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function AnalystReviewPanel({ reviewItems, onResolve, onDismiss, isLoading }: Props) {
  const critical = reviewItems.filter((i) => classifyIssue(i.issue) === "critical");
  const warnings = reviewItems.filter((i) => classifyIssue(i.issue) === "warning");
  const infos = reviewItems.filter((i) => classifyIssue(i.issue) === "info");
  const pending = reviewItems.filter((i) => i.status === "PENDING").length;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-32 gap-2 text-[#555555]">
        <Loader2 size={18} className="animate-spin text-amber-500" />
        <p className="text-xs">Loading review items...</p>
      </div>
    );
  }

  if (reviewItems.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/20">
        <ShieldCheck size={20} className="text-emerald-500" />
        <p className="text-xs text-emerald-400 font-medium text-center">No flags raised</p>
        <p className="text-[11px] text-[#666666] text-center">All claims passed verification gates. Report is auto-eligible for publication.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Summary bar */}
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-[#888888] uppercase tracking-widest">
          Analyst Flags
        </h3>
        <div className="flex items-center gap-2">
          {critical.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
              <ShieldAlert size={10} /> {critical.length}
            </span>
          )}
          {warnings.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle size={10} /> {warnings.length}
            </span>
          )}
          {pending > 0 && (
            <span className="text-[10px] text-[#666666]">{pending} pending</span>
          )}
        </div>
      </div>

      {/* Grouped by severity */}
      <div className="space-y-2">
        {[...critical, ...warnings, ...infos].map((item, i) => (
          <ReviewItemCard
            key={`${item.dimension}-${i}`}
            item={item}
            index={i}
            onResolve={onResolve}
            onDismiss={onDismiss}
          />
        ))}
      </div>
    </div>
  );
}
