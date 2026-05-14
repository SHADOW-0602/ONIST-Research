import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import config
import asyncio
from google import genai

logger = logging.getLogger(__name__)

class NotebookClient:
    def __init__(self):
        self.db_url = config.DATABASE_URL
        self.genai_client = genai.Client(api_key=config.GOOGLE_API_KEY)

    def _get_connection(self):
        if not self.db_url:
            raise ValueError("DATABASE_URL must be set")
        return psycopg2.connect(self.db_url)

    async def initialize_schema(self):
        """
        Creates the required tables for Layer 4 persistence in CockroachDB.
        """
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Table 1: Notebook Versions
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notebook_versions (
                            version_id TEXT PRIMARY KEY,
                            company_id TEXT,
                            ticker TEXT,
                            version_number INTEGER,
                            run_type TEXT,
                            run_date TIMESTAMP,
                            trigger_event TEXT,
                            dimensions_updated TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_current INTEGER DEFAULT 0,
                            previous_version_id TEXT
                        )
                    """)
                    
                    # Table 2: Notebook Entries
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notebook_entries (
                            entry_id TEXT PRIMARY KEY,
                            version_id TEXT REFERENCES notebook_versions(version_id),
                            company_id TEXT,
                            ticker TEXT,
                            dimension TEXT,
                            field_path TEXT,
                            claim_id TEXT,
                            value TEXT,
                            verification_status TEXT,
                            source_quality_score TEXT,
                            hallucination_risk TEXT,
                            staleness_severity TEXT,
                            change_status TEXT,
                            last_verified_date TIMESTAMP,
                            refetch_triggered INTEGER DEFAULT 0,
                            analyst_override INTEGER DEFAULT 0,
                            analyst_override_note TEXT,
                            suppressed INTEGER DEFAULT 0,
                            suppressed_reason TEXT,
                            embedding TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Table 3: Analyst Annotations
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notebook_analyst_annotations (
                            annotation_id TEXT PRIMARY KEY,
                            entry_id TEXT REFERENCES notebook_entries(entry_id),
                            analyst_id TEXT,
                            annotation_type TEXT,
                            annotation_text TEXT,
                            confidence_override TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Table 4: FDD Reports (Published)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS fdd_reports (
                            report_id TEXT PRIMARY KEY,
                            ticker TEXT,
                            version INTEGER,
                            run_date TIMESTAMP,
                            title TEXT,
                            executive_summary TEXT,
                            sections_json TEXT,
                            bull_thesis TEXT,
                            bear_thesis TEXT,
                            conflict_resolution TEXT,
                            status TEXT,
                            analyst_id TEXT,
                            scheduled_at TIMESTAMP,
                            is_retracted INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Table 6: Portfolio Signals (Layer 7 Tracking)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS portfolio_signals (
                            signal_id TEXT PRIMARY KEY,
                            ticker TEXT,
                            action TEXT,
                            sentiment TEXT,
                            confidence TEXT,
                            sizing TEXT,
                            entry_price FLOAT,
                            current_price FLOAT,
                            roi FLOAT,
                            stop_loss TEXT,
                            risk_reward TEXT,
                            status TEXT DEFAULT 'ACTIVE',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                conn.commit()
        await asyncio.to_thread(_run)

    async def schedule_report(self, report_id: str, scheduled_at: str):
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE fdd_reports SET status = 'SCHEDULED', scheduled_at = %s WHERE report_id = %s",
                        [scheduled_at, report_id]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def retract_report(self, report_id: str):
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE fdd_reports SET status = 'RETRACTED', is_retracted = 1 WHERE report_id = %s",
                        [report_id]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def save_fdd_report(self, ticker: str, report: Dict[str, Any], analyst_id: str = "system"):
        """Saves or updates an FDD report in CockroachDB (UPSERT)."""
        report_id = report.get("report_id") or f"rep_{ticker}_{uuid.uuid4().hex[:8]}"
        title = report.get("title", f"FDD Report: {ticker}")
        exec_summary = report.get("executive_summary", {}).get("content", "") if isinstance(report.get("executive_summary"), dict) else report.get("executive_summary", "")
        sections_json = json.dumps(report.get("sections", {}))
        bull_thesis = json.dumps(report.get("bull_thesis", {}))
        bear_thesis = json.dumps(report.get("bear_thesis", {}))
        conflict_res = json.dumps(report.get("conflict_resolution", {}))
        status = report.get("status", "DRAFT")

        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPSERT INTO fdd_reports (
                            report_id, ticker, title, executive_summary, sections_json, 
                            bull_thesis, bear_thesis, conflict_resolution, status, analyst_id, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        report_id, ticker, title, exec_summary, sections_json, 
                        bull_thesis, bear_thesis, conflict_res, status, analyst_id, datetime.now()
                    ])
                conn.commit()
        await asyncio.to_thread(_run)
        return report_id

    async def get_fdd_reports(self, ticker: str) -> List[Dict[str, Any]]:
        """Retrieves all FDD reports for a specific ticker."""
        def _run():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM fdd_reports WHERE ticker = %s ORDER BY created_at DESC", [ticker])
                    return cur.fetchall()
        return await asyncio.to_thread(_run)

    async def delete_ticker_data(self, ticker: str):
        """Completely deletes all CockroachDB records for a given ticker."""
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Delete Analyst Annotations
                    cur.execute("""
                        DELETE FROM notebook_analyst_annotations 
                        WHERE entry_id IN (SELECT entry_id FROM notebook_entries WHERE ticker = %s)
                    """, [ticker])
                    
                    # 2. Delete Notebook Entries
                    cur.execute("DELETE FROM notebook_entries WHERE ticker = %s", [ticker])
                    
                    # 3. Delete Notebook Versions
                    cur.execute("DELETE FROM notebook_versions WHERE ticker = %s", [ticker])
                    
                    # 4. Delete FDD Reports
                    cur.execute("DELETE FROM fdd_reports WHERE ticker = %s", [ticker])
                conn.commit()
        await asyncio.to_thread(_run)
        logger.info(f"Successfully deleted all CockroachDB data for ticker: {ticker}")

    async def get_fdd_reports(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch all published FDD reports for a ticker (for version comparison)."""
        def _run():
            try:
                with self._get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(
                            "SELECT * FROM fdd_reports WHERE ticker = %s ORDER BY version DESC",
                            [ticker]
                        )
                        return [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching fdd_reports for {ticker}: {e}")
                return []
        return await asyncio.to_thread(_run)

    async def get_latest_version(self, ticker: str) -> Optional[Dict[str, Any]]:
        def _run():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM notebook_versions WHERE ticker = %s AND is_current = 1 LIMIT 1",
                        [ticker]
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        return await asyncio.to_thread(_run)

    async def get_notebook_entries(self, ticker: str) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieves all entries for the latest version of a ticker, grouped by dimension."""
        version = await self.get_latest_version(ticker)
        if not version:
            return {}
        
        def _run():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM notebook_entries WHERE version_id = %s",
                        [version["version_id"]]
                    )
                    rows = cur.fetchall()
                    grouped = {}
                    for row in rows:
                        dim = row["dimension"]
                        if dim not in grouped:
                            grouped[dim] = []
                        grouped[dim].append(dict(row))
                    return grouped
        return await asyncio.to_thread(_run)

    async def get_all_tickers(self) -> List[str]:
        """Lists all unique tickers available in the research database."""
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT DISTINCT ticker FROM notebook_versions ORDER BY ticker")
                    return [row[0] for row in cur.fetchall()]
        return await asyncio.to_thread(_run)

    async def search_tickers(self, query: str, limit: int = 8) -> List[str]:
        """Search for unique tickers in the database matching the query."""
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT DISTINCT ticker FROM notebook_versions WHERE ticker LIKE %s LIMIT %s",
                        [f"%{query}%", limit]
                    )
                    return [row[0] for row in cur.fetchall()]
        return await asyncio.to_thread(_run)

    async def write_notebook_orchestration(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        company_id = state.get("resolved_identity", {}).get("company_name", ticker)
        run_type = "delta" if state.get("notebook_entries") else "cold"
        
        latest = await self.get_latest_version(ticker)
        next_v = (latest["version_number"] + 1) if latest else 1
        prev_id = latest["version_id"] if latest else None
        
        statements = []
        args_list = []
        
        if prev_id:
            statements.append("UPDATE notebook_versions SET is_current = 0 WHERE version_id = %s")
            args_list.append([prev_id])
        
        new_version_id = str(uuid.uuid4())
        run_date = datetime.now()
        
        statements.append("""
            INSERT INTO notebook_versions 
            (version_id, company_id, ticker, version_number, run_type, run_date, is_current, previous_version_id)
            VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
        """)
        args_list.append([new_version_id, company_id, ticker, next_v, run_type, run_date, prev_id])
        
        agent_outputs = state.get("agent_outputs", {})
        for dim, claims in agent_outputs.items():
            if isinstance(claims, list):
                for claim in claims:
                    self._prepare_entry(statements, args_list, new_version_id, company_id, ticker, dim, claim)
            elif isinstance(claims, dict) and "material_claims" in claims:
                for claim in claims["material_claims"]:
                    self._prepare_entry(statements, args_list, new_version_id, company_id, ticker, dim, claim)
            elif isinstance(claims, dict):
                self._prepare_entry(statements, args_list, new_version_id, company_id, ticker, dim, claims)
        
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for stmt, args in zip(statements, args_list):
                        cur.execute(stmt, args)
                conn.commit()
        await asyncio.to_thread(_run)
        
        return {
            "version_id": new_version_id,
            "version_number": next_v,
            "run_type": run_type,
            "new_entry_ids": []
        }

    async def update_semantic_index(self, entry_data: List[Dict[str, Any]]):
        if not entry_data:
            return
            
        statements = []
        args_list = []
        
        for entry in entry_data:
            text_to_embed = f"Dimension: {entry['dimension']}\nField: {entry['field_path']}\nClaim: {json.dumps(entry['value'])}"
            response = await asyncio.to_thread(
                self.genai_client.models.embed_content,
                model="text-embedding-004",
                contents=text_to_embed
            )
            embedding = response.embeddings[0].values
            
            statements.append("UPDATE notebook_entries SET embedding = %s WHERE entry_id = %s")
            args_list.append([json.dumps(embedding), entry['entry_id']])
            
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for stmt, args in zip(statements, args_list):
                        cur.execute(stmt, args)
                conn.commit()
        await asyncio.to_thread(_run)
            
        logger.info(f"Semantic index updated for {len(entry_data)} entries.")

    async def add_annotation(self, entry_id: str, analyst_id: str, annotation_type: str, text: str, include_in_fdd: bool = False):
        annotation_id = str(uuid.uuid4())
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO notebook_analyst_annotations (annotation_id, entry_id, analyst_id, annotation_type, annotation_text)
                           VALUES (%s, %s, %s, %s, %s)""",
                        [annotation_id, entry_id, analyst_id, annotation_type, text]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def confidence_override(self, entry_id: str, analyst_id: str, confidence: str):
        annotation_id = str(uuid.uuid4())
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE notebook_entries SET verification_status = 'analyst_override' WHERE entry_id = %s", [entry_id])
                    cur.execute(
                        """INSERT INTO notebook_analyst_annotations (annotation_id, entry_id, analyst_id, annotation_type, confidence_override)
                           VALUES (%s, %s, %s, 'override', %s)""",
                        [annotation_id, entry_id, analyst_id, confidence]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def suppress_claim(self, entry_id: str, analyst_id: str, reason: str):
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE notebook_entries SET suppressed = 1, suppressed_reason = %s WHERE entry_id = %s",
                        [reason, entry_id]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def inject_manual_claim(self, version_id: str, company_id: str, ticker: str, dimension: str, claim: Dict[str, Any], analyst_id: str):
        entry_id = str(uuid.uuid4())
        claim_id = f"inject_{uuid.uuid4().hex[:8]}"
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO notebook_entries 
                           (entry_id, version_id, company_id, ticker, dimension, field_path, claim_id, value, 
                            verification_status, change_status, analyst_override, source_quality_score)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'analyst_override', 'new', 1, 'analyst_injection')""",
                        [entry_id, version_id, company_id, ticker, dimension, 
                         claim.get("field_path", "injected"),
                         claim_id,
                         json.dumps(claim)]
                    )
                conn.commit()
        await asyncio.to_thread(_run)

    async def log_prompt_telemetry(self, data: Dict[str, Any]):
        """Logs prompt-completion data for ML-based optimization."""
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO prompt_telemetry (
                            prompt_name, dimension, model_name, prompt_version, 
                            input_context, raw_output, final_approved_output, delta_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        data.get("prompt_name"),
                        data.get("dimension"),
                        data.get("model_name"),
                        data.get("prompt_version"),
                        json.dumps(data.get("input_context")),
                        data.get("raw_output"),
                        data.get("final_approved_output"),
                        json.dumps(data.get("delta_json"))
                    ])
                conn.commit()
        await asyncio.to_thread(_run)

    def _prepare_entry(self, statements: list, args_list: list, version_id: str, company_id: str, ticker: str, dimension: str, claim: dict):
        entry_id = str(uuid.uuid4())
        last_verified = datetime.now()
        
        statements.append("""
            INSERT INTO notebook_entries 
            (entry_id, version_id, company_id, ticker, dimension, field_path, claim_id, value, 
             verification_status, source_quality_score, hallucination_risk, staleness_severity, 
             change_status, last_verified_date, refetch_triggered)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """)
        args_list.append([
            entry_id, version_id, company_id, ticker, dimension, 
            claim.get("field_path", "unknown"),
            claim.get("claim_id", str(uuid.uuid4())),
            json.dumps(claim),
            claim.get("verification_status", "unverified"),
            claim.get("source_quality_score", "absent"),
            claim.get("hallucination_risk", "ungrounded"),
            claim.get("staleness_severity", "stale"),
            claim.get("change_status", "new"),
            last_verified,
            1 if claim.get("refetch_triggered", False) else 0
        ])

    def generate_diff(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute a structured diff between the current agent_outputs and the
        previous notebook_entries stored in GraphState.
        Returns a list of DiffEntry objects for the frontend NotebookDiff component.
        """
        agent_outputs: Dict[str, Any] = state.get("agent_outputs", {})
        existing: Dict[str, Any] = state.get("notebook_entries", {}) or {}

        diff_entries = []
        new_count = 0
        updated_count = 0
        deprecated_count = 0

        # Build a flat lookup of existing claims keyed by dimension+field_path
        existing_index: Dict[str, Any] = {}
        for dimension, entries in existing.items():
            if isinstance(entries, list):
                for entry in entries:
                    fp = entry.get("field_path", "unknown")
                    key = f"{dimension}::{fp}"
                    existing_index[key] = entry

        # Iterate new agent outputs and compare against existing
        for dimension, data in agent_outputs.items():
            claims = []
            if isinstance(data, list):
                claims = data
            elif isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        claims.extend(v)

            for claim in claims:
                if not isinstance(claim, dict):
                    continue
                fp = claim.get("field_path", "unknown")
                key = f"{dimension}::{fp}"
                value = claim.get("value", {})
                claim_text = value.get("claim", str(value)) if isinstance(value, dict) else str(value)
                source = claim.get("source_quality_score", "—")

                if key not in existing_index:
                    # New entry
                    diff_entries.append({
                        "id": key,
                        "dimension": dimension,
                        "field_path": fp,
                        "claim": claim_text,
                        "status": "new",
                        "source": source,
                    })
                    new_count += 1
                else:
                    prev = existing_index[key]
                    prev_val = prev.get("value", {})
                    prev_text = prev_val.get("claim", str(prev_val)) if isinstance(prev_val, dict) else str(prev_val)

                    if prev_text != claim_text:
                        # Updated entry
                        diff_entries.append({
                            "id": key,
                            "dimension": dimension,
                            "field_path": fp,
                            "claim": claim_text,
                            "status": "updated",
                            "previousValue": prev_text,
                            "newValue": claim_text,
                            "source": source,
                        })
                        updated_count += 1

        # Detect deprecated entries (existed before, not in new outputs)
        new_keys = {
            f"{dim}::{c.get('field_path', 'unknown')}"
            for dim, data in agent_outputs.items()
            for c in (data if isinstance(data, list) else [])
            if isinstance(c, dict)
        }
        for key, entry in existing_index.items():
            if key not in new_keys:
                dim, fp = key.split("::", 1)
                val = entry.get("value", {})
                deprecated_count += 1
                diff_entries.append({
                    "id": key,
                    "dimension": dim,
                    "field_path": fp,
                    "claim": val.get("claim", str(val)) if isinstance(val, dict) else str(val),
                    "status": "deprecated",
                    "source": entry.get("source_quality_score", "—"),
                })

        return {
            "entries": diff_entries,
            "summary": {
                "new": new_count,
                "updated": updated_count,
                "deprecated": deprecated_count,
            },
            "fdd_regeneration_required": (new_count + updated_count) > 0,
        }

    async def save_portfolio_signal(self, signal_data: Dict[str, Any]):
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO portfolio_signals (
                            signal_id, ticker, action, sentiment, confidence, 
                            sizing, entry_price, current_price, roi, 
                            stop_loss, risk_reward
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (signal_id) DO NOTHING
                    """, (
                        str(uuid.uuid4()),
                        signal_data['ticker'],
                        signal_data['action'],
                        signal_data['ticker_sentiment'],
                        signal_data['confidence_level'],
                        signal_data['sizing'],
                        signal_data['entry_price'],
                        signal_data['entry_price'], # Current price starts as entry price
                        0.0, # ROI starts at 0
                        signal_data['stop_loss_trigger'],
                        signal_data['risk_reward']
                    ))
                conn.commit()
        await asyncio.to_thread(_run)

    async def get_portfolio_signals(self) -> List[Dict[str, Any]]:
        def _run():
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM portfolio_signals ORDER BY created_at DESC")
                    return cur.fetchall()
        return await asyncio.to_thread(_run)

    async def update_signal_prices(self, updates: List[Dict[str, Any]]):
        def _run():
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for update in updates:
                        cur.execute("""
                            UPDATE portfolio_signals 
                            SET current_price = %s, roi = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE signal_id = %s
                        """, (update['current_price'], update['roi'], update['signal_id']))
                conn.commit()
        await asyncio.to_thread(_run)

notebook_client = NotebookClient()
