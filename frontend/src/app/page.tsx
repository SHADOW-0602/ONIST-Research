"use client";

import { TickerSearch } from "@/components/landing/TickerSearch";
import { Header } from "@/components/common/Header";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="min-h-screen w-full flex flex-col bg-[#050505]">
      <Header />
      <main className="flex-1 w-full relative overflow-y-auto scrollbar-hide selection:bg-blue-500/30 flex flex-col items-center pt-32 px-4">
      {/* Background Elements (Fixed) */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <motion.div 
          animate={{
            x: [0, 100, 0],
            y: [0, 50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px]"
        />
        
        <motion.div 
          animate={{
            x: [0, -80, 0],
            y: [0, -100, 0],
            scale: [1.2, 1, 1.2],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-emerald-600/10 rounded-full blur-[120px]"
        />

        <motion.div 
          animate={{
            opacity: [0.1, 0.3, 0.1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]"
        />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] mix-blend-overlay"></div>
      </div>

      <div className="relative z-10 w-full max-w-4xl text-center">
        {/* Hero Section */}
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="flex flex-col items-center mb-16"
        >
          <motion.div 
            whileHover={{ scale: 1.05, rotate: 5 }}
            className="w-16 h-16 bg-gradient-to-br from-blue-600 to-emerald-600 rounded-2xl flex items-center justify-center shadow-[0_0_50px_rgba(37,99,235,0.4)] mb-8 cursor-pointer"
          >
            <span className="text-white font-black text-2xl tracking-tighter">ON</span>
          </motion.div>
          
          <h1 className="text-6xl md:text-8xl font-bold text-white tracking-tight mb-6">
            Research <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-blue-400 to-emerald-400">Intelligence.</span>
          </h1>
          
          <p className="text-gray-400 text-xl md:text-2xl font-medium tracking-wide max-w-3xl mx-auto leading-relaxed opacity-80">
            Autonomous multi-agent synthesis for institutional-grade <br className="hidden md:block" /> fundamental due diligence.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="mb-32"
        >
          <TickerSearch />
        </motion.div>

        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-48">
          <motion.div 
            whileHover={{ y: -5 }}
            className="bg-white/[0.02] border border-white/5 p-8 rounded-3xl backdrop-blur-sm"
          >
            <div className="text-blue-500 font-black text-4xl mb-2">9+</div>
            <div className="text-[10px] uppercase font-black tracking-[0.3em] text-gray-500">Research Agents</div>
          </motion.div>
          
          <motion.div 
            whileHover={{ y: -5 }}
            className="bg-white/[0.02] border border-white/5 p-8 rounded-3xl backdrop-blur-sm"
          >
            <div className="text-emerald-500 font-black text-4xl mb-2">99%</div>
            <div className="text-[10px] uppercase font-black tracking-[0.3em] text-gray-500">Source Verifiable</div>
          </motion.div>

          <motion.div 
            whileHover={{ y: -5 }}
            className="bg-white/[0.02] border border-white/5 p-8 rounded-3xl backdrop-blur-sm"
          >
            <div className="text-blue-500 font-black text-4xl mb-2">&lt; 3m</div>
            <div className="text-[10px] uppercase font-black tracking-[0.3em] text-gray-500">Full Synthesis</div>
          </motion.div>
        </div>

        {/* Value Proposition Section */}
        <div className="text-left mb-40">
           <h2 className="text-4xl font-bold text-white mb-12 tracking-tight">The Multi-Agent <br/><span className="text-blue-500">Advantage.</span></h2>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              <div className="space-y-4">
                 <h3 className="text-xl font-bold text-white tracking-wide">Autonomous Dimension Mapping</h3>
                 <p className="text-gray-500 leading-relaxed">Specialist agents analyze Management, Financials, and Strategy in parallel, ensuring no critical data point is missed during the ingestion phase.</p>
              </div>
              <div className="space-y-4">
                 <h3 className="text-xl font-bold text-white tracking-wide">Multi-Gate Verification</h3>
                 <p className="text-gray-500 leading-relaxed">Every claim is cross-referenced against primary SEC filings and news sources with a mandatory 4-tier verification status label.</p>
              </div>
              <div className="space-y-4">
                 <h3 className="text-xl font-bold text-white tracking-wide">Materiality Gating</h3>
                 <p className="text-gray-500 leading-relaxed">Intelligent filters suppress noise and immaterial commentary, focusing the final FDD report strictly on decision-ready investment signals.</p>
              </div>
              <div className="space-y-4">
                 <h3 className="text-xl font-bold text-white tracking-wide">Adversarial Bull/Bear Debate</h3>
                 <p className="text-gray-400 font-medium">Internal debate nodes stress-test every thesis, presenting analysts with the strongest counter-arguments for robust risk assessment.</p>
              </div>
           </div>
        </div>
      </div>

      {/* Final Call to Action */}
      <motion.div 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        className="relative z-10 mb-24 text-center"
      >
        <button 
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="group flex flex-col items-center gap-4 mx-auto"
        >
          <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center group-hover:border-blue-500/50 transition-colors">
            <motion.div 
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-gray-500 group-hover:text-blue-500"
            >
              ↑
            </motion.div>
          </div>
          <span className="text-[10px] font-bold text-gray-600 tracking-[0.3em] uppercase">Return to Search</span>
        </button>
      </motion.div>

      {/* Professional Footer Section */}
      <footer className="relative z-10 w-full bg-[#080808] border-t border-white/5 pt-20 pb-12 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
          <div className="col-span-1 md:col-span-2">
             <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-emerald-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-black text-xs">ON</span>
                </div>
                <span className="text-white font-bold tracking-tight text-xl">ONIST Intelligence.</span>
             </div>
             <p className="text-gray-500 max-w-sm leading-relaxed text-sm">
                The next generation of institutional equity research. Autonomous, verifiable, and decision-ready.
             </p>
          </div>
          
          <div>
             <h4 className="text-white font-bold text-xs uppercase tracking-[0.2em] mb-6">Infrastructure</h4>
             <ul className="space-y-3 text-sm text-gray-500">
                <li className="hover:text-blue-400 transition-colors cursor-default">Gemini 2.0 Flash</li>
                <li className="hover:text-blue-400 transition-colors cursor-default">LangGraph Orchestration</li>
                <li className="hover:text-blue-400 transition-colors cursor-default">CockroachDB · Qdrant</li>
             </ul>
          </div>

          <div>
             <h4 className="text-white font-bold text-xs uppercase tracking-[0.2em] mb-6">Platform</h4>
             <ul className="space-y-3 text-sm text-gray-500">
                <li className="hover:text-emerald-400 transition-colors cursor-default">Notebook HITL</li>
                <li className="hover:text-emerald-400 transition-colors cursor-default">FDD Synthesis</li>
                <li className="hover:text-emerald-400 transition-colors cursor-default">Security & Audit</li>
             </ul>
          </div>
        </div>

        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center pt-8 border-t border-white/5 gap-6">
           <div className="text-[10px] text-gray-600 font-bold tracking-[0.2em] uppercase">
              © 2026 ONIST RESEARCH GROUP. ALL RIGHTS RESERVED.
           </div>
           
           <div className="flex items-center gap-6">
              <div className="px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/5 flex items-center gap-3 text-[9px] text-gray-500 font-bold tracking-[0.2em]">
                 <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                 SYSTEM STATUS: NOMINAL
              </div>
           </div>
        </div>
      </footer>
    </main>
    </div>
  );
}
