import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Annotated, Dict, List, Optional, TypedDict, Union, Any, Tuple
from langgraph.graph import StateGraph, END

# Import the agent instances
from backend.agents.identity import identity_agent
from backend.agents.sector import sector_agent
from backend.agents.business_mechanics import business_mechanics_agent
from backend.agents.business_segments import business_segments_agent
from backend.agents.business_strategy import business_strategy_agent
from backend.agents.management_comp import management_comp_agent
from backend.agents.management_bios import management_bios_agent
from backend.agents.dossier import dossier_agent
from backend.agents.footprint import footprint_agent

# Import RAG, Verification, and Notifications
from backend.ingestion.rag_pipeline import rag_pipeline
from backend.ingestion.edgar_client import edgar_client
from backend.pipeline.verification import verification_pipeline
from backend.pipeline.notifications import notification_system

# Import Layer 4 Components
from backend.agents.materiality_filter import materiality_filter_agent
from backend.pipeline.notebook_client import notebook_client

# Import Layer 5 Components
from backend.agents.fdd_synthesis_agent import fdd_synthesis_agent
from backend.agents.report_debate import bull_bear_agent, conflict_resolution_agent
from backend.agents.analyst import analyst_agent

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    ticker: str
    company_name_input: str
    run_date: str
    source_chunks: Optional[str]
    notebook_entries: Optional[Dict[str, Any]]
    resolved_identity: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    errors: List[str]
    refetch_queue: List[Dict[str, Any]]
    verification_handoffs: Dict[str, Any]
    alerts: Dict[str, List[str]]
    fdd_synthesis_queue: Optional[Dict[str, Any]]
    notebook_version: int
    materiality_config: Dict[str, Any]
    fdd_report_draft: Optional[Dict[str, Any]]
    bull_thesis: Optional[Dict[str, Any]]
    bear_thesis: Optional[Dict[str, Any]]
    conflict_resolution: Optional[Dict[str, Any]]
    top_material_findings: List[str]
    what_changed_summary: Dict[str, Any]
    source_registry: Dict[str, str] # Global deduplicated map of source_id -> content
    force_refresh: bool
    company_context: str
    
    # HITL / Feedback
    analyst_regeneration_instruction: Optional[str]
    analyst_rejection_feedback: Optional[str]
    analyst_thesis_adjudication: Optional[str] # "accept_bull", "accept_bear", "neutral"
    publication_id: Optional[str]
    status: str
    re_run_list: List[str] # List of dimensions to refresh
    refresh_dimension: Optional[str] # Manual trigger
    analyst_review_items: List[Dict[str, Any]] # Items flagged for manual review
    prompt_telemetry_buffer: Dict[str, Any]
    last_fdd_synthesis_queue: Dict[str, Any]
    investment_committee_minutes: Dict[str, Any]
    systemic_risks: List[Dict[str, Any]]
    trading_signal: Dict[str, Any]

def _requires_retry(gate_result: Dict[str, Any]) -> bool:
    """Helper to determine if a gate result warrants a re-run of the agent."""
    if not gate_result:
        return False
    status = gate_result.get("status", "PASS")
    # Gate 1: Hallucination
    if gate_result.get("overall_hallucination_risk") == "high":
        return True
    if gate_result.get("ungrounded_claim_count", 0) > 0:
        return True
    # Gate 2: Source Quality
    if status == "FAIL":
        return True
    return False

def _get_summary_val(gate: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely extracts values from complex gate results."""
    if not gate:
        return default
    return gate.get(key, default)

async def _run_agent_with_verification(agent: Any, query_hint: str, state: GraphState, layer: int = 1) -> Tuple:
    """
    Helper to run an agent followed by the Layer 3 Verification Gates.
    Includes autonomous Gate 1 retry logic (max 2 retries).
    """
    ticker = state.get("ticker", "Unknown").upper()
    
    # 0. Safety: Ensure inputs are dictionaries
    resolved_identity = state.get("resolved_identity", {})
    if not isinstance(resolved_identity, dict):
        resolved_identity = {}
        
    resolved = {
        "company_name": resolved_identity.get("company_name", state.get("company_name_input", "Unknown")),
        "ticker": ticker,
        "exchange": resolved_identity.get("exchange", "Unknown")
    }
    
    notebook_entries = state.get("notebook_entries", {})
    if not isinstance(notebook_entries, dict):
        notebook_entries = {}
    
    # [OPTIMIZATION] Trim notebook context to the 5 most recent entries to keep prompts small and fast
    trimmed_notebook = {}
    for dim, entries in notebook_entries.items():
        if isinstance(entries, list):
            trimmed_notebook[dim] = entries[-5:] # Take last 5 most recent
        else:
            trimmed_notebook[dim] = entries
    notebook_entries = trimmed_notebook

        
    run_type = "delta" if notebook_entries.get(agent.dimension_name) else "cold"
    last_run = state.get("last_run_date")
    
    # 2. Agent Execution Loop (Retry for Hallucinations)
    attempts = 0
    max_retries = 2
    
    while attempts <= max_retries:
        # 1. Dimension-Specific RAG Query
        queries = {
            "identity": f"Full legal name, ticker, exchange, and primary address for {ticker}",
            "sector": f"Sector classification, industry, and peer group for {ticker}",
            "business_mechanics": f"Revenue model, pricing power, value drivers, and competitive moat for {ticker}",
            "business_segments": f"Segment revenue, geographic breakdown, and business unit performance for {ticker}",
            "business_strategy": f"Strategic initiatives, R&D focus, and future growth bets for {ticker}",
            "management_comp": f"Executive compensation, CEO pay ratio, and board member pay for {ticker}",
            "management_bios": f"Biographies of executive officers, board members, and leadership history for {ticker}",
            "dossier": f"Board composition, institutional ownership, and 13D/G filings for {ticker}",
            "footprint": f"ESG ratings, major litigation, and public sentiment for {ticker}"
        }
        query = queries.get(agent.dimension_name, f"Financials and operations for {ticker}")
        
        rag_res = await asyncio.to_thread(rag_pipeline.query_index, ticker, query, layer=layer, run_type=run_type)
        
        # [FIX] For the Identity dimension, explicitly pull the dei_summary if it exists 
        # to ensure critical fields like CIK and HQ are populated.
        context = rag_res["context"]
        if agent.dimension_name == "identity":
            ticker_dir = os.path.join("downloads", "sec", "sec-edgar-filings", ticker)
            summary_path = os.path.join(ticker_dir, "dei_summary.txt")
            if os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as f:
                    dei_content = f.read()
                    if dei_content not in context:
                        context = f"{dei_content}\n\n{context}"
        
        source_registry = state.get("source_registry", {})

        new_texts = rag_res.get("source_texts", {})
        if new_texts:
            source_registry.update(new_texts)
        
        # 2. Agent Analysis
        variables = {
            **state,
            "source_chunks": context,
            "ticker": ticker,
            "company_name": resolved.get("legal_name", ticker)
        }

        agent_res = await agent.analyze(variables)
        
        if agent_res.get("status") == "agent_failure":
            logger.error(f"[{agent.dimension_name}] Agent returned failure: {agent_res.get('error')}. Skipping verification gates.")
            return agent.dimension_name, {}, [], notification_system.get_pending_alerts(), {}, {}
        
        parsed = json.loads(agent_res["raw_output"]) if agent_res["status"] == "success" else {"error": agent_res.get("status")}
        
        # 3. Layer 3 Verification
        print(f"--- [LAYER 3] Verifying {agent.dimension_name} via 3-Gate Pipeline ---", flush=True)
        handoff_data = {
            "agent_output": parsed,
            "source_documents": rag_res["source_ids"],
            "source_tier_map": rag_res.get("source_tier_map", {}),
            "run_type": run_type,
            "company": resolved.get("legal_name", ticker),
            "ticker": ticker
        }
        
        notebook_ready, gates = await verification_pipeline.verify_agent_output(handoff_data, state)
        
        # Log gate results
        g1_status = "PASS" if not _requires_retry(gates.get("gate1", {})) else "FAIL"
        print(f"    [Gate 1: Hallucination] -> {g1_status}", flush=True)
        print(f"    [Gate 2: Source Audit] -> {gates.get('gate2', {}).get('status', 'OK')}", flush=True)
        print(f"    [Gate 3: Staleness] -> {gates.get('gate3', {}).get('status', 'OK')}", flush=True)
        
        # [PRD UPDATE] Analyze Notifications
        notification_system.process_gate_results(agent.dimension_name, gates)
        
        # Check for "All three gates failed" -> Full Re-run (once)
        gate1 = gates.get("gate1", {})
        gate2 = gates.get("gate2", {})
        gate3 = gates.get("gate3", {})
        
        all_failed = (
            _requires_retry(gate1) and
            _requires_retry(gate2) and
            _requires_retry(gate3)
        )
        
        if all_failed and attempts == 0:
            attempts = 1 # Force second attempt
            logger.warning(f"--- [LAYER 3 CRITICAL] All 3 gates failed for {agent.dimension_name}. Triggering full re-run. ---")
            continue

        # 4. Check Gate 1: Hallucination Retry Trigger
        if _requires_retry(gate1) and attempts < max_retries:
            attempts += 1
            logger.warning(f"--- [GATE 1 RETRY] {agent.dimension_name} attempt {attempts}/{max_retries} ---")
            
            # Narrow context using Gate 1 identified passages
            ungrounded = gate1.get("ungrounded_claims_summary", [])
            if ungrounded and isinstance(ungrounded, list):
                try:
                    narrowed_context = "\n\n".join([f"CLAIM: {u.get('claim_text', 'Unknown')}\nREASON: {u.get('reason_ungrounded', 'Unknown')}" for u in ungrounded if isinstance(u, dict)])
                    current_context = f"{rag_res['context']}\n\n[VERIFICATION ERROR]\nThe following claims were ungrounded. Please correct them using the source data:\n{narrowed_context}"
                except AttributeError:
                    pass # Safety net for malformed list items
            continue # Re-run loop
            
        # 5. Gate 2: Source Gap Retry (New Implementation)
        if _requires_retry(gate2) and attempts < max_retries:
            attempts += 1
            logger.warning(f"--- [GATE 2 RETRY] {agent.dimension_name} attempt {attempts}/{max_retries} ---")
            
            # Re-run with explicit citation instruction
            current_context = f"{rag_res['context']}\n\n[SOURCING ERROR]\nSome claims were missing authoritative citations. Please ensure every material claim is attributed to a Tier 1 or Tier 2 source where possible."
            continue # Re-run loop

        # 6. Final Status Stamping (for Notebook and FDD use)
        if isinstance(notebook_ready, list):
            for claim in notebook_ready:
                if not isinstance(claim, dict): continue
                # Map to PRD status tiers
                hall_risk = _get_summary_val(gate1, "overall_hallucination_risk")
                hall_count = _get_summary_val(gate1, "ungrounded", 0)
                source_q = _get_summary_val(gate2, "overall_source_quality")
                source_absent = _get_summary_val(gate2, "source_quality_absent", 0)
                
                # PRD: Hallucination failed OR Source unattributable failed -> Unverified
                if hall_risk == "high" or hall_count > 0 or source_absent > 0:
                    claim["verification_status"] = "unverified"
                # PRD: Source unattributable fixed -> Partially Verified
                elif source_q == "weak" or source_q == "medium":
                    claim["verification_status"] = "partially_verified"
                else:
                    claim["verification_status"] = "verified"
                    
                # Store source quality for tiered filtering
                claim["source_quality_score"] = source_q or "low"
                    
                # Staleness labeling
                if _get_summary_val(gate3, "refetch_triggered"):
                    claim["staleness_severity"] = "refreshed"
                elif _get_summary_val(gate3, "staleness_detected"):
                    claim["staleness_severity"] = "stale"
                    
        # 7. Gate 3: Staleness (Queue for Refetch)
        refetches = gate3.get("refetch_queue", [])
        
        return agent.dimension_name, notebook_ready, refetches, notification_system.get_pending_alerts(), handoff_data, source_registry

    return agent.dimension_name, {}, [], notification_system.get_pending_alerts(), {}, {}

async def data_ingestion_node(state: GraphState):
    """Layer 0: Download and ingest filings if missing or forced."""
    ticker = state['ticker'].upper()
    print(f"--- [LAYER 0] Running Data Ingestion for {ticker} ---", flush=True)
    
    # Check if data already exists in the shared collection to skip ingestion
    force_refresh = state.get("force_refresh", False)
    try:
        from qdrant_client.http import models as qmodels
        collection_name = "onist_research_v1"
        count_res = rag_pipeline.client.count(
            collection_name=collection_name,
            count_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="ticker",
                        match=qmodels.MatchValue(value=ticker)
                    )
                ]
            )
        )
        if count_res.count > 0 and not force_refresh:
            print(f"--- [LAYER 0] Data for {ticker} already exists in shared collection ({count_res.count} nodes). Skipping ingestion. ---", flush=True)
            return {}
        elif force_refresh:
            print(f"--- [LAYER 0] Force Refresh active. Removing existing points for {ticker}... ---", flush=True)
            rag_pipeline.delete_collection(ticker)
    except Exception as e:
        print(f"--- [LAYER 0] Collection check failed ({e}). Proceeding to ingest... ---", flush=True)

    # 1. Download filings (10-K, 10-Q) and get DEI metadata
    metadata = edgar_client.download_filings(ticker, amount=1)
    
    # 2. Create a DEI summary file for RAG context
    ticker_dir = os.path.join("downloads", "sec", "sec-edgar-filings", ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    
    dei = metadata.get("dei", {})
    if dei:
        summary_path = os.path.join(ticker_dir, "dei_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("--- CANONICAL ENTITY IDENTITY DATA (DEI) ---\n")
            for key, value in dei.items():
                f.write(f"{key.replace('_', ' ').upper()}: {value}\n")
            f.write("--- END DEI DATA ---\n")
        print(f"--- [LAYER 0] Created DEI summary at {summary_path} ---", flush=True)

    # 3. Index into RAG
    
    if os.path.exists(ticker_dir):
        print(f"--- [LAYER 0] Indexing filings from {ticker_dir} ---", flush=True)
        # Run synchronous ingestion in a thread to avoid blocking the event loop
        await asyncio.to_thread(rag_pipeline.ingest_directory, ticker_dir, ticker)
        
        # Populate preliminary source library for UI
        ingested_files = []
        for root, _, filenames in os.walk(ticker_dir):
            for f in filenames:
                if f.endswith(('.html', '.htm', '.pdf', '.txt')):
                    ingested_files.append(f)
        
        preliminary_handoff = {
            "source_documents": ingested_files,
            "source_tier_map": {f: "Tier1" for f in ingested_files},
            "agent_output": {},
            "run_type": "cold"
        }
        return {"verification_handoffs": {"layer_0": preliminary_handoff}}
    else:
        print(f"--- [LAYER 0] Warning: No filings found in {ticker_dir} ---")
        return {}

async def staleness_sweep_node(state: GraphState):
    """Step 1: Staleness Reviewer checks every Notebook entry against category thresholds."""
    print(f"--- [STEP 1] Running Staleness Sweep ---", flush=True)
    re_run_list = state.get("re_run_list", [])
    
    # Manual trigger check
    if state.get("refresh_dimension"):
        re_run_list.append(state["refresh_dimension"])
        
    # Automatic staleness check with category thresholds
    notebook = state.get("notebook_entries", {})
    now = datetime.now()
    
    thresholds = {
        "management_bios": 90, # Stable
        "management_comp": 90,
        "sector_classification": 90,
        "business_mechanics": 30, # Moderate
        "business_segments": 30,
        "business_strategy": 30,
        "dossier": 30,
        "footprint": 14, # Volatile
    }
    
    if notebook:
        for dim, entries in notebook.items():
            if dim in re_run_list: continue
            
            is_stale = False
            threshold_days = thresholds.get(dim, 30)
            
            if isinstance(entries, list):
                for e in entries:
                    # Check explicit staleness flag from verification gates
                    if e.get("staleness_severity") == "stale":
                        is_stale = True
                        break
                    
                    # Check creation date
                    created_at_str = e.get("created_at")
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                            age_days = (now.replace(tzinfo=None) - created_at.replace(tzinfo=None)).days
                            if age_days > threshold_days:
                                is_stale = True
                                break
                        except: pass
            
            if is_stale:
                re_run_list.append(dim)
                
    return {"re_run_list": list(set(re_run_list))}

async def event_detection_node(state: GraphState):
    """Step 2 & 3: Map SEC filings and News to dimensions."""
    print(f"--- [STEP 2] Running Event Detection ---", flush=True)
    re_run_list = state.get("re_run_list", [])
    
    # Mock event detection (would normally check an 'events' DB or API)
    # We look for context clues in company_context or identity_data
    context = state.get("company_context", "").lower()
    
    if "10-q" in context or "10-k" in context:
        re_run_list.extend(["business_segments", "business_mechanics", "business_strategy"])
    if "8-k" in context or "ceo" in context or "cfo" in context:
        re_run_list.extend(["management_bios", "management_comp", "dossier"])
    if "proxy" in context:
        re_run_list.extend(["management_comp", "management_bios", "dossier"])
    if "news" in context or "acquisition" in context:
        re_run_list.append("footprint")
        
    # Always include identity for cold runs or if missing
    if not state.get("notebook_entries") or "identity" not in state["notebook_entries"]:
        re_run_list.append("identity")
        
    return {"re_run_list": list(set(re_run_list))}

async def identity_node(state: GraphState):
    print(f"--- [MICRO-BATCH 0] Running Identity Normalization ---", flush=True)
    dim, data, refetches, alerts, handoff, registry = await _run_agent_with_verification(identity_agent, "legal name, ticker, exchange, CIK", state, layer=1)
    
    # 0. Safety: Ensure data is a dict
    if not isinstance(data, dict):
        data = {}
        
    company_info = data.get("company", {})
    if not isinstance(company_info, dict):
        company_info = {}
        
    def _get_nested(obj: dict, key1: str, key2: str, default: Any) -> Any:
        val = obj.get(key1, {})
        if isinstance(val, dict):
            return val.get(key2, default)
        return default

    identity_data = {
        "company_name": _get_nested(company_info, "legal_name", "value", state['company_name_input']),
        "ticker": _get_nested(company_info, "primary_ticker", "value", state['ticker']),
        "exchange": _get_nested(company_info, "primary_ticker", "exchange", "Unknown")
    }
    
    return {
        "resolved_identity": identity_data,
        "agent_outputs": {dim: data},
        "verification_handoffs": {dim: handoff},
        "source_registry": registry,
        "refetch_queue": refetches,
        "alerts": alerts
    }

async def micro_batch_node(state: GraphState):
    print("--- [LAYER 1] Running Research Batches (Staggered) ---", flush=True)
    agent_outputs = state.get("agent_outputs", {})
    verification_handoffs = state.get("verification_handoffs", {})
    refetch_queue = state.get("refetch_queue", [])
    current_alerts = state.get("alerts", {"immediate": [], "standard": [], "informational": []})

    # Clear notification buffer for this run
    notification_system.clear()

    # Micro-batch A
    tasks_a = []
    if not state.get("notebook_entries") or "sector" in state["re_run_list"]:
        tasks_a.append(_run_agent_with_verification(sector_agent, "GICS sector, industry, peers", state))
    if not state.get("notebook_entries") or "business_mechanics" in state["re_run_list"]:
        tasks_a.append(_run_agent_with_verification(business_mechanics_agent, "revenue model, moat", state))
    if not state.get("notebook_entries") or "business_segments" in state["re_run_list"]:
        tasks_a.append(_run_agent_with_verification(business_segments_agent, "segments, margins", state))
    
    if tasks_a:
        results_a = await asyncio.gather(*tasks_a)
        for dim, data, rf, alerts, handoff, registry in results_a:
            agent_outputs[dim] = data
            verification_handoffs[dim] = handoff
            state["source_registry"].update(registry)
            refetch_queue.extend(rf)
            for k in current_alerts: current_alerts[k].extend(alerts.get(k, []))
        
    await asyncio.sleep(0.15)
    
    # Micro-batch B
    tasks_b = []
    if not state.get("notebook_entries") or "business_strategy" in state["re_run_list"]:
        tasks_b.append(_run_agent_with_verification(business_strategy_agent, "strategic bets, risks", state))
    if not state.get("notebook_entries") or "management_comp" in state["re_run_list"]:
        tasks_b.append(_run_agent_with_verification(management_comp_agent, "compensation metrics", state))
    if not state.get("notebook_entries") or "management_bios" in state["re_run_list"]:
        tasks_b.append(_run_agent_with_verification(management_bios_agent, "career history, bios", state))
        
    if tasks_b:
        results_b = await asyncio.gather(*tasks_b)
        for dim, data, rf, alerts, handoff, registry in results_b:
            agent_outputs[dim] = data
            verification_handoffs[dim] = handoff
            state["source_registry"].update(registry)
            refetch_queue.extend(rf)
            for k in current_alerts: current_alerts[k].extend(alerts.get(k, []))
        
    return {
        "agent_outputs": agent_outputs, 
        "verification_handoffs": verification_handoffs,
        "source_registry": state["source_registry"],
        "refetch_queue": refetch_queue, 
        "alerts": current_alerts
    }

async def specialist_node(state: GraphState):
    print("--- [LAYER 2] Running Specialist Agents ---", flush=True)
    agent_outputs = state.get("agent_outputs", {})
    verification_handoffs = state.get("verification_handoffs", {})
    refetch_queue = state.get("refetch_queue", [])
    current_alerts = state.get("alerts", {"immediate": [], "standard": [], "informational": []})
    
    notification_system.clear()

    tasks = []
    if not state.get("notebook_entries") or "dossier" in state["re_run_list"]:
        tasks.append(_run_agent_with_verification(dossier_agent, "board composition, 13D/G", state, layer=2))
    if not state.get("notebook_entries") or "footprint" in state["re_run_list"]:
        tasks.append(_run_agent_with_verification(footprint_agent, "sentiment, ESG, litigation", state, layer=2))
        
    if tasks:
        results = await asyncio.gather(*tasks)
        for dim, data, rf, alerts, handoff, registry in results:
            agent_outputs[dim] = data
            verification_handoffs[dim] = handoff
            state["source_registry"].update(registry)
            refetch_queue.extend(rf)
            for k in current_alerts: current_alerts[k].extend(alerts.get(k, []))
        
    return {
        "agent_outputs": agent_outputs, 
        "verification_handoffs": verification_handoffs,
        "source_registry": state["source_registry"],
        "refetch_queue": refetch_queue, 
        "alerts": current_alerts
    }

async def materiality_filter_node(state: GraphState):
    print("--- [LAYER 4] Running Materiality Filter (Mistral) ---", flush=True)
    
    run_type = "delta" if state.get("notebook_entries") else "cold"
    
    # Aggregate all Gate 3 outputs
    all_gate3 = state.get("agent_outputs", {})
    
    variables = {
        "company_name": state["resolved_identity"]["company_name"],
        "ticker": state["resolved_identity"]["ticker"],
        "run_date": state["run_date"],
        "run_type": run_type,
        "all_gate3_outputs": json.dumps(all_gate3, indent=2),
        "existing_notebook": json.dumps(state.get("notebook_entries", {}), indent=2),
        "last_run_date": state.get("last_run_date", "N/A"),
        "last_fdd_synthesis_queue": json.dumps(state.get("last_fdd_synthesis_queue", {}), indent=2),
        "materiality_config": json.dumps(state.get("materiality_config", {}), indent=2)
    }
    
    # CRITICAL: Temporarily using analyst_agent (GPT-4) as primary due to Mistral outage
    print("--- [LAYER 4] PIVOT: Using GPT-4 for Materiality (Mistral Outage) ---", flush=True)
    res = await analyst_agent.analyze(variables)
    
    # Safety: Ensure res is a dict
    if not isinstance(res, dict):
        res = {}
        
    def _get_nested_val(obj: dict, key1: str, key2: str, default: Any) -> Any:
        val = obj.get(key1, {})
        if isinstance(val, dict):
            return val.get(key2, default)
        return default

    regeneration_required = _get_nested_val(res, "delta_filter_summary", "fdd_regeneration_required", True) if run_type == "delta" else True
    
    # Buffer telemetry for Layer 6 optimization
    telemetry_buffer = state.get("prompt_telemetry_buffer", {}) or {}
    telemetry_buffer[f"materiality/materiality_filter_{run_type}"] = {
        "prompt_name": f"materiality/materiality_filter_{run_type}",
        "dimension": "materiality",
        "model_name": "analyst_agent_gpt4", # Since it's pivoted to GPT-4
        "input_context": variables,
        "raw_output": json.dumps(res)
    }

    return {
        "fdd_synthesis_queue": res.get("fdd_synthesis_queue") if run_type == "cold" else res.get("updated_fdd_synthesis_queue"),
        "materiality_summary": res.get("materiality_summary") if run_type == "cold" else res.get("updated_materiality_summary"),
        "what_changed_summary": res.get("what_changed_summary"),
        "fdd_regeneration_required": regeneration_required,
        "prompt_telemetry_buffer": telemetry_buffer
    }

async def notebook_write_node(state: GraphState):
    print("--- [LAYER 4] Writing to Research Notebook (PostgreSQL) ---", flush=True)
    
    # 1. Versioned Write
    write_res = await notebook_client.write_notebook_orchestration(state)
    
    # 2. Semantic Index Update (Step 6)
    # We collect all current entries to re-index or just the delta
    # For now, we update the semantic index for all entries in the state
    entries_to_index = []
    for dim, claims in state.get("agent_outputs", {}).items():
        if isinstance(claims, list):
            for c in claims:
                if isinstance(c, dict):
                    entries_to_index.append({"dimension": dim, "field_path": c.get("field_path"), "value": c, "entry_id": c.get("entry_id")})
    
    await notebook_client.update_semantic_index(entries_to_index)
    
    # 3. Diff Generation
    diff = notebook_client.generate_diff(state)
    
    # 3. Notification Dispatch
    notification_system.dispatch_diff(diff)
    
    return {
        "notebook_version": write_res["version_number"],
        "alerts": notification_system.get_pending_alerts()
    }

async def analyst_review_node(state: GraphState):
    """
    Human-in-the-loop breakpoint.
    Persists the current draft to the database for analyst review.
    """
    print("--- [HITL] Analyst Review & Approval ---", flush=True)
    ticker = state.get("ticker", "Unknown").upper()
    
    # 1. Flag items for review (e.g. unverified material claims)
    review_items = []
    agent_outputs = state.get("agent_outputs", {})
    
    # Logic: Any unverified claim in Layer 2 or Layer 4 that is "high" materiality
    # For now, we'll collect alerts that are "critical"
    alerts = state.get("alerts", {})
    for dim, msgs in alerts.items():
        for msg in msgs:
            if "CRITICAL" in msg or "UNVERIFIED" in msg:
                review_items.append({
                    "dimension": dim,
                    "issue": msg,
                    "status": "PENDING"
                })
    
    # 2. Persist DRAFT to CockroachDB
    report_draft = state.get("fdd_report_draft", {})
    if report_draft:
        try:
            report_draft["status"] = "DRAFT"
            await notebook_client.save_fdd_report(
                ticker=ticker,
                report=report_draft,
                analyst_id="system"
            )
        except Exception as e:
            logger.error(f"Failed to persist draft to DB: {e}")

    return {"analyst_review_items": review_items, "status": "DRAFT — Pending Analyst Approval"}

async def report_synthesis_node(state: GraphState):
    print("--- [LAYER 5] Running FDD Report Synthesis (Mistral) ---", flush=True)
    variables = {
        "company_name": state["resolved_identity"]["company_name"],
        "ticker": state["resolved_identity"]["ticker"],
        "run_date": state["run_date"],
        "fdd_synthesis_queue": json.dumps(state.get("fdd_synthesis_queue"), indent=2),
        "materiality_summary": state.get("materiality_summary"),
        "top_material_findings": state.get("top_material_findings")
    }
    
    # Inject analyst feedback if present
    if state.get("analyst_regeneration_instruction"):
        variables["analyst_feedback"] = state["analyst_regeneration_instruction"]
    if state.get("analyst_rejection_feedback"):
        variables["rejection_feedback"] = state["analyst_rejection_feedback"]
        
    # CRITICAL: PIVOT to GPT-4 if Mistral fails
    try:
        res = await fdd_synthesis_agent.process(variables)
    except Exception as e:
        print(f"--- [LAYER 5] PIVOT: Mistral failed ({e}). Using GPT-4 for Synthesis ---", flush=True)
        res = await analyst_agent.analyze(variables)
        
    # Buffer telemetry for Layer 6 optimization
    telemetry_buffer = state.get("prompt_telemetry_buffer", {}) or {}
    telemetry_buffer["report/fdd_synthesis_cold"] = {
        "prompt_name": "report/fdd_synthesis_cold",
        "dimension": "report",
        "model_name": fdd_synthesis_agent.model_name,
        "input_context": variables,
        "raw_output": json.dumps(res) if isinstance(res, dict) else str(res)
    }
    
    return {"fdd_report_draft": res, "prompt_telemetry_buffer": telemetry_buffer}

async def bull_bear_debate_node(state: GraphState):
    print("--- [LAYER 5] Running Two-Pass Bull/Bear Debate (Cohere) ---", flush=True)
    
    is_delta = bool(state.get("notebook_entries"))
    run_suffix = "_delta" if is_delta else ""
    
    common_vars = {
        "company_name": state["resolved_identity"]["company_name"],
        "ticker": state["resolved_identity"]["ticker"],
        "run_date": state["run_date"],
        "fdd_synthesis_queue": json.dumps(state.get("fdd_synthesis_queue"), indent=2),
        "materiality_summary": state.get("materiality_summary")
    }
    
    if is_delta:
        common_vars["previous_bull_thesis"] = json.dumps(state.get("last_bull_thesis", {}), indent=2)
        common_vars["previous_bear_thesis"] = json.dumps(state.get("last_bear_thesis", {}), indent=2)
        common_vars["what_changed_summary"] = json.dumps(state.get("what_changed_summary", {}), indent=2)
        common_vars["last_run_date"] = state.get("last_run_date", "N/A")
    
    # ---------------------------------------------------------
    # PASS 1: Independent Thesis Generation
    # ---------------------------------------------------------
    print(f"  > Pass 1: Independent Thesis Generation (Delta: {is_delta})...", flush=True)
    bull_vars_p1 = common_vars.copy()
    bull_vars_p1["run_type"] = f"bull_pass1{run_suffix}"
    
    bear_vars_p1 = common_vars.copy()
    bear_vars_p1["run_type"] = f"bear_pass1{run_suffix}"
    
    try:
        bull_res_1, bear_res_1 = await asyncio.gather(
            bull_bear_agent.process(bull_vars_p1),
            bull_bear_agent.process(bear_vars_p1)
        )
    except Exception as e:
        logger.warning(f"Cohere Bull/Bear Agent failed: {e}. Falling back to Analyst Agent...")
        bull_res_1, bear_res_1 = await asyncio.gather(
            analyst_agent.analyze(bull_vars_p1),
            analyst_agent.analyze(bear_vars_p1)
        )
    
    # ---------------------------------------------------------
    # PASS 2: Rebuttal Exchange
    # ---------------------------------------------------------
    print("  > Pass 2: Rebuttal Exchange...", flush=True)
    bull_vars_p2 = common_vars.copy()
    bull_vars_p2["run_type"] = f"bull_pass2{run_suffix}"
    bull_vars_p2["bear_thesis"] = json.dumps(bear_res_1, indent=2)
    
    bear_vars_p2 = common_vars.copy()
    bear_vars_p2["run_type"] = f"bear_pass2{run_suffix}"
    bear_vars_p2["bull_thesis"] = json.dumps(bull_res_1, indent=2)
    
    try:
        bull_res_2, bear_res_2 = await asyncio.gather(
            bull_bear_agent.process(bull_vars_p2),
            bull_bear_agent.process(bear_vars_p2)
        )
    except Exception as e:
        logger.warning(f"Cohere Bull/Bear Agent (Pass 2) failed: {e}. Falling back to Analyst Agent...")
        bull_res_2, bear_res_2 = await asyncio.gather(
            analyst_agent.analyze(bull_vars_p2),
            analyst_agent.analyze(bear_vars_p2)
        )
    
    # Merge passes
    bull_final = {**bull_res_1, **bull_res_2}
    bear_final = {**bear_res_1, **bear_res_2}
    
    # Buffer telemetry for Layer 6 optimization
    telemetry_buffer = state.get("prompt_telemetry_buffer", {}) or {}
    telemetry_buffer["report/bull_bear_pass2"] = {
        "prompt_name": "report/bull_bear_pass2",
        "dimension": "report",
        "model_name": "cohere_command_r_plus",
        "input_context": bull_vars_p2, # Representative of both
        "raw_output": json.dumps({"bull": bull_res_2, "bear": bear_res_2})
    }

    return {
        "bull_thesis": bull_final,
        "bear_thesis": bear_final,
        "prompt_telemetry_buffer": telemetry_buffer
    }

async def conflict_resolution_node(state: GraphState):
    print("--- [LAYER 5] Running Conflict Resolution (Cohere) ---", flush=True)
    is_delta = bool(state.get("notebook_entries"))
    
    variables = {
        "company_name": state["resolved_identity"]["company_name"],
        "ticker": state["resolved_identity"]["ticker"],
        "run_date": state["run_date"],
        "run_type": "delta" if is_delta else "cold",
        "fdd_synthesis_queue": json.dumps(state.get("fdd_synthesis_queue"), indent=2),
        "bull_thesis": json.dumps(state.get("bull_thesis"), indent=2),
        "bear_thesis": json.dumps(state.get("bear_thesis"), indent=2)
    }
    
    # Handle analyst thesis adjudication
    adjudication = state.get("analyst_thesis_adjudication")
    if adjudication:
        variables["analyst_adjudication_instruction"] = f"The analyst has explicitly chosen the {adjudication.replace('accept_', '')} thesis as the correct direction. Please align the resolution and FDD report sections with this choice."

    if is_delta:
        variables["previous_conflict_resolution"] = json.dumps(state.get("last_conflict_resolution", {}), indent=2)
        variables["what_changed_summary"] = json.dumps(state.get("what_changed_summary", {}), indent=2)
        variables["last_run_date"] = state.get("last_run_date", "N/A")
        
    # CRITICAL: PIVOT to GPT-4 if Cohere fails
    try:
        res = await conflict_resolution_agent.process(variables)
    except Exception as e:
        print(f"--- [LAYER 5] PIVOT: Cohere failed ({e}). Using GPT-4 for Conflict Resolution ---", flush=True)
        res = await analyst_agent.analyze(variables)

    # Buffer telemetry for Layer 6 optimization
    telemetry_buffer = state.get("prompt_telemetry_buffer", {}) or {}
    telemetry_buffer["report/conflict_resolution"] = {
        "prompt_name": "report/conflict_resolution",
        "dimension": "report",
        "model_name": "cohere_command_r_plus",
        "input_context": variables,
        "raw_output": json.dumps(res)
    }

    return {"conflict_resolution": res, "prompt_telemetry_buffer": telemetry_buffer}

async def compiler_node(state: GraphState):
    print("--- [LAYER 5] Compiling Final FDD Report Draft ---", flush=True)
    
    synthesis = state.get("fdd_report_draft", {})
    if not isinstance(synthesis, dict):
        synthesis = {}
        
    conflict_res = state.get("conflict_resolution", {})
    if not isinstance(conflict_res, dict):
        conflict_res = {}
        
    is_delta = bool(state.get("notebook_entries"))
    
    # 1. Base Metadata
    final_report = {
        "title": f"FUNDAMENTAL DUE DILIGENCE REPORT - {state['resolved_identity']['company_name']}",
        "ticker": state["resolved_identity"]["ticker"],
        "run_date": state["run_date"],
        "version": synthesis.get("report_version", 1),
        "status": "PUBLISHED" if state.get("publication_id") else "DRAFT — Pending Analyst Approval",
    }
    
    # 2. What Changed (Delta Only)
    if is_delta and "what_changed" in synthesis:
        final_report["what_changed"] = synthesis["what_changed"]
        
    # 3. Component A Sections
    final_report["executive_summary"] = synthesis.get("executive_summary")
    final_report["sections"] = synthesis.get("sections", {})
    
    # 4. Component C (Bull & Bear)
    if "bull_bear_report_section" in conflict_res:
        final_report["sections"]["investment_thesis_bull_bear"] = conflict_res["bull_bear_report_section"]
        
    # 5. Disclaimer
    final_report["disclaimer"] = (
        "DISCLAIMER\n\n"
        "This report has been generated by the ONIST AI Research Platform using a Multi-Agent RAG architecture. "
        "All claims are sourced from public filings, news sources, and financial data providers as cited. "
        "Claims are labelled by verification status:\n\n"
        "• No label = Verified (passed all verification gates)\n"
        "• [Source note] = Partially verified\n"
        "• [Unverified] = Not independently corroborated\n"
        "• [Forward-looking] = Management guidance or projection\n"
        "• [Analyst override] = Analyst-assessed, proprietary basis\n"
        "• [Analyst injection] = Analyst-sourced, not public data\n\n"
        "**REGULATORY DISCLOSURE**: This is an AI-assisted Fundamental Due Diligence (FDD) Report. "
        "All findings are synthesised from public and private datasets. Analyst attestation is required for final publication. "
        "It does not constitute investment advice. The information herein is for institutional use only."
    )
    
    def _get_nested_val(obj: dict, key1: str, key2: str, default: Any) -> Any:
        val = obj.get(key1, {})
        if isinstance(val, dict):
            return val.get(key2, default)
        return default

    # [PRD UPDATE] Analyst Bottleneck Mitigation
    # Placeholder for auto-publish logic: if materiality is low and time > 4h, auto-approve.
    # Currently just flagging for the compiler.
    total_claims = _get_nested_val(synthesis, "report_metadata", "total_claims_synthesised", 0)
    final_report["auto_publish_eligible"] = total_claims < 5
    
    # Extract analyst review items from Component A and Component C
    analyst_review_items = []
    
    for section_name, section_data in synthesis.get("sections", {}).items():
        if isinstance(section_data, dict) and section_data.get("unverified_claims_included", 0) > 0:
            analyst_review_items.append({
                "item_type": "unsupported_claim",
                "description": f"Unverified claims included in {section_data.get('title', section_name)}",
                "urgency": "high",
                "suggested_action": "Review and verify claims or exclude from report"
            })
            
    if "analyst_review_items" in conflict_res:
        analyst_review_items.extend(conflict_res["analyst_review_items"])
        
    # 6. Quality Checks
    quality_failures = []
    
    # Check Executive Summary
    exec_summary = final_report.get("executive_summary", {})
    if not exec_summary:
        quality_failures.append("Executive summary is missing or empty.")
    else:
        word_count = exec_summary.get("word_count", 0)
        if word_count > 300:
            quality_failures.append(f"Executive summary exceeds 300 words ({word_count} words).")
            
    # Check Required Sections
    required_sections = [
        "company_snapshot", "business_model_and_economics", "financial_performance", 
        "strategy_and_competitive_moat", "management_and_governance", "risks_and_red_flags", 
        "market_perception_and_sentiment", "investment_thesis_bull_bear"
    ]
    for sec in required_sections:
        if sec not in final_report.get("sections", {}):
            quality_failures.append(f"Required section '{sec}' is missing.")
            
    # Check delta run requirements
    if is_delta and "what_changed" not in final_report:
        quality_failures.append("What Changed section is missing for delta run.")
        
    # Append quality failures to analyst review items
    for failure in quality_failures:
        analyst_review_items.append({
            "item_type": "quality_check_failure",
            "description": failure,
            "urgency": "medium",
            "suggested_action": "Regenerate affected section or accept as-is"
        })
        
    final_report["analyst_review_items"] = analyst_review_items
    
    return {"fdd_report_draft": final_report}

async def layer7_institutional_review_node(state: GraphState):
    """
    Advanced Layer 7 Institutional Review:
    - Investment Committee Debate
    - Contagion & Systemic Risk Analysis
    """
    print("--- [LAYER 7] Running Institutional Review (Committee + Contagion) ---", flush=True)
    
    report_draft = state.get("fdd_report_draft", {})
    ticker = state["resolved_identity"]["ticker"]
    company_name = state["resolved_identity"]["company_name"]
    
    # 1. Run Investment Committee
    from backend.agents.investment_committee import investment_committee
    committee_minutes = await investment_committee.run_committee(
        report_draft, 
        {"ticker": ticker, "company_name": company_name}
    )
    
    # 2. Run Contagion Analysis
    from backend.pipeline.contagion import contagion_analyzer
    # Dimensions to analyze for contagion
    dimensions = ["business_strategy", "business_mechanics", "footprint"]
    systemic_risks = await contagion_analyzer.analyze_systemic_risks(ticker, dimensions)
    
    # 3. Generate Trading Signal
    from backend.pipeline.trading_engine import trading_engine
    signal = trading_engine.generate_signal(committee_minutes.get("cio_verdict", {}))
    
    return {
        "investment_committee_minutes": committee_minutes,
        "systemic_risks": systemic_risks,
        "trading_signal": signal
    }

# --- Graph Construction ---
workflow = StateGraph(GraphState)
workflow.add_node("data_ingestion", data_ingestion_node)
workflow.add_node("staleness_sweep", staleness_sweep_node)
workflow.add_node("event_detection", event_detection_node)
workflow.add_node("identity", identity_node)
workflow.add_node("research_batches", micro_batch_node)
workflow.add_node("specialists", specialist_node)
workflow.add_node("materiality", materiality_filter_node)
workflow.add_node("notebook_write", notebook_write_node)
workflow.add_node("report_synthesis", report_synthesis_node)
workflow.add_node("bull_bear", bull_bear_debate_node)
workflow.add_node("conflict_resolution", conflict_resolution_node)
workflow.add_node("compiler", compiler_node)
workflow.add_node("layer7_review", layer7_institutional_review_node)
workflow.add_node("analyst_review", analyst_review_node)

workflow.set_entry_point("data_ingestion")
workflow.add_edge("data_ingestion", "staleness_sweep")
workflow.add_edge("staleness_sweep", "event_detection")
workflow.add_edge("event_detection", "identity")
workflow.add_edge("identity", "research_batches")
workflow.add_edge("research_batches", "specialists")

# Layer 4 Parallel
workflow.add_edge("specialists", "materiality")
workflow.add_edge("specialists", "notebook_write")

# Layer 5 Transition (Conditional)
def route_after_materiality(state: GraphState):
    if state.get("fdd_regeneration_required", True):
        return ["report_synthesis", "bull_bear"]
    else:
        # Skip Layer 5, jump to analyst review (or end if no review needed for non-material)
        return ["analyst_review"]

workflow.add_conditional_edges(
    "materiality",
    route_after_materiality,
    {
        "report_synthesis": "report_synthesis",
        "bull_bear": "bull_bear",
        "analyst_review": "analyst_review"
    }
)

# Join for Conflict Resolution
workflow.add_edge("report_synthesis", "conflict_resolution")
workflow.add_edge("bull_bear", "conflict_resolution")

workflow.add_edge("conflict_resolution", "compiler")
workflow.add_edge("compiler", "layer7_review")
workflow.add_edge("layer7_review", "analyst_review")

def route_after_review(state: GraphState):
    """Routes the graph based on analyst feedback."""
    if state.get("analyst_rejection_feedback"):
        print(f"--- [HITL] Analyst REJECTED: {state['analyst_rejection_feedback']} ---", flush=True)
        if state.get("re_run_list"):
            return "research_batches"
        return "report_synthesis"
    
    if state.get("status") == "PUBLISHED":
        print("--- [HITL] Analyst APPROVED. Publishing... ---", flush=True)
        return END
        
    return END

workflow.add_conditional_edges(
    "analyst_review",
    route_after_review,
    {
        "research_batches": "research_batches",
        "report_synthesis": "report_synthesis",
        END: END
    }
)

from langgraph.checkpoint.memory import MemorySaver
app = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["analyst_review"])
