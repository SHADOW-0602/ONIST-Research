"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Globe, Database, TrendingUp, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { usePipeline } from "../../hooks/usePipeline";

export function TickerSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { searchTickers } = usePipeline();

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 1) {
        setIsLoading(true);
        const data = await searchTickers(query);
        setResults(data);
        setIsLoading(false);
      } else {
        setResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchTickers]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (ticker: string) => {
    router.push(`/workspace/${ticker}`);
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto z-50">
      <div className={`relative flex items-center transition-all duration-300 ${isFocused ? 'scale-[1.02]' : ''}`}>
        <div className="absolute left-6 text-gray-400">
          <Search size={22} className={isFocused ? 'text-blue-500' : ''} />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          placeholder="Search Ticker or Company (e.g. AAPL, NVIDIA)..."
          className="w-full bg-[#1A1A1A] border-2 border-[#333333] focus:border-blue-600/50 text-white rounded-full py-5 px-16 text-lg outline-none transition-all shadow-2xl placeholder:text-gray-600"
        />
        {isLoading && (
          <div className="absolute right-6">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {isFocused && (results.length > 0 || query.length > 0) && (
          <motion.div
            ref={dropdownRef}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute top-full mt-4 w-full bg-[#161616] border border-[#333333] rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] backdrop-blur-xl"
          >
            <div className="p-2">
              {results.length > 0 ? (
                results.map((item, idx) => (
                  <motion.button
                    key={`${item.ticker}-${idx}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    onClick={() => handleSelect(item.ticker)}
                    className="w-full flex items-center justify-between p-4 hover:bg-blue-600/10 rounded-xl transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${item.source === 'Notebook' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-blue-500/10 text-blue-500 border border-blue-500/20'}`}>
                        {item.source === 'Notebook' ? <Database size={18} /> : <Globe size={18} />}
                      </div>
                      <div className="text-left">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-lg tracking-wider">{item.ticker}</span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-black uppercase tracking-tight ${item.source === 'Notebook' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-blue-500/10 text-blue-400'}`}>
                            {item.source}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500 truncate w-64">{item.name}</div>
                      </div>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowRight size={18} className="text-blue-500" />
                    </div>
                  </motion.button>
                ))
              ) : (
                query.length > 0 && !isLoading && (
                  <button
                    onClick={() => handleSelect(query.toUpperCase())}
                    className="w-full flex items-center justify-between p-4 hover:bg-blue-600/10 rounded-xl transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center border border-blue-500/20">
                        <TrendingUp size={18} />
                      </div>
                      <div className="text-left">
                        <span className="font-bold text-white text-lg tracking-wider">INITIATE: {query.toUpperCase()}</span>
                        <div className="text-sm text-gray-500">No existing records. Start fresh research run.</div>
                      </div>
                    </div>
                    <ArrowRight size={18} className="text-blue-500" />
                  </button>
                )
              )}
            </div>
            
            <div className="border-t border-[#333333] p-3 bg-[#1A1A1A] flex justify-between items-center px-6">
               <span className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">YFINANCE API + ONIST COMPENDIUM</span>
               <div className="flex gap-4">
                  <div className="flex items-center gap-1.5 text-[10px] text-emerald-500 font-bold">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                    REAL-TIME SYNC
                  </div>
               </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
