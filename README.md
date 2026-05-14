<br># ONIST Research Intelligence Platform

> **Institutional-grade Fundamental Due Diligence (FDD) synthesis powered by a multi-agent AI pipeline with Human-in-the-Loop oversight.**

---

## Overview

ONIST is a production-ready research intelligence platform that automates the end-to-end workflow for fundamental equity due diligence. It ingests public company data across multiple sources, routes it through a multi-layer agent pipeline with built-in verification gates, and produces structured FDD reports with real-time analyst oversight.

The system is designed for institutional research teams who need:
- **Speed** — hours of research compressed into an automated pipeline (now with **high-speed local document parsing**)

- **Auditability** — every claim is source-tagged and verification-status-labeled
- **Interactive Sources** — review raw source text directly within the workspace
- **Control** — analysts retain full editorial authority via the HITL workspace
- **Performance Tracking** — live ROI monitoring of institutional trading signals (**New: Layer 7**)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ONIST Research Intelligence Platform                  │
├──────────────────────────────┬──────────────────────────────────────────────┤
│       BACKEND (FastAPI)      │         FRONTEND (Next.js)                   │
│                              │                                              │
│  Layer 0 — Data Ingestion    │  Left Pane   — Source Library               │
│   • Polygon.io (pricing)     │   • Interactive Source Preview Modals       │
│   • EDGAR (SEC filings)      │  Center Pane — Research Canvas (Notebook)   │
│   • Local SEC Parser (High   │  Right Pane  — HITL Review Hub              │
│     Speed Regex)             │                                              │
│   • RAG Pipeline (LlamaIndex │  Components                                 │
│     + Qdrant)                │   • SourceViewModal                         │
│   • 1024-token Optimized     │   • HITLRegenerateModal                     │
│                              │   • HITLApprovalModal                       │
│  Layer 1 — Primary Agents    │   • FDDReportTemplate (PDF Export)          │
│   • Gemini 2.0 Flash         │                                              │
│   • 7 Research Dimensions    │  Data Flow                                  │
│                              │   usePipeline() hook polls /api/v1/research │
│  Layer 2 — Specialist Agents │   /state/:taskId every 2s for live state    │
│   • NVIDIA NIM (Llama 3.1)   │                                              │
│   • Dossier + Footprint      │                                              │
│                              │                                              │
│  Layer 3 — Verification      │                                              │
│   • Gate 1: Hallucination    │                                              │
│   • Gate 2: Source Audit     │                                              │
│   • Gate 3: Staleness Check  │                                              │
│   (powered by Azure OpenAI)  │                                              │
│                              │                                              │
│  Layer 4 — Notebook & Filter │                                              │
│   • CockroachDB (PostgreSQL) │                                              │
│   • Materiality Filter       │                                              │
│   • Qdrant semantic index    │                                              │
│                              │                                              │
│  Layer 5 — Synthesis         │                                              │
│   • Mistral Large (FDD)      │                                              │
│   • Cohere (Bull/Bear Debate)│                                              │
│   • LangGraph HITL interrupt │                                              │
│                              │                                              │
│  Layer 6 — Self-Optimization │                                              │
│   • Shadow Prompting         │                                              │
│   • Automated Engineering    │                                              │
│   • Prompt Telemetry DB      │                                              │
│                              │                                              │
│  Layer 7 — Institutional Hub │                                              │
│   • Investment Committee     │                                              │
│   • Trading Signal Engine    │                                              │
│   • Portfolio Performance    │                                              │
│   • Live ROI Monitor (yf)    │                                              │
└──────────────────────────────┴──────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| API Server | FastAPI + Uvicorn |
| Orchestration | LangGraph (StateGraph + MemorySaver) |
| Primary Agents (L1) | Google Gemini 2.5 Flash via native `google-genai` SDK |
| Specialist Agents (L2) | NVIDIA NIM / Llama 3.1 405B via `langchain-nvidia-ai-endpoints` |
| Verification Gates (L3) | Azure OpenAI / gpt-4o-mini via `langchain-openai` |
| FDD Synthesis (L5) | Mistral Large via `langchain-mistralai` |
| Adversarial Debate (L5) | Cohere Command-R+ via `langchain-cohere` |
| RAG Vector Store | Qdrant Cloud via `llama-index-vector-stores-qdrant` |
| Document Parsing | Local LlamaIndex Readers (PyMuPDF, DocxReader, HTMLTagReader) |

| Serverless Database | CockroachDB (PostgreSQL) via `psycopg2` |
| Embeddings | Google Gemini Embedding (`text-embedding-004`) via native SDK |
| Prompt Optimizer (L6) | Gemini 2.0 Pro via native SDK |
| Portfolio Monitor (L7) | `yfinance` + `asyncio` background service |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| Icons | Lucide React |
| PDF Export | `react-to-print` |
| State/Polling | Custom `usePipeline` hook |

---

## Project Structure

```
ONIST-Research/
├── backend/
│   ├── main.py                    # FastAPI app entry point + CORS config
│   ├── api.py                     # REST endpoints: /start, /state, /inject, /approve
│   ├── config.py                  # Environment variable loader
│   ├── models.py                  # Pydantic data models
│   ├── agents/
│   │   ├── base.py                # Base Gemini agent (Layer 1)
│   │   ├── base_nim.py            # Base NVIDIA NIM agent (Layer 2)
│   │   ├── base_azure.py          # Base Azure OpenAI agent (Layer 3)
│   │   ├── base_cohere.py         # Base Cohere agent (Layer 5)
│   │   ├── base_mistral.py        # Base Mistral agent (Layer 5)
│   │   ├── identity.py            # Identity Normalization
│   │   ├── sector.py              # Sector Classification
│   │   ├── business_mechanics.py  # Revenue model & moat
│   │   ├── business_segments.py   # Segment financials
│   │   ├── business_strategy.py   # Strategic bets & risks
│   │   ├── management_comp.py     # Compensation analysis
│   │   ├── management_bios.py     # Executive biographies
│   │   ├── dossier.py             # Board composition & 13D/G (L2)
│   │   ├── footprint.py           # ESG, sentiment, litigation (L2)
│   │   ├── materiality_filter.py  # Filters claims for synthesis (L4)
│   │   ├── fdd_synthesis_agent.py # FDD section generation (L5)
│   │   └── report_debate.py       # Bull/Bear adversarial agents (L5)
│   ├── ingestion/
│   │   ├── rag_pipeline.py        # LlamaIndex + Qdrant RAG
│   │   ├── polygon_client.py      # Polygon.io price data
│   │   ├── edgar_client.py        # SEC EDGAR filing downloader
│   │   ├── finviz_client.py       # Finviz screener scraper
│   │   └── scraper.py             # Async web scraper (Crawl4AI)
│   ├── pipeline/
│   │   ├── orchestrator.py        # LangGraph StateGraph (Master Pipeline)
│   │   ├── notebook_client.py     # CockroachDB CRUD + semantic index
│   │   ├── verification.py        # Three-Gate verification pipeline
│   │   ├── notifications.py       # Alert dispatching
│   │   └── portfolio_monitor.py   # Background ROI tracking service
│   ├── synthesis/
│   │   ├── mistral_fdd.py         # Mistral FDD compiler
│   │   └── cohere_debate.py       # Cohere adversarial debate
│   └── pipeline/
│       ├── verification.py        # Centralized verification pipeline
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx           # App entry point
│   │   ├── components/workspace/
│   │   │   ├── WorkspaceLayout.tsx
│   │   │   ├── LeftPaneSourceLibrary.tsx
│   │   │   ├── CenterPaneResearchCanvas.tsx
│   │   │   ├── RightPaneReviewGate.tsx
│   │   │   ├── FDDReportTemplate.tsx  # PDF print template
│   │   │   ├── HITLRegenerateModal.tsx
│   │   │   ├── HITLDirectEditModal.tsx
│   │   │   ├── HITLApprovalModal.tsx
│   │   │   ├── VerificationHighlighter.tsx
│   │   │   └── TickerSparkline.tsx
│   │   └── hooks/
│   │       └── usePipeline.ts     # State polling + action dispatchers
├── requirements.txt               # Python backend dependencies
├── .env                           # API keys and service URLs (see below)
└── README.md
```

---

## Prerequisites

- Python **3.11+**
- Node.js **18+** and npm
- A [CockroachDB](https://www.cockroachlabs.com/) cluster (Serverless/Free tier works)
- A [Qdrant Cloud](https://qdrant.tech/) cluster (free tier works)

---

## Environment Setup

Copy the following into a `.env` file at the project root and fill in your keys:

```env
# LLM Providers
GOOGLE_API_KEY=           # Gemini 2.0 Flash (Layer 1 agents + embeddings)
AZURE_OPENAI_KEY=         # Azure OpenAI (Layer 3 verification gates)
AZURE_OPENAI_ENDPOINT=    # Azure OpenAI instance endpoint
AZURE_OPENAI_DEPLOYMENT=  # Deployment name (e.g., gpt-4o-mini)
COHERE_API_KEY=           # Cohere Command-R+ (Layer 5 adversarial debate)
MISTRAL_API_KEY=          # Mistral Large (Layer 5 FDD synthesis)
NVIDIA_API_KEY=           # NVIDIA NIM (Layer 2 specialist agents)

# Observability
LANGCHAIN_API_KEY=        # LangSmith tracing (optional but recommended)

# Vector Store
QDRANT_URL=               # Qdrant Cloud cluster URL
QDRANT_API_KEY=           # Qdrant API key


# Financial Data
POLYGON_API_KEY=          # Polygon.io (market data)
RAPIDAPI_KEY=             # RapidAPI (supplementary data sources)

# Production Database (CockroachDB / PostgreSQL)
DATABASE_URL=             # postgresql://user:pass@host:port/dbname?sslmode=require
```

---

## Installation

### 1. Backend

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install all Python dependencies
pip install -r requirements.txt

# Initialize the database schema
python scripts/init_db.py

# Start the FastAPI server
uvicorn backend.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Next.js dev server
npm run dev
```

The UI will be available at `http://localhost:3050`.

---

## API Reference

All endpoints are namespaced under `/api/v1/research/`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research/start` | Trigger a new pipeline run for a given ticker |
| `GET` | `/research/state/{task_id}` | Poll full LangGraph state and pipeline status |
| `POST` | `/research/inject/{task_id}` | Inject analyst guidance or a direct edit claim |
| `POST` | `/research/approve/{task_id}` | Resume pipeline past the HITL interrupt to Layer 5 |
| `POST` | `/prompts/optimize` | Trigger ML optimization of research prompts |
| `DELETE` | `/research/delete/{ticker}` | Cascading delete of ticker data (DB, Qdrant, FS) |

### Start a pipeline run

```json
POST /api/v1/research/start
{
  "ticker": "AAPL",
  "company_context": "Apple Inc. Global Technology"
}
```

Response:
```json
{ "message": "Pipeline triggered successfully", "task_id": "uuid-here" }
```

### Inject analyst guidance (before approving)

```json
POST /api/v1/research/inject/{task_id}
{
  "action": "guidance",
  "payload": "Focus more on TSMC supply chain risk in Q4 projections."
}
```

---

## The Pipeline Flow

```
Start ──► Identity ──► Layer 1 Agents (micro-batch A+B) ──► Layer 2 Specialists
                                                                     │
                                                        ┌────────────┘
                                                        ▼
                              Materiality Filter ◄── Notebook Write (DB)
                                    │
                                    ▼
               ┌──────────────────────────────────────┐
               │  LAYER 5 SYNTHESIS (runs in parallel) │
               │  • FDD Synthesis (Mistral Large)      │
               │  • Bull/Bear Debate (Cohere, 2-pass)  │
               └──────────────┬───────────────────────┘
                              ▼
                     Conflict Resolution
                              │
                              ▼
                        Compiler Node ──► analyst_review (HITL interrupt)
                                                   │
                              ┌────────────────────┤
                              ▼                    ▼
                         Approve &           Inject Guidance /
                         Publish ───┐        Direct Edit ──► re-synthesize
                                    │
                                    ▼
                         Layer 7: Institutional Committee
                                    │
                                    ▼
                         Trading Signal Generation
                                    │
                                    ▼
                         Portfolio Performance Tracking (Live ROI)
```

### Verification Gates (Layer 3)

Every agent output passes through three gates before entering the notebook:

| Gate | Model | Purpose |
|---|---|---|
| **Gate 1** Hallucination Detector | Azure OpenAI / gpt-4o-mini | Cross-references claims against RAG context; flags ungrounded statements. Auto-retries (max 2x). |
| **Gate 2** Source Auditor | Azure OpenAI / gpt-4o-mini | Validates source tier (Tier1=SEC, Tier2=News, Tier3=Unverified). Flags sourcing gaps. |
| **Gate 3** Staleness Reviewer | Azure OpenAI / gpt-4o-mini | Detects data points older than thresholds; queues stale fields for re-fetch. |

### Claim Audit Labels

All claims in generated reports carry one of these labels:

| Label | Meaning |
|---|---|
| *(no label)* | Fully verified — passed all three gates |
| `[Source note]` | Partially verified |
| `[Unverified]` | Not independently corroborated |
| `[Forward-looking]` | Management guidance or projection |
| `[Analyst override]` | Analyst-assessed on proprietary basis |
| `[Analyst injection]` | Analyst-sourced; not from public data |
| `[Deleted]` | Data purge signal processed |

---

## Human-in-the-Loop (HITL) Workflow

The pipeline pauses at the `analyst_review` node (via a LangGraph interrupt) before generating the final FDD report. The analyst can:

1. **Approve & Publish** — Resumes Layer 5 synthesis and marks the report as complete.
2. **Regenerate with Guidance** — Injects a custom prompt to steer Mistral's synthesis focus.
3. **Direct Edit / Inject** — Injects a claim with an `[Analyst injection]` audit tag directly into the notebook.

---

## Self-Optimizing Intelligence (Layer 6)

ONIST features a closed-loop learning system that allows the AI to improve its research reasoning based on your specific analyst preferences:

### Shadow Prompting
To ensure reliability, the system uses a **non-destructive shadow architecture**. Original prompts remain immutable in the `prompts/` directory, while optimized versions are stored in `prompts_optimized/`. The system always prioritizes the optimized version if it exists.

### The Optimization Cycle
1. **Telemetry Capture**: Every time you publish a report, the system calculates the "Delta" between the AI's draft and your final edits.
2. **Gap Analysis**: This delta is stored in the `prompt_telemetry` table.
3. **Automated Engineering**: Triggering the "Optimize Intelligence" button in the dashboard runs an ML pipeline that analyzes your edits to rewrite and refine the system's internal instructions.

### Optimized Components
The system currently optimizes:
- **Materiality Filtering** (Learning your threshold for "Important" news)
- **Thesis Adjudication** (Learning your bias for Bull/Bear evidence)
- **FDD Synthesis** (Learning your preferred tone and depth)

---

## PDF Export

Once the pipeline completes Layer 5, an **Export PDF** button appears in the workspace. Clicking it triggers the browser's native print engine against a hidden, print-optimized `FDDReportTemplate` component, producing a clean white-paper PDF with:
- Cover page (Company, Ticker, Date, Status)
- Full ONIST disclaimer
- Executive Summary
- All synthesized sections
- Bull/Bear investment thesis

---

## Development Notes

- The `usePipeline` React hook is the **single source of truth** for all frontend state. All new UI should consume it.
- All new database operations should go through `backend/pipeline/notebook_client.py`.
- The `task_id` (UUID) is used as LangGraph's `thread_id`, enabling multi-analyst, multi-session research streams.
- The `[Analyst injection]` audit tag is automatically appended to any claim injected via the HITL modal.

---

## License

MIT — see [LICENSE](./LICENSE).
