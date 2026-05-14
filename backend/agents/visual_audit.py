import logging
import json
from typing import Dict, Any, List
from google import genai
from google.genai import types
from backend.config import config

logger = logging.getLogger(__name__)

class VisualAuditAgent:
    def __init__(self, model_name: str = "gemini-2.0-pro-exp-02-05"):
        self.model_name = model_name
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)

    async def audit_claim_visually(self, claim: str, images: List[bytes]) -> Dict[str, Any]:
        """
        Cross-references a text claim against a list of visual evidence (e.g., earnings slides).
        """
        logger.info(f"--- [LAYER 3] Running Visual Evidence Audit for claim: {claim[:50]}... ---")
        
        # Prepare content parts
        contents = [
            "You are an Expert Forensic Auditor. Your task is to verify the following text claim against the provided visual evidence (earnings slides, financial charts).",
            f"CLAIM TO VERIFY: {claim}",
            "If the visual evidence confirms the claim, return 'verified'.",
            "If the visual evidence contradicts the claim (e.g., numbers don't match charts), return 'contradiction'.",
            "If the evidence is missing or ambiguous, return 'unverified'."
        ]
        
        # Add images
        for i, img_bytes in enumerate(images):
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))

        # Call Gemini 2.0 Pro
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Visual Audit Failed: {e}")
            return {"status": "error", "reason": str(e)}

visual_audit_agent = VisualAuditAgent()

import asyncio
