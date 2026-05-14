import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

export interface ReviewItem {
  dimension: string;
  issue: string;
  status: 'PENDING' | 'RESOLVED' | 'DISMISSED';
}

export function usePipeline() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('Idle');
  const [graphState, setGraphState] = useState<any>(null);
  const [diff, setDiff] = useState<any>(null);
  const [publishedReport, setPublishedReport] = useState<any>(null);
  const [notebookEntries, setNotebookEntries] = useState<Record<string, any[]>>({});
  // Analyst review items — sourced from top-level graphState.analyst_review_items
  const [analystReviewItems, setAnalystReviewItems] = useState<ReviewItem[]>([]);

  // Poll backend for state updates
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (taskId && status !== 'Completed' && !status.startsWith('Error')) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/research/state/${taskId}`);
          if (res.ok) {
            const data = await res.json();
            setStatus(data.status);
            setGraphState(data.graph_state);

            // Sync analyst_review_items from top-level graph state
            if (data.graph_state?.analyst_review_items) {
              // Only overwrite if backend has items (preserve local resolve/dismiss state)
              const backendItems: ReviewItem[] = data.graph_state.analyst_review_items;
              setAnalystReviewItems((prev) => {
                // Merge: keep local status overrides, add any new items from backend
                const prevMap = new Map(prev.map((p, i) => [`${p.dimension}:${p.issue}`, p]));
                return backendItems.map((item) => {
                  const key = `${item.dimension}:${item.issue}`;
                  return prevMap.get(key) || { ...item, status: item.status ?? 'PENDING' };
                });
              });
            }

            // Once we have a ticker, fetch the published version if not already fetched
            if (data.graph_state?.ticker && !publishedReport) {
              const historyRes = await fetch(`${API_BASE}/fdd/history/${data.graph_state.ticker}`);
              if (historyRes.ok) {
                const history = await historyRes.json();
                const latest = history.reports.find((r: any) => r.status === 'PUBLISHED');
                if (latest) setPublishedReport(latest);
              }

              // Fetch historical notebook entries
              const notebookRes = await fetch(`${API_BASE}/notebook/entries/${data.graph_state.ticker}`);
              if (notebookRes.ok) {
                const notebookData = await notebookRes.json();
                setNotebookEntries(notebookData.entries);
              }
            }
          } else if (res.status === 404) {
            // Task lost (likely backend restart)
            setStatus('Error: Research session expired. Please re-run the pipeline.');
            setTaskId(null);
          }
        } catch (error) {
          console.error('Failed to poll pipeline status', error);
        }
      }, 2000);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [taskId, status, publishedReport]);

  // ── Pipeline control ────────────────────────────────────────────────────────
  const startPipeline = useCallback(async (ticker: string, context: string, forceRefresh: boolean = false) => {
    try {
      setStatus('Triggering Pipeline...');
      const res = await fetch(`${API_BASE}/research/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, company_context: context, force_refresh: forceRefresh }),
      });
      const data = await res.json();
      
      if (data.task_id === 'completed-existing-report') {
        setStatus('Completed');
        setTaskId('completed'); // special flag
        // Force state update by setting ticker in a mock graphState
        setGraphState({ ticker });
        return;
      }
      
      setTaskId(data.task_id);
    } catch (error) {
      console.error(error);
      setStatus('Error: Failed to start');
    }
  }, []);

  const approveSynthesis = useCallback(async (approve: boolean = true, feedback?: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/research/approve/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approve, feedback }),
    });
  }, [taskId]);

  const injectGuidance = useCallback(async (text: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/research/inject/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'guidance', payload: text }),
    });
  }, [taskId]);

  const directEdit = useCallback(async (claim: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/research/inject/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'direct_edit', payload: claim }),
    });
  }, [taskId]);

  // A5 — Refresh trigger
  const triggerRefresh = useCallback(async (dimension?: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/research/refresh/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dimension: dimension || null }),
    });
  }, [taskId]);

  // A6 — Fetch diff
  const fetchDiff = useCallback(async () => {
    if (!taskId) return;
    try {
      const res = await fetch(`${API_BASE}/research/diff/${taskId}`);
      if (res.ok) {
        const data = await res.json();
        setDiff(data.diff);
      }
    } catch (error) {
      console.error('Failed to fetch diff', error);
    }
  }, [taskId]);

  // ── Part A Notebook HITL Actions ───────────────────────────────────────────

  // A1 — Claim-level annotation
  const annotateClaim = useCallback(async (entryId: string, annotationType: string, text: string) => {
    await fetch(`${API_BASE}/notebook/annotate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry_id: entryId, analyst_id: 'analyst_1', annotation_type: annotationType, text }),
    });
  }, []);

  // A2 — Confidence override
  const overrideClaim = useCallback(async (entryId: string, confidence: string) => {
    await fetch(`${API_BASE}/notebook/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry_id: entryId, analyst_id: 'analyst_1', confidence }),
    });
  }, []);

  // A3 — Claim suppression
  const suppressClaim = useCallback(async (entryId: string, reason: string) => {
    await fetch(`${API_BASE}/notebook/suppress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry_id: entryId, analyst_id: 'analyst_1', reason }),
    });
  }, []);

  // A4 — Manual injection (structured)
  const injectClaim = useCallback(async (ticker: string, dimension: string, fieldPath: string, claimText: string, source?: string) => {
    await fetch(`${API_BASE}/notebook/inject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analyst_id: 'analyst_1',
        ticker,
        dimension,
        field_path: fieldPath,
        claim_text: claimText,
        source: source || 'analyst_injection',
      }),
    });
  }, []);

  // ── Part B FDD Report HITL Actions ─────────────────────────────────────────

  // B1 — Section-level editing
  const editFDDSection = useCallback(async (sectionId: string, newContent: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/fdd/edit_section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, section_id: sectionId, new_content: newContent }),
    });
  }, [taskId]);

  // B2 — Bull/Bear adjudication
  const adjudicateThesis = useCallback(async (action: 'accept_bull' | 'accept_bear' | 'neutral') => {
    if (!taskId) return;
    await fetch(`${API_BASE}/fdd/adjudicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, action }),
    });
  }, [taskId]);

  // B4 — Selective regeneration
  const regenerateFDDSection = useCallback(async (sectionId: string, feedback: string) => {
    if (!taskId) return;
    await fetch(`${API_BASE}/fdd/regenerate_section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, section_id: sectionId, feedback }),
    });
  }, [taskId]);

  // B5 — Publication control
  const publishFDD = useCallback(async () => {
    if (!taskId) return;
    const res = await fetch(`${API_BASE}/fdd/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, analyst_id: 'analyst_1' }),
    });
    if (res.ok) {
      const data = await res.json();
      return data.report_id;
    }
    return null;
  }, [taskId]);

  const schedulePublication = useCallback(async (reportId: string, timestamp: string) => {
    await fetch(`${API_BASE}/fdd/schedule`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_id: reportId, scheduled_at: timestamp }),
    });
  }, []);

  const retractReport = useCallback(async (reportId: string) => {
    await fetch(`${API_BASE}/fdd/retract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_id: reportId }),
    });
  }, []);

  // B6 — Fetch FDD History
  const fetchFDDHistory = useCallback(async (ticker: string) => {
    const res = await fetch(`${API_BASE}/fdd/history/${ticker}`);
    if (res.ok) {
      const data = await res.json();
      return data.reports;
    }
    return [];
  }, []);

  // Fetch Notebook Entries
  const fetchNotebookEntries = useCallback(async (ticker: string) => {
    const res = await fetch(`${API_BASE}/notebook/entries/${ticker}`);
    if (res.ok) {
      const data = await res.json();
      setNotebookEntries(data.entries);
      return data.entries;
    }
    return {};
  }, []);

  // ── Analyst Review Item Actions (optimistic UI) ───────────────────────────

  const resolveReviewItem = useCallback((index: number) => {
    setAnalystReviewItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, status: 'RESOLVED' as const } : item))
    );
  }, []);

  const dismissReviewItem = useCallback((index: number) => {
    setAnalystReviewItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, status: 'DISMISSED' as const } : item))
    );
  }, []);

  const clearResolvedItems = useCallback(() => {
    setAnalystReviewItems((prev) => prev.filter((item) => item.status === 'PENDING'));
  }, []);
  
  // Layer 6 — Prompt Optimization
  const optimizePrompts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/prompts/optimize`, { method: 'POST' });
      return res.ok;
    } catch (error) {
      console.error('Failed to trigger prompt optimization', error);
      return false;
    }
  }, []);

  // ── Search Actions ─────────────────────────────────────────────────────────
  const searchTickers = useCallback(async (query: string) => {
    if (!query || query.length < 1) return [];
    try {
      const res = await fetch(`${API_BASE}/tickers/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        return data.results;
      }
    } catch (error) {
      console.error('Failed to search tickers', error);
    }
    return [];
  }, []);

  return {
    taskId,
    status,
    graphState,
    diff,
    notebookEntries,
    publishedReport,
    analystReviewItems,
    startPipeline,
    searchTickers,
    approveSynthesis,
    injectGuidance,
    directEdit,
    triggerRefresh,
    fetchDiff,
    annotateClaim,
    overrideClaim,
    suppressClaim,
    injectClaim,
    editFDDSection,
    adjudicateThesis,
    regenerateFDDSection,
    publishFDD,
    schedulePublication,
    retractReport,
    fetchFDDHistory,
    fetchNotebookEntries,
    resolveReviewItem,
    dismissReviewItem,
    clearResolvedItems,
    optimizePrompts,
  };
}

