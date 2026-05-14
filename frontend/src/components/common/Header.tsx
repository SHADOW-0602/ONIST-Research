"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { History, ChevronDown, Database, Clock, ArrowRight, ExternalLink, Trash2, AlertTriangle, X, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const params = useParams();
  const router = useRouter();
  const activeTicker = params.ticker as string;

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    // Fetch all tickers that have notebooks/reports
    const fetchHistory = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/tickers/search?q=');
        if (res.ok) {
          const data = await res.json();
          // Filter only Notebook sources (which means they have local data)
          setHistory(data.results.filter((r: any) => r.source === 'Notebook'));
        }
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, [activeTicker]);

  const handleDelete = async () => {
    if (!activeTicker) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/research/delete/${activeTicker}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setIsDeleteDialogOpen(false);
        router.push('/');
      } else {
        console.error("Failed to delete ticker data");
      }
    } catch (err) {
      console.error("Error during deletion", err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <header className="h-16 border-b border-[#2A2A2A] bg-[#111111]/80 backdrop-blur-xl flex items-center justify-between px-6 sticky top-0 z-[100]">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-emerald-600 rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.2)] group-hover:shadow-[0_0_30px_rgba(37,99,235,0.4)] transition-all">
            <span className="text-white font-black text-xs">ON</span>
          </div>
          <span className="text-white font-bold tracking-tight text-lg">ONIST</span>
        </Link>

        {activeTicker && (
          <div className="flex items-center gap-3 pl-6 border-l border-white/5">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">Active Session</span>
            <div className="px-3 py-1 bg-blue-600/10 border border-blue-500/20 rounded-md flex items-center gap-2">
              <span className="text-blue-400 font-bold text-sm tracking-widest">{activeTicker}</span>
              <button 
                onClick={() => setIsDeleteDialogOpen(true)}
                className="p-1 hover:bg-red-500/10 rounded text-gray-500 hover:text-red-400 transition-colors"
                title="Delete all data for this company"
              >
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        )}

        <nav className="flex items-center gap-1 ml-4 bg-white/5 p-1 rounded-xl border border-white/5">
           <Link 
            href={activeTicker ? `/workspace/${activeTicker}` : '/'}
            className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${!pathname.includes('portfolio') ? 'bg-white/10 text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'}`}
           >
             Analysis
           </Link>
           <Link 
            href="/portfolio"
            className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${pathname.includes('portfolio') ? 'bg-white/10 text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'}`}
           >
             Portfolio
           </Link>
        </nav>
      </div>

      <div className="relative">
        <button 
          onClick={() => setIsHistoryOpen(!isHistoryOpen)}
          className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all duration-300 ${isHistoryOpen ? 'bg-white/5 border-white/20' : 'border-white/5 hover:border-white/20'}`}
        >
          <History size={16} className="text-gray-400" />
          <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">History</span>
          <ChevronDown size={14} className={`text-gray-500 transition-transform duration-300 ${isHistoryOpen ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {isHistoryOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute top-full mt-4 right-0 w-80 bg-[#161616] border border-[#2A2A2A] rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden"
            >
              <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">Notebook Compendium</span>
                <Clock size={12} className="text-gray-600" />
              </div>
              
              <div className="max-h-[400px] overflow-y-auto p-2 scrollbar-hide">
                {history.length > 0 ? (
                  history.map((item) => (
                    <button
                      key={item.ticker}
                      onClick={() => {
                        setIsHistoryOpen(false);
                        router.push(`/workspace/${item.ticker}`);
                      }}
                      className={`w-full flex items-center justify-between p-3 rounded-xl transition-all group ${activeTicker === item.ticker ? 'bg-blue-600/10 border border-blue-500/20' : 'hover:bg-white/5 border border-transparent'}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${activeTicker === item.ticker ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-gray-500'}`}>
                          <Database size={14} />
                        </div>
                        <div className="text-left">
                          <div className="text-sm font-bold text-white tracking-widest">{item.ticker}</div>
                          <div className="text-[10px] text-gray-500 truncate w-40">{item.name}</div>
                        </div>
                      </div>
                      <ArrowRight size={14} className={`transition-all ${activeTicker === item.ticker ? 'text-blue-400 opacity-100' : 'text-gray-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-1'}`} />
                    </button>
                  ))
                ) : (
                  <div className="py-12 text-center">
                    <History size={32} className="mx-auto text-gray-700 mb-3 opacity-20" />
                    <p className="text-xs text-gray-600 font-medium">No previous sessions found.</p>
                  </div>
                )}
              </div>
              
              <div className="p-3 bg-[#1A1A1A] border-t border-white/5 flex justify-center">
                <button className="text-[10px] text-blue-500/60 font-bold uppercase tracking-widest hover:text-blue-400 transition-colors flex items-center gap-2">
                  <ExternalLink size={10} />
                  Access Full Archives
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {isDeleteDialogOpen && (
          <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => !isDeleting && setIsDeleteDialogOpen(false)}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-[#161616] border border-red-500/20 rounded-2xl shadow-[0_0_50px_rgba(239,68,68,0.1)] overflow-hidden"
            >
              <div className="p-6 text-center">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4 text-red-500">
                  <AlertTriangle size={32} />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-2">Confirm Deletion</h3>
                <p className="text-sm text-gray-400 mb-6 leading-relaxed">
                  You are about to <span className="text-red-400 font-bold">permanently delete</span> all research data, vectorized filings, and notebook entries for <span className="text-white font-mono">{activeTicker}</span>. This action cannot be undone.
                </p>
                
                <div className="flex gap-3">
                  <button
                    disabled={isDeleting}
                    onClick={() => setIsDeleteDialogOpen(false)}
                    className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl text-xs font-bold text-gray-400 hover:text-white transition-all uppercase tracking-widest"
                  >
                    Cancel
                  </button>
                  <button
                    disabled={isDeleting}
                    onClick={handleDelete}
                    className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-500 rounded-xl text-xs font-bold text-white transition-all uppercase tracking-widest shadow-[0_0_20px_rgba(220,38,38,0.3)] flex items-center justify-center gap-2"
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Deleting…
                      </>
                    ) : (
                      'Delete Everything'
                    )}
                  </button>
                </div>
              </div>

              <button 
                onClick={() => setIsDeleteDialogOpen(false)}
                className="absolute top-4 right-4 p-2 text-gray-600 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </header>
  );
}
