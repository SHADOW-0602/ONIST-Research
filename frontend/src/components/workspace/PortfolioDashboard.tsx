"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, BarChart3, Clock, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";

interface PortfolioSignal {
  signal_id: string;
  ticker: string;
  action: string;
  sentiment: string;
  confidence: string;
  sizing: string;
  entry_price: number;
  current_price: number;
  roi: number;
  stop_loss: string;
  risk_reward: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export function PortfolioDashboard() {
  const [signals, setSignals] = useState<PortfolioSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/portfolio/signals");
      if (res.ok) {
        const data = await res.json();
        setSignals(data.signals);
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.error("Failed to fetch portfolio signals", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    // Refresh every 5 minutes
    const interval = setInterval(fetchSignals, 300000);
    return () => clearInterval(interval);
  }, []);

  const avgRoi = signals.length > 0 
    ? signals.reduce((acc, s) => acc + s.roi, 0) / signals.length 
    : 0;
    
  const successRate = signals.length > 0
    ? (signals.filter(s => s.roi > 0).length / signals.length) * 100
    : 0;

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[#111111] scrollbar-hide">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header Section */}
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-black text-white tracking-tight mb-2">Institutional Portfolio</h1>
            <p className="text-gray-500 font-medium tracking-wide flex items-center gap-2">
              <Activity size={14} className="text-blue-500" />
              Live performance tracking of AI-generated research signals
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {lastUpdated && (
              <div className="text-right">
                <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Last Synced</div>
                <div className="text-xs text-gray-300 font-mono">{lastUpdated.toLocaleTimeString()}</div>
              </div>
            )}
            <button 
              onClick={fetchSignals}
              disabled={loading}
              className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all group"
            >
              <RefreshCw size={18} className={`text-gray-400 group-hover:text-white transition-all ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Hero Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard 
            title="Total Signals" 
            value={signals.length.toString()} 
            icon={<Target className="text-blue-400" />}
            color="blue"
          />
          <StatCard 
            title="Average ROI" 
            value={`${avgRoi.toFixed(2)}%`} 
            icon={avgRoi >= 0 ? <TrendingUp className="text-emerald-400" /> : <TrendingDown className="text-red-400" />}
            color={avgRoi >= 0 ? "emerald" : "red"}
            subtitle="Portfolio-wide return"
          />
          <StatCard 
            title="Success Rate" 
            value={`${successRate.toFixed(1)}%`} 
            icon={<BarChart3 className="text-amber-400" />}
            color="amber"
            subtitle="Signals in profit"
          />
          <StatCard 
            title="Active Positions" 
            value={signals.filter(s => s.status === 'ACTIVE').length.toString()} 
            icon={<DollarSign className="text-purple-400" />}
            color="purple"
          />
        </div>

        {/* Signals Table */}
        <div className="bg-[#161616] border border-[#2A2A2A] rounded-3xl overflow-hidden shadow-2xl">
          <div className="px-8 py-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
            <span className="text-sm font-bold text-white uppercase tracking-widest">Performance Ledger</span>
            <div className="flex gap-2">
              <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 uppercase tracking-widest">Live Execution</div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Ticker</th>
                  <th className="px-6 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Action</th>
                  <th className="px-6 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Entry / Current</th>
                  <th className="px-6 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Conviction</th>
                  <th className="px-6 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">ROI</th>
                  <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {signals.map((signal, idx) => (
                  <motion.tr 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    key={signal.signal_id} 
                    className="hover:bg-white/[0.02] transition-colors group"
                  >
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center font-bold text-blue-400 tracking-tighter group-hover:bg-blue-600 group-hover:text-white transition-all">
                          {signal.ticker}
                        </div>
                        <div>
                          <div className="text-sm font-bold text-white tracking-widest">{signal.ticker}</div>
                          <div className="text-[10px] text-gray-500 font-mono">
                            {new Date(signal.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-6">
                      <span className={`px-3 py-1 rounded-lg text-[10px] font-black tracking-widest uppercase ${
                        signal.action === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
                        signal.action === 'SELL' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                        'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                      }`}>
                        {signal.action}
                      </span>
                    </td>
                    <td className="px-6 py-6 font-mono">
                      <div className="text-sm text-gray-300">${signal.entry_price.toFixed(2)}</div>
                      <div className="text-[10px] text-gray-500">→ ${signal.current_price.toFixed(2)}</div>
                    </td>
                    <td className="px-6 py-6">
                      <div className="flex flex-col gap-1">
                        <div className="text-xs font-bold text-white tracking-wide">{signal.sentiment}</div>
                        <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" 
                            style={{ width: signal.confidence }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-6">
                      <div className={`flex items-center gap-1 text-sm font-black tracking-tight ${signal.roi >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {signal.roi >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                        {signal.roi.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-8 py-6 text-right">
                      <span className={`text-[10px] font-bold uppercase tracking-[0.2em] ${signal.status === 'ACTIVE' ? 'text-blue-400 animate-pulse' : 'text-gray-600'}`}>
                        {signal.status}
                      </span>
                    </td>
                  </motion.tr>
                ))}
                {signals.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-8 py-20 text-center text-gray-500">
                      <BarChart3 size={48} className="mx-auto mb-4 opacity-10" />
                      <p className="text-sm font-medium">No signals recorded yet. Publish a research report to generate a signal.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color, subtitle }: { title: string, value: string, icon: React.ReactNode, color: string, subtitle?: string }) {
  const colorMap: any = {
    blue: "bg-blue-600/10 border-blue-500/20 text-blue-400 shadow-[0_0_30px_rgba(37,99,235,0.05)]",
    emerald: "bg-emerald-600/10 border-emerald-500/20 text-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.05)]",
    amber: "bg-amber-600/10 border-amber-500/20 text-amber-400 shadow-[0_0_30px_rgba(245,158,11,0.05)]",
    purple: "bg-purple-600/10 border-purple-500/20 text-purple-400 shadow-[0_0_30px_rgba(139,92,246,0.05)]",
    red: "bg-red-600/10 border-red-500/20 text-red-400 shadow-[0_0_30px_rgba(220,38,38,0.05)]"
  };

  return (
    <motion.div 
      whileHover={{ y: -5, scale: 1.02 }}
      className={`p-6 border rounded-3xl transition-all duration-300 ${colorMap[color]}`}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="p-3 bg-white/5 rounded-2xl">{icon}</div>
        <Clock size={12} className="text-gray-600" />
      </div>
      <div>
        <div className="text-[10px] font-black uppercase tracking-[0.2em] mb-1 opacity-60">{title}</div>
        <div className="text-3xl font-black tracking-tighter text-white">{value}</div>
        {subtitle && <div className="text-[10px] font-medium text-gray-500 mt-2 uppercase tracking-widest">{subtitle}</div>}
      </div>
    </motion.div>
  );
}
