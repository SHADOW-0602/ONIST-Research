"use client";

import React from "react";

interface Props {
  ticker: string;
}

export function TickerSparkline({ ticker }: Props) {
  // Static SVG sparkline for visual representation (Mocking Polygon API data)
  return (
    <div className="w-full h-full flex items-center justify-end">
      <div className="flex flex-col items-end">
        <span className="text-emerald-400 font-medium text-sm">+2.4%</span>
        <svg viewBox="0 0 100 30" className="w-24 h-6 overflow-visible">
          <path
            d="M0,25 C10,25 15,10 25,15 C35,20 45,5 50,10 C55,15 65,25 75,15 C85,5 95,10 100,5"
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M0,25 C10,25 15,10 25,15 C35,20 45,5 50,10 C55,15 65,25 75,15 C85,5 95,10 100,5 L100,30 L0,30 Z"
            fill="url(#sparkline-gradient)"
            opacity="0.2"
          />
          <defs>
            <linearGradient id="sparkline-gradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="transparent" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
