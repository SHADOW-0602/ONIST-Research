import React, { forwardRef } from 'react';

interface Props {
  fddDraft: any;
}

export const FDDReportTemplate = forwardRef<HTMLDivElement, Props>(({ fddDraft }, ref) => {
  if (!fddDraft) return null;

  const renderSectionContent = (content: any) => {
    if (!content) return null;
    if (typeof content === 'string') return content;
    
    // If it's a structured object (like the Investment Thesis)
    return (
      <div className="space-y-4">
        {content.preamble && <p>{typeof content.preamble === 'string' ? content.preamble : JSON.stringify(content.preamble)}</p>}
        {content.bull_case && (
          <div>
            <h4 className="font-bold text-emerald-700">Bull Case</h4>
            <p>{typeof content.bull_case === 'string' ? content.bull_case : JSON.stringify(content.bull_case)}</p>
          </div>
        )}
        {content.bear_case && (
          <div>
            <h4 className="font-bold text-red-700">Bear Case</h4>
            <p>{typeof content.bear_case === 'string' ? content.bear_case : JSON.stringify(content.bear_case)}</p>
          </div>
        )}
        {content.key_debate_points && (
          <div>
            <h4 className="font-bold">Key Debate Points</h4>
            <p>{typeof content.key_debate_points === 'string' ? content.key_debate_points : JSON.stringify(content.key_debate_points)}</p>
          </div>
        )}
        
        {/* Fallback for other object types */}
        {!content.preamble && !content.bull_case && (
          <pre className="text-xs overflow-x-auto p-2 bg-gray-50 rounded">
            {JSON.stringify(content, null, 2)}
          </pre>
        )}
      </div>
    );
  };

  return (
    <div ref={ref} className="p-12 max-w-4xl mx-auto bg-white text-black font-serif print-container">
      {/* Cover Page */}
      <div className="flex flex-col h-[90vh] justify-center items-center text-center break-after-page">
        <h1 className="text-4xl font-bold mb-4 uppercase tracking-wider">{fddDraft.title || "Fundamental Due Diligence"}</h1>
        <h2 className="text-2xl font-medium text-gray-700 mb-8">{fddDraft.ticker}</h2>
        <div className="w-16 h-1 bg-gray-900 mx-auto mb-8" />
        <p className="text-lg font-semibold uppercase tracking-widest text-gray-500 mb-2">ONIST Institutional Research</p>
        <p className="text-md text-gray-400">Generated: {fddDraft.run_date || new Date().toISOString().split('T')[0]}</p>
        <p className="text-md text-gray-400">Status: {fddDraft.status}</p>
      </div>

      {/* Disclaimer Page */}
      <div className="break-after-page mt-12">
        <h3 className="text-xl font-bold mb-6 border-b border-gray-300 pb-2">Disclaimer & Methodology</h3>
        <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap font-sans">
          {fddDraft.disclaimer}
        </p>
      </div>

      {/* Executive Summary */}
      {fddDraft.executive_summary && (
        <div className="break-after-page mt-12">
          <h3 className="text-2xl font-bold mb-6 border-b border-gray-300 pb-2 uppercase">Executive Summary</h3>
          <div className="text-md leading-relaxed text-gray-800">
            {renderSectionContent(fddDraft.executive_summary.content || fddDraft.executive_summary)}
          </div>
        </div>
      )}

      {/* Dynamic Sections */}
      {fddDraft.sections && Object.entries(fddDraft.sections).map(([key, section]: [string, any], index) => {
        if (!section) return null;
        return (
          <div key={key} className="mb-12 break-inside-avoid">
            <h3 className="text-xl font-bold mb-4 border-b border-gray-200 pb-1 capitalize">
              {section.title || key.replace(/_/g, ' ')}
            </h3>
            <div className="text-md leading-relaxed text-gray-800 whitespace-pre-wrap">
              {renderSectionContent(section.content || section)}
            </div>
          </div>
        );
      })}
    </div>
  );
});

FDDReportTemplate.displayName = "FDDReportTemplate";
