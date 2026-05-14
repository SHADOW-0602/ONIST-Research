import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import the compiled LangGraph app and Command object
from backend.pipeline.orchestrator import app as langgraph_app, GraphState
from backend.pipeline.notebook_client import notebook_client
import os
import shutil
import logging
from langgraph.types import Command

logger = logging.getLogger(__name__)

from backend.ingestion.rag_pipeline import rag_pipeline
from backend.pipeline.notifications import notification_system
from backend.pipeline.optimizer import PromptOptimizer

router = APIRouter()

class ResearchRequest(BaseModel):
    ticker: str
    company_context: str
    force_refresh: bool = False

class InjectRequest(BaseModel):
    action: str  # "guidance" or "direct_edit"
    payload: Any # Text string or JSON claim

# ─── Part A Notebook HITL Models ──────────────────────────────────────────────
class AnnotateRequest(BaseModel):
    entry_id: str
    analyst_id: str
    annotation_type: str  # "commentary", "nuance", "limitation"
    text: str

class ConfidenceOverrideRequest(BaseModel):
    entry_id: str
    analyst_id: str
    confidence: str  # "primary_confirmed" | "secondary_reported" | "agent_inferred" | "unverified"

class SuppressRequest(BaseModel):
    entry_id: str
    analyst_id: str
    reason: str

class NotebookInjectRequest(BaseModel):
    analyst_id: str
    ticker: str
    dimension: str
    field_path: str
    claim_text: str
    source: Optional[str] = "analyst_injection"

class RefreshRequest(BaseModel):
    dimension: Optional[str] = None  # None triggers a full company re-run

# ─── Part B FDD Report HITL Models ───────────────────────────────────────────
class FDDSectionEditRequest(BaseModel):
    task_id: str
    section_id: str
    new_content: str

class FDDAdjudicateRequest(BaseModel):
    task_id: str
    action: str  # "accept_bull", "accept_bear", "neutral"

class FDDRejectRequest(BaseModel):
    task_id: str
    feedback: str

class FDDPublishRequest(BaseModel):
    task_id: str
    analyst_id: str

class FDDRegenerateSectionRequest(BaseModel):
    task_id: str
    section_id: str
    feedback: str

class FDDScheduleRequest(BaseModel):
    report_id: str
    scheduled_at: str

class FDDRetractRequest(BaseModel):
    report_id: str

# In-memory store for tracking task high-level statuses
task_statuses = {}

async def run_research_pipeline_task(task_id: str, request: ResearchRequest):
    """Background task that runs the LangGraph orchestrator up to the interrupt."""
    try:
        task_statuses[task_id] = "Running Data Ingestion (Layer 0)..."
        config = {"configurable": {"thread_id": task_id}}
        
        initial_state = {
            "ticker": request.ticker,
            "company_name_input": request.ticker, # Default to ticker for discovery
            "run_date": datetime.now().isoformat(),
            "company_context": request.company_context,
            "force_refresh": request.force_refresh,
            "existing_notebook": None,
            "identity_data": {},
            "source_registry": {},
            "parallel_results": []
        }
        
        task_statuses[task_id] = "Running Primary Agents (Layer 1 - Layer 4)..."
        
        # Execute up to the interrupt (analyst_review)
        async for event in langgraph_app.astream(initial_state, config=config):
            pass 
            
        task_statuses[task_id] = "Pending Analyst Review"
        
    except Exception as e:
        task_statuses[task_id] = f"Error: {str(e)}"

@router.post("/research/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start the research pipeline for a given ticker."""
    ticker = request.ticker.upper()
    
    # Check if we already have a recent research session (optional: or a published report)
    if not request.force_refresh:
        # Check if there is a published report already
        reports = await notebook_client.get_fdd_reports(ticker)
        published = [r for r in reports if r['status'] == 'PUBLISHED']
        if published:
            # If report exists, we return a virtual task completion
            return {"message": "Existing report found", "task_id": "completed-existing-report"}

    task_id = str(uuid.uuid4())
    task_statuses[task_id] = "Initializing"
    background_tasks.add_task(run_research_pipeline_task, task_id, request)
    return {"message": "Pipeline triggered successfully", "task_id": task_id}

@router.get("/research/state/{task_id}")
async def get_state(task_id: str):
    """Endpoint for the frontend to poll both high-level status and deep LangGraph state."""
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Task not found")
        
    status = task_statuses[task_id]
    state_payload = None
    
    # If the graph has generated state, fetch it
    config = {"configurable": {"thread_id": task_id}}
    graph_state = langgraph_app.get_state(config)
    
    if graph_state and hasattr(graph_state, 'values'):
        state_payload = graph_state.values
        
    return {
        "task_id": task_id, 
        "status": status,
        "graph_state": state_payload
    }

@router.post("/research/inject/{task_id}")
async def inject_review_data(task_id: str, request: InjectRequest):
    """Allows the analyst to inject guidance or edits before resuming."""
    if task_id not in task_statuses or task_statuses[task_id] != "Pending Analyst Review":
        raise HTTPException(status_code=400, detail="Task is not pending review.")
        
    config = {"configurable": {"thread_id": task_id}}
    
    # We construct the resume payload
    resume_payload = {
        "action": request.action,
        "payload": request.payload
    }
    
    # Resuming the graph with the injected data
    task_statuses[task_id] = "Synthesizing and Regenerating..."
    
    try:
        async for event in langgraph_app.astream(Command(resume=resume_payload), config=config):
            pass
        task_statuses[task_id] = "Pending Analyst Review" # Drops back to review if regeneration happens
    except Exception as e:
        task_statuses[task_id] = f"Error during injection: {str(e)}"
        
    return {"message": "Injection processed."}

class ApprovalRequest(BaseModel):
    approve: bool = True
    feedback: Optional[str] = None

@router.post("/research/approve/{task_id}")
async def approve_research(task_id: str, request: Optional[ApprovalRequest] = None, background_tasks: BackgroundTasks = BackgroundTasks()):
    """Approve or reject the FDD draft to resume or re-run the pipeline."""
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Task not found")

    is_approved = request.approve if request else True
    feedback = request.feedback if request else None

    if not is_approved:
        # Handle rejection: Signal graph to re-run synthesis with feedback
        async def run_rejection():
            task_statuses[task_id] = "Re-synthesizing based on feedback..."
            try:
                config = {"configurable": {"thread_id": task_id}}
                langgraph_app.update_state(config, {"analyst_rejection_feedback": feedback})
                async for event in langgraph_app.astream(Command(resume={"action": "reject", "feedback": feedback}), config=config):
                    pass
                task_statuses[task_id] = "Pending Analyst Review"
            except Exception as e:
                task_statuses[task_id] = f"Rejection Error: {str(e)}"
        
        background_tasks.add_task(run_rejection)
        return {"message": "Draft rejected. Re-synthesizing..."}

    async def resume_task():
        task_statuses[task_id] = "Synthesizing Final Report..."
        try:
            config = {"configurable": {"thread_id": task_id}}
            # Use Command(resume=...) to pass the approval signal
            async for event in langgraph_app.astream(Command(resume={"action": "approve"}), config=config):
                pass
            task_statuses[task_id] = "Completed"
        except Exception as e:
            task_statuses[task_id] = f"Error: {str(e)}"
            
    background_tasks.add_task(resume_task)
    return {"message": "Draft approved. Synthesis pipeline resumed."}


# ═══════════════════════════════════════════════════════════════════════════════
# PART A — HITL NOTEBOOK ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# A1 — Claim-level annotation
@router.post("/notebook/annotate")
async def annotate_claim(request: AnnotateRequest):
    """Add a commentary annotation to any notebook entry."""
    try:
        await notebook_client.add_annotation(
            entry_id=request.entry_id,
            analyst_id=request.analyst_id,
            annotation_type=request.annotation_type,
            text=request.text
        )
        return {"message": "Annotation saved.", "entry_id": request.entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# A2 — Confidence override
@router.post("/notebook/override")
async def override_confidence(request: ConfidenceOverrideRequest):
    """Manually promote or demote a claim's confidence tier."""
    try:
        await notebook_client.confidence_override(
            entry_id=request.entry_id,
            analyst_id=request.analyst_id,
            confidence=request.confidence
        )
        return {"message": "Confidence override applied.", "entry_id": request.entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# A3 — Claim suppression
@router.post("/notebook/suppress")
async def suppress_claim(request: SuppressRequest):
    """Suppress a claim from FDD synthesis without deleting it from the notebook."""
    try:
        await notebook_client.suppress_claim(
            entry_id=request.entry_id,
            analyst_id=request.analyst_id,
            reason=request.reason
        )
        return {"message": "Claim suppressed.", "entry_id": request.entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# A4 — Manual data injection
@router.post("/notebook/inject")
async def inject_notebook_claim(request: NotebookInjectRequest):
    """Add a new claim directly to the notebook — tagged as analyst-sourced."""
    try:
        # Fetch the current version for this ticker
        version = await notebook_client.get_latest_version(request.ticker)
        version_id = version["version_id"] if version else str(uuid.uuid4())

        claim_payload = {
            "field_path": request.field_path,
            "value": {"claim": request.claim_text, "source": request.source},
            "verification_status": "analyst_override",
            "source_quality_score": "analyst_injection",
            "hallucination_risk": "none",
            "staleness_severity": "none",
        }
        await notebook_client.inject_manual_claim(
            version_id=version_id,
            company_id=request.ticker,
            ticker=request.ticker,
            dimension=request.dimension,
            claim=claim_payload,
            analyst_id=request.analyst_id
        )
        return {"message": "Claim injected into notebook.", "dimension": request.dimension}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# A5 — Refresh trigger
@router.post("/research/refresh/{task_id}")
async def trigger_refresh(task_id: str, request: RefreshRequest, background_tasks: BackgroundTasks):
    """Trigger a targeted dimension refresh or full company re-run."""
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Task not found")

    config = {"configurable": {"thread_id": task_id}}
    graph_state = langgraph_app.get_state(config)

    if not graph_state or not hasattr(graph_state, 'values'):
        raise HTTPException(status_code=400, detail="No pipeline state found for this task.")

    current_state = graph_state.values
    ticker = current_state.get("ticker", "UNKNOWN")
    company = current_state.get("company_name_input", ticker)

    def run_refresh():
        task_statuses[task_id] = f"Refreshing{' ' + request.dimension if request.dimension else ' (full re-run)'}..."
        try:
            initial_state = {
                "ticker": ticker,
                "company_context": company,
                "existing_notebook": current_state.get("notebook_entries"),
                "identity_data": current_state.get("resolved_identity", {}),
                "parallel_results": []
            }
            # For a targeted dimension refresh, signal the dimension in the state
            if request.dimension:
                initial_state["refresh_dimension"] = request.dimension

            refresh_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            for event in langgraph_app.stream(initial_state, config=refresh_config):
                pass
            task_statuses[task_id] = "Pending Analyst Review"
        except Exception as e:
            task_statuses[task_id] = f"Refresh Error: {str(e)}"

    background_tasks.add_task(run_refresh)
    dimension_label = request.dimension or "all dimensions"
    return {"message": f"Refresh triggered for {dimension_label}.", "task_id": task_id}

# A6 — Diff review
@router.get("/research/diff/{task_id}")
async def get_notebook_diff(task_id: str):
    """Return the structured diff of the latest pipeline run for analyst review."""
    if task_id not in task_statuses:
        raise HTTPException(status_code=404, detail="Task not found")

    config = {"configurable": {"thread_id": task_id}}
    graph_state = langgraph_app.get_state(config)

    if not graph_state or not hasattr(graph_state, 'values'):
        return {"diff": [], "summary": {"new": 0, "updated": 0, "deprecated": 0}}

    state = graph_state.values
    diff = notebook_client.generate_diff(state)
    return {"diff": diff, "task_id": task_id}


# ═══════════════════════════════════════════════════════════════════════════════
# PART B — FDD REPORT HITL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# B1 — Section-level editing
@router.post("/fdd/edit_section")
async def edit_fdd_section(request: FDDSectionEditRequest):
    """Manually edit a specific section of the FDD draft."""
    config = {"configurable": {"thread_id": request.task_id}}
    state = langgraph_app.get_state(config)
    if not state or not hasattr(state, 'values'):
        raise HTTPException(status_code=404, detail="State not found")
    
    current_values = state.values
    draft = current_values.get("fdd_report_draft", {})
    
    if request.section_id == "executive_summary":
        if "executive_summary" in draft:
            draft["executive_summary"]["content"] = request.new_content
    elif "sections" in draft and request.section_id in draft["sections"]:
        draft["sections"][request.section_id]["content"] = request.new_content
    else:
        raise HTTPException(status_code=404, detail=f"Section {request.section_id} not found")
    
    langgraph_app.update_state(config, {"fdd_report_draft": draft})
    return {"message": "Section updated."}

# B2 — Bull/Bear adjudication
@router.post("/fdd/adjudicate")
async def adjudicate_thesis(request: FDDAdjudicateRequest):
    """Accept bull or bear thesis as the analyst's preferred direction."""
    config = {"configurable": {"thread_id": request.task_id}}
    langgraph_app.update_state(config, {"analyst_thesis_adjudication": request.action})
    return {"message": f"Thesis adjudicated to: {request.action}"}

# B4 — Selective regeneration
@router.post("/fdd/regenerate_section")
async def regenerate_fdd_section(request: FDDRegenerateSectionRequest, background_tasks: BackgroundTasks):
    """Regenerate a specific section based on analyst feedback."""
    config = {"configurable": {"thread_id": request.task_id}}
    
    def run_regeneration():
        task_statuses[request.task_id] = f"Regenerating section: {request.section_id}..."
        try:
            # We can use Command(resume=...) or update state and re-trigger
            # For simplicity, we update the state with a regeneration instruction
            instruction = f"REGENERATE SECTION: {request.section_id}\nFEEDBACK: {request.feedback}"
            langgraph_app.update_state(config, {"analyst_regeneration_instruction": instruction})
            # Re-run synthesis node
            langgraph_app.invoke(Command(resume={"action": "regenerate", "section": request.section_id, "feedback": request.feedback}), config=config)
            task_statuses[request.task_id] = "Pending Analyst Review"
        except Exception as e:
            task_statuses[request.task_id] = f"Regeneration Error: {str(e)}"
            
    background_tasks.add_task(run_regeneration)
    return {"message": f"Regeneration triggered for {request.section_id}."}

# B5 — Publication control
@router.post("/fdd/publish")
async def publish_fdd(request: FDDPublishRequest):
    """Publish the final FDD report and persist it to CockroachDB."""
    config = {"configurable": {"thread_id": request.task_id}}
    state = langgraph_app.get_state(config)
    if not state or not hasattr(state, 'values'):
        raise HTTPException(status_code=404, detail="State not found")
    
    current_values = state.values
    draft = current_values.get("fdd_report_draft", {})
    ticker = current_values.get("ticker", "UNKNOWN")
    
    report_id = await notebook_client.save_fdd_report(ticker, draft, request.analyst_id)
    
    # Mark state as published
    langgraph_app.update_state(config, {"publication_id": report_id, "status": "PUBLISHED"})
    task_statuses[request.task_id] = "Completed (Published)"
    
    # [NEW] Log Layer 6 Telemetry (Multi-Stage)
    telemetry_buffer = current_values.get("prompt_telemetry_buffer", {})
    for p_name, t_data in telemetry_buffer.items():
        # Tag with final results where applicable
        if p_name == "report/fdd_synthesis_cold":
            t_data["final_approved_output"] = json.dumps(draft)
        elif p_name == "report/conflict_resolution":
            t_data["final_approved_output"] = json.dumps(draft.get("sections", {}).get("investment_thesis_bull_bear", {}))
        elif p_name.startswith("materiality/"):
            # For materiality, we could log the final notebook entries as the "Approved" set
            # But simpler is to log it as a reference point
            t_data["final_approved_output"] = "CONSIDERED_DURING_PUBLICATION"
            
        # Log to DB
        await notebook_client.log_prompt_telemetry(t_data)
        logger.info(f"--- [LAYER 6] Telemetry logged for {ticker}/{p_name} ---")
    
    # [NEW] Log Portfolio Signal (Layer 7 Tracking)
    trading_signal = current_values.get("trading_signal")
    if trading_signal:
        try:
            import yfinance as yf
            ticker_data = yf.Ticker(ticker)
            entry_price = ticker_data.fast_info.get('last_price')
            if not entry_price:
                hist = ticker_data.history(period="1d")
                if not hist.empty:
                    entry_price = hist['Close'].iloc[-1]
            
            if entry_price:
                trading_signal['entry_price'] = float(entry_price)
                trading_signal['ticker'] = ticker
                await notebook_client.save_portfolio_signal(trading_signal)
                logger.info(f"--- [LAYER 7] Trading Signal Logged for {ticker} at ${entry_price:.2f} ---")
        except Exception as e:
            logger.error(f"Failed to log portfolio signal for {ticker}: {e}")

    return {"message": "Report published successfully.", "report_id": report_id}

@router.post("/fdd/schedule")
async def schedule_fdd(request: FDDScheduleRequest):
    """Schedule a published report for a future timestamp."""
    await notebook_client.schedule_report(request.report_id, request.scheduled_at)
    return {"message": f"Report scheduled for {request.scheduled_at}"}

@router.post("/fdd/retract")
async def retract_fdd(request: FDDRetractRequest):
    """Retract a published or scheduled report."""
    await notebook_client.retract_report(request.report_id)
    return {"message": "Report retracted successfully."}

# Layer 6 — Prompt Optimization
@router.post("/prompts/optimize")
async def trigger_prompt_optimization(background_tasks: BackgroundTasks):
    """Triggers the ML pipeline to optimize prompts based on recent feedback."""
    optimizer = PromptOptimizer()
    
    async def run_optimization():
        try:
            # Optimize the entire Layer 4-5 reasoning chain
            prompts_to_optimize = [
                ("report", "fdd_synthesis_cold"),
                ("report", "conflict_resolution"),
                ("materiality", "materiality_filter_cold"),
                ("materiality", "materiality_filter_delta")
            ]
            
            for dim, p_name in prompts_to_optimize:
                await optimizer.optimize_prompt(dim, p_name)
                
            logger.info("--- [LAYER 6] Full-Chain Prompt Optimization Complete ---")
        except Exception as e:
            logger.error(f"Prompt Optimization Failed: {e}")

    background_tasks.add_task(run_optimization)
    return {"message": "Prompt optimization cycle triggered in background."}

# B6 — Version comparison (fetch history)
@router.get("/fdd/history/{ticker}")
async def get_fdd_history(ticker: str):
    """Fetch all published FDD reports for a ticker."""
    reports = await notebook_client.get_fdd_reports(ticker)
    return {"reports": reports}

import yfinance as yf

# ─── Search Endpoints ──────────────────────────────────────────────────────────

@router.delete("/research/delete/{ticker}")
async def delete_ticker_data(ticker: str):
    """Completely delete all data related to a ticker from Turso, Qdrant, and File System."""
    ticker = ticker.upper()
    try:
        logger.info(f"Triggering full deletion for {ticker}...")
        
        # 1. Delete from CockroachDB
        await notebook_client.delete_ticker_data(ticker)
        
        # 2. Delete from Qdrant
        rag_pipeline.delete_collection(ticker)
        
        # 3. Delete from File System
        # Base directory for SEC filings
        sec_dir = os.path.join("downloads", "sec", "sec-edgar-filings", ticker)
        if os.path.exists(sec_dir):
            shutil.rmtree(sec_dir)
            logger.info(f"Deleted SEC directory: {sec_dir}")
        
        # Cleanup any other potential locations (e.g. news) if they exist
        news_dir = os.path.join("downloads", "news", ticker)
        if os.path.exists(news_dir):
            shutil.rmtree(news_dir)
            logger.info(f"Deleted News directory: {news_dir}")
            
        return {"message": f"Successfully deleted all data for {ticker}"}
    except Exception as e:
        logger.error(f"Error deleting data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickers/search")
async def search_tickers(q: str = ""):
    """Search for tickers in Notebook history and the global market via yfinance."""
    results = []
    seen = set()

    # 1. Search existing Notebooks in CockroachDB
    try:
        ticker_list = await notebook_client.search_tickers(q)
        for ticker in ticker_list:
            results.append({"ticker": ticker, "name": f"Local Notebook: {ticker}", "source": "Notebook"})
            seen.add(ticker)
    except Exception as e:
        print(f"Error searching notebooks: {e}")

    # 2. Global search via yfinance
    if len(q) >= 1:
        try:
            # yfinance search provides a list of suggestions
            ticker_data = yf.Search(q, max_results=8).quotes
            for quote in ticker_data:
                symbol = quote.get('symbol')
                name = quote.get('longname') or quote.get('shortname') or symbol
                if symbol not in seen:
                    results.append({
                        "ticker": symbol,
                        "name": name,
                        "source": "Market"
                    })
                    seen.add(symbol)
        except Exception as e:
            print(f"Error searching yfinance: {e}")

    return {"results": results[:12]}

@router.get("/tickers/all")
async def get_all_tickers():
    """Returns a list of all tickers currently in the database."""
    tickers = await notebook_client.get_all_tickers()
    return {"tickers": tickers}

@router.get("/notebook/entries/{ticker}")
async def get_notebook_entries(ticker: str):
    """Retrieves all research claims for a ticker, grouped by dimension."""
    entries = await notebook_client.get_notebook_entries(ticker.upper())
    return {"ticker": ticker.upper(), "entries": entries}

@router.get("/fdd/reports/{ticker}")
async def get_fdd_reports(ticker: str):
    """Retrieves all FDD reports for a ticker."""
    reports = await notebook_client.get_fdd_reports(ticker.upper())
    return {"ticker": ticker.upper(), "reports": reports}

@router.get("/prompts/history")
async def get_prompt_history():
    """Returns the diff between baseline prompts and optimized prompts."""
    try:
        base_dir = os.path.join(os.path.dirname(__file__), "agents", "prompts")
        opt_dir = os.path.join(os.path.dirname(__file__), "agents", "prompts_optimized")
        
        history = []
        
        # Iterate through all dimensions in optimized dir
        if os.path.exists(opt_dir):
            for dim in os.listdir(opt_dir):
                dim_path = os.path.join(opt_dir, dim)
                if os.path.isdir(dim_path):
                    for p_file in os.listdir(dim_path):
                        if p_file.endswith(".txt"):
                            p_name = p_file.replace(".txt", "")
                            
                            # Read Optimized
                            with open(os.path.join(dim_path, p_file), "r", encoding="utf-8") as f:
                                opt_content = f.read()
                                
                            # Read Baseline
                            base_path = os.path.join(base_dir, dim, p_file)
                            base_content = ""
                            if os.path.exists(base_path):
                                with open(base_path, "r", encoding="utf-8") as f:
                                    base_content = f.read()
                                    
                            history.append({
                                "dimension": dim,
                                "prompt_name": p_name,
                                "baseline": base_content,
                                "optimized": opt_content,
                                "last_updated": datetime.fromtimestamp(os.path.getmtime(os.path.join(dim_path, p_file))).isoformat()
                            })
                            
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/signals")
async def get_portfolio_signals():
    """Returns all logged portfolio signals and their performance."""
    try:
        signals = await notebook_client.get_portfolio_signals()
        return {"signals": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

