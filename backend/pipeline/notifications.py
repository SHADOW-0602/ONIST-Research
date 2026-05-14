import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self):
        self.immediate_alerts = []
        self.standard_alerts = []
        self.informational_alerts = []

    def process_gate_results(self, agent_name: str, gates: Dict[str, Any]):
        """
        [DEPRECATED/LEGACY] Analysis during gate processing.
        Newer logic uses dispatch_diff.
        """
        gate1 = gates.get("gate1", {})
        gate2 = gates.get("gate2", {})
        gate3 = gates.get("gate3", {})
        
        # ... (Old logic retained for backward compatibility if needed)
        pass

    def dispatch_diff(self, diff: Dict[str, Any]):
        """
        Implementation of Step 5 of PRD.
        Dispatches the structured diff to the analyst interface.
        """
        # 1. IMMEDIATE (Push/Email)
        if diff.get("fdd_regeneration_flag", {}).get("urgency") == "immediate":
            self.immediate_alerts.append(f"[IMMEDIATE] FDD Regeneration Required: {diff['fdd_regeneration_flag']['reason']}")
            
        for action in diff.get("analyst_actions_required", []):
            if action.get("urgency") == "immediate":
                self.immediate_alerts.append(f"[IMMEDIATE] Action Required: {action['description']}")

        if diff.get("diff_summary", {}).get("unverified_new_entries", 0) > 5:
            self.immediate_alerts.append(f"[IMMEDIATE] High volume of unverified new entries detected.")

        # 2. STANDARD (Email)
        if diff.get("fdd_regeneration_flag", {}).get("regeneration_required"):
            self.standard_alerts.append(f"[STANDARD] FDD Regeneration Requested: {diff['fdd_regeneration_flag']['reason']}")
            
        if diff.get("diff_summary", {}).get("refetch_queue_size", 0) > 3:
            self.standard_alerts.append(f"[STANDARD] High re-fetch volume: {diff['diff_summary']['refetch_queue_size']} entries.")

        # 3. INFORMATIONAL
        if diff.get("diff_summary", {}).get("total_unchanged_entries", 0) > 0 and not self.immediate_alerts:
             self.informational_alerts.append(f"[INFO] Delta run completed. {diff['diff_summary']['total_updated_entries']} entries updated.")

    def get_pending_alerts(self) -> Dict[str, List[str]]:
        return {
            "immediate": self.immediate_alerts,
            "standard": self.standard_alerts,
            "informational": self.informational_alerts
        }

    def clear(self):
        self.immediate_alerts = []
        self.standard_alerts = []
        self.informational_alerts = []

notification_system = NotificationSystem()
