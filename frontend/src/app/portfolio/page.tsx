"use client";

import { Header } from "@/components/common/Header";
import { PortfolioDashboard } from "@/components/workspace/PortfolioDashboard";

export default function PortfolioPage() {
  return (
    <div className="h-screen w-full bg-[#111111] text-[#EAEAEA] font-sans flex flex-col overflow-hidden">
      <Header />
      <div className="flex-1 overflow-hidden">
        <PortfolioDashboard />
      </div>
    </div>
  );
}
