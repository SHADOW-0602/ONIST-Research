import React from 'react';

type ChangeStatus = 'new' | 'updated' | 'deprecated' | 'unchanged';

interface DiffEntry {
  id: string;
  dimension: string;
  claim: string;
  status: ChangeStatus;
  previousValue?: string;
  newValue?: string;
  source: string;
}

const mockDiffs: DiffEntry[] = [
  {
    id: '1',
    dimension: 'Business Strategy',
    claim: 'Two new risk factors identified following Q3 earnings commentary.',
    status: 'new',
    source: 'Q3 Earnings Transcript'
  },
  {
    id: '2',
    dimension: 'Business Segments',
    claim: 'Cloud Services revenue guidance revised downwards.',
    status: 'updated',
    previousValue: '$4.2B',
    newValue: '$3.9B',
    source: '8-K Filing (Oct 12)'
  },
  {
    id: '3',
    dimension: 'Management Bio',
    claim: 'CFO departure confirmed — previous compensation entry no longer valid.',
    status: 'deprecated',
    source: 'Press Release'
  }
];

export default function NotebookDiff() {
  return (
    <div className="glass-panel p-6 mb-8">
      <div className="flex items-center justify-between mb-6 border-b border-[var(--color-glass-border)] pb-4">
        <div>
          <h2 className="text-xl font-semibold text-white tracking-tight">What Changed</h2>
          <p className="text-sm text-gray-400 mt-1">Delta since last Notebook version (Oct 12, 2026)</p>
        </div>
        <div className="flex gap-3 text-sm font-medium">
          <span className="px-3 py-1 rounded-full badge-new">1 New</span>
          <span className="px-3 py-1 rounded-full badge-updated">1 Updated</span>
          <span className="px-3 py-1 rounded-full badge-deprecated">1 Deprecated</span>
        </div>
      </div>

      <div className="space-y-4">
        {mockDiffs.map((entry) => (
          <div key={entry.id} className="glass-card p-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-gray-400 tracking-wider uppercase">{entry.dimension}</span>
                {entry.status === 'new' && <span className="text-[10px] uppercase px-2 py-0.5 rounded badge-new">New</span>}
                {entry.status === 'updated' && <span className="text-[10px] uppercase px-2 py-0.5 rounded badge-updated">Updated</span>}
                {entry.status === 'deprecated' && <span className="text-[10px] uppercase px-2 py-0.5 rounded badge-deprecated">Removed</span>}
              </div>
              <p className="text-sm text-gray-200 leading-relaxed">{entry.claim}</p>
              
              {entry.status === 'updated' && (
                <div className="mt-3 flex items-center gap-3 text-sm font-mono bg-black/30 p-2 rounded border border-white/5 inline-flex">
                  <span className="text-gray-500 line-through">{entry.previousValue}</span>
                  <span className="text-gray-600">→</span>
                  <span className="text-blue-400 font-bold">{entry.newValue}</span>
                </div>
              )}
            </div>
            <div className="text-xs text-gray-500 flex items-center gap-1 bg-black/20 px-2 py-1 rounded border border-white/5 whitespace-nowrap">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
              {entry.source}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
