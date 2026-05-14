"use client";

import React from "react";
import { ShieldAlert } from "lucide-react";

interface Props {
  content: string;
}

export function VerificationHighlighter({ content }: Props) {
  // Very simplistic parser looking for [Unverified ...] markers for UI demonstration
  const parts = content.split(/(\[Unverified[^\]]*\])/g);

  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith("[Unverified")) {
          return (
            <span 
              key={i} 
              className="inline-flex items-baseline gap-1 bg-amber-500/10 border border-amber-500/30 text-amber-200 px-1.5 py-0.5 rounded cursor-help relative group"
            >
              <ShieldAlert size={12} className="relative top-0.5 text-amber-500" />
              <span className="opacity-90">{part.replace("[Unverified —", "").replace("]", "").trim()}</span>
              
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-[#1A1A1A] border border-[#333333] rounded shadow-xl text-[10px] text-[#AAAAAA] opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
                This claim requires analyst verification. Not backed by SEC filings.
              </div>
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}
